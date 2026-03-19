"""
Sentinel-NAC: ARP Network Scanner
File: backend/scanner/arp_scanner.py
Purpose: Continuously monitor a local network for newly connected devices
         using Scapy's ARP packet sniffing and active ARP sweeping.

IMPORTANT: This module must only be run on networks you own or have
           explicit authorization to monitor. See docs/ethics_statement.md.

Requires root / administrator privileges for raw packet capture.
"""

import time
import threading
import logging
from typing import Callable, Optional, Dict

# Third-party
try:
    from scapy.all import (
        ARP, Ether, srp, sniff, conf as scapy_conf
    )
    SCAPY_AVAILABLE = True
except ImportError:
    SCAPY_AVAILABLE = False

# Project modules
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config.settings import SCAN_INTERFACE, SCAN_TARGET, SCAN_INTERVAL

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Callback type: called whenever a device is discovered
# Signature: on_device(mac: str, ip: str, source: str) -> None
# ---------------------------------------------------------------------------
DeviceCallback = Callable[[str, str, str], None]


class ARPScanner:
    """
    Dual-mode network scanner:
      1. Passive ARP sniffing  — listens for ARP broadcasts in real time.
      2. Active ARP sweep      — periodically probes all IPs in the subnet.

    Both modes run in separate daemon threads and call the registered
    on_device callback whenever a MAC/IP pair is observed.

    Simulation Mode:
      If Scapy is unavailable or SCAN_INTERFACE=='simulate', the scanner
      emits pre-defined fake devices so the system can be demoed without
      root privileges or a real network.
    """

    SIMULATION_DEVICES = [
        {"mac": "AA:BB:CC:11:22:33", "ip": "192.168.1.10"},
        {"mac": "AA:BB:CC:44:55:66", "ip": "192.168.1.20"},
        {"mac": "AA:BB:CC:77:88:99", "ip": "192.168.1.30"},  # rogue
    ]

    def __init__(
        self,
        interface: str = SCAN_INTERFACE,
        target: str = SCAN_TARGET,
        interval: int = SCAN_INTERVAL,
        on_device: Optional[DeviceCallback] = None,
        simulate: bool = False,
    ):
        self.interface = interface
        self.target    = target
        self.interval  = interval
        self.on_device = on_device or self._default_callback
        self.simulate  = simulate or (not SCAPY_AVAILABLE) or (interface == "simulate")

        self._stop_event = threading.Event()
        self._seen_macs: Dict[str, str] = {}  # mac -> ip (dedup cache)
        self._lock = threading.Lock()

        if self.simulate:
            logger.warning(
                "ARPScanner running in SIMULATION mode — no real packets captured."
            )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Start scanner threads (non-blocking)."""
        logger.info(
            "ARPScanner starting — interface=%s  target=%s  interval=%ds  simulate=%s",
            self.interface, self.target, self.interval, self.simulate,
        )
        if self.simulate:
            t = threading.Thread(target=self._simulate_loop, daemon=True)
            t.start()
        else:
            # Passive sniff thread
            sniff_thread = threading.Thread(
                target=self._passive_sniff, daemon=True, name="sentinel-sniff"
            )
            sniff_thread.start()

            # Active sweep thread
            sweep_thread = threading.Thread(
                target=self._active_sweep_loop, daemon=True, name="sentinel-sweep"
            )
            sweep_thread.start()

    def stop(self) -> None:
        """Signal scanner threads to stop."""
        logger.info("ARPScanner stop requested.")
        self._stop_event.set()

    # ------------------------------------------------------------------
    # Internal — passive sniffing
    # ------------------------------------------------------------------

    def _passive_sniff(self) -> None:
        """Sniff live ARP packets and invoke callback for each unique source."""
        logger.debug("Passive ARP sniffer started on %s", self.interface)
        try:
            sniff(
                iface=self.interface,
                filter="arp",
                prn=self._handle_arp_packet,
                store=False,
                stop_filter=lambda _: self._stop_event.is_set(),
            )
        except Exception as exc:
            logger.error("Passive sniffer error: %s", exc)

    def _handle_arp_packet(self, packet) -> None:
        """Called by Scapy for each captured ARP packet."""
        if not (packet.haslayer(ARP) and packet.haslayer(Ether)):
            return

        arp = packet[ARP]
        mac = arp.hwsrc.upper()
        ip  = arp.psrc

        # Ignore broadcast / invalid addresses
        if mac in {"FF:FF:FF:FF:FF:FF", "00:00:00:00:00:00"} or ip == "0.0.0.0":
            return

        self._notify(mac, ip, source="passive_sniff")

    # ------------------------------------------------------------------
    # Internal — active sweep
    # ------------------------------------------------------------------

    def _active_sweep_loop(self) -> None:
        """Periodically send ARP requests to all IPs in the target subnet."""
        logger.debug(
            "Active ARP sweep loop started (interval=%ds, target=%s)",
            self.interval, self.target,
        )
        while not self._stop_event.is_set():
            self._do_sweep()
            self._stop_event.wait(self.interval)

    def _do_sweep(self) -> None:
        """Send ARP requests and process replies."""
        logger.debug("ARP sweep → %s", self.target)
        try:
            answered, _ = srp(
                Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=self.target),
                timeout=2,
                iface=self.interface,
                verbose=False,
            )
            for _, response in answered:
                mac = response[ARP].hwsrc.upper()
                ip  = response[ARP].psrc
                self._notify(mac, ip, source="active_sweep")
        except Exception as exc:
            logger.error("Active sweep error: %s", exc)

    # ------------------------------------------------------------------
    # Internal — simulation mode
    # ------------------------------------------------------------------

    def _simulate_loop(self) -> None:
        """
        Emit fake devices in a loop to simulate a live network.
        Introduces them one-by-one with a short delay so the demo
        shows real-time detection behavior.
        """
        devices = list(self.SIMULATION_DEVICES)
        index = 0
        while not self._stop_event.is_set():
            device = devices[index % len(devices)]
            self._notify(device["mac"], device["ip"], source="simulation")
            index += 1
            # Wait the configured interval before emitting next device
            self._stop_event.wait(self.interval)

    # ------------------------------------------------------------------
    # Internal — dedup and callback
    # ------------------------------------------------------------------

    def _notify(self, mac: str, ip: str, source: str) -> None:
        """
        De-duplicate (mac, ip) pairs and invoke the on_device callback
        only for:
          - Brand new MACs, OR
          - Previously seen MACs that now have a different IP
        """
        with self._lock:
            previous_ip = self._seen_macs.get(mac)
            if previous_ip == ip:
                return  # No change — skip
            self._seen_macs[mac] = ip

        logger.debug("Device seen: MAC=%s  IP=%s  source=%s", mac, ip, source)
        try:
            self.on_device(mac, ip, source)
        except Exception as exc:
            logger.error("on_device callback raised an exception: %s", exc)

    # ------------------------------------------------------------------
    # Default callback (used when no external callback is provided)
    # ------------------------------------------------------------------

    @staticmethod
    def _default_callback(mac: str, ip: str, source: str) -> None:
        logger.info("[DEVICE] MAC=%-18s  IP=%-16s  source=%s", mac, ip, source)
