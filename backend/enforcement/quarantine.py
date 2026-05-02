"""
Sentinel-NAC: Enforcement / Quarantine Module
File: backend/enforcement/quarantine.py
Purpose: Restrict network access for BLOCKED or QUARANTINED devices.

SAFETY NOTE: All enforcement is strictly for authorized lab environments.
             The system NEVER targets devices on networks it doesn't own.

Supported modes (set via ENFORCEMENT_MODE in .env):
  simulation - Logs and marks devices as restricted; no OS-level changes.
               Best for demo, CI, and environments without root access.

  firewall   - Uses iptables (Linux) to DROP traffic from the device's MAC.
               Requires root / sudo. Affects only this host's traffic rules.

  denylist   - Maintains an in-memory deny list that the scanner respects.
               Less powerful than firewall; useful on macOS / Windows.

All modes share the same interface so the rest of the system is mode-agnostic.
"""

import logging
import subprocess
import threading
from typing import Set, Dict

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.settings import ENFORCEMENT_MODE
from database import db
from logs.logger import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# In-memory deny list (shared across modes for status tracking)
# ---------------------------------------------------------------------------
_restricted_macs: Set[str] = set()
_lock = threading.Lock()


# ---------------------------------------------------------------------------
# Base class
# ---------------------------------------------------------------------------

class BaseEnforcement:
    """Abstract interface for enforcement backends."""

    def restrict(self, mac: str, ip: str, device_id: int) -> bool:
        raise NotImplementedError

    def release(self, mac: str, ip: str, device_id: int) -> bool:
        raise NotImplementedError

    def is_restricted(self, mac: str) -> bool:
        with _lock:
            return mac.upper() in _restricted_macs

    def _mark_restricted(self, mac: str) -> None:
        with _lock:
            _restricted_macs.add(mac.upper())

    def _unmark_restricted(self, mac: str) -> None:
        with _lock:
            _restricted_macs.discard(mac.upper())


# ---------------------------------------------------------------------------
# Simulation mode
# ---------------------------------------------------------------------------

class SimulationEnforcement(BaseEnforcement):
    """
    Safe demo mode: records enforcement state in memory and database only.
    No OS-level network changes are made.
    """

    def restrict(self, mac: str, ip: str, device_id: int) -> bool:
        logger.warning(
            "[SIMULATION] QUARANTINE ACTIVATED: MAC=%s  IP=%s  "
            "(No real network block applied — simulation mode)",
            mac, ip,
        )
        self._mark_restricted(mac)
        db.log_event(
            mac_address=mac,
            ip_address=ip,
            event_type="ENFORCEMENT_STARTED",
            actor="system",
            details="[SIMULATION] Device marked as restricted (no real block).",
        )
        return True

    def release(self, mac: str, ip: str, device_id: int) -> bool:
        logger.info(
            "[SIMULATION] QUARANTINE RELEASED: MAC=%s  IP=%s", mac, ip
        )
        self._unmark_restricted(mac)
        db.log_event(
            mac_address=mac,
            ip_address=ip,
            event_type="ENFORCEMENT_STOPPED",
            actor="system",
            details="[SIMULATION] Device restriction removed.",
        )
        return True


# ---------------------------------------------------------------------------
# Firewall mode (iptables — Linux only)
# ---------------------------------------------------------------------------

class FirewallEnforcement(BaseEnforcement):
    """
    Uses iptables to DROP all inbound and outbound traffic from a device's MAC.
    Requires the host to run Linux with root privileges.

    WARNING: Only use on YOUR OWN network equipment in an authorized lab.
    """

    IPTABLES = "/sbin/iptables"

    def restrict(self, mac: str, ip: str, device_id: int) -> bool:
        """Insert iptables rules to block the device."""
        logger.warning(
            "[FIREWALL] Blocking MAC=%s  IP=%s via iptables", mac, ip
        )
        success = True
        # Block incoming traffic from this MAC (INPUT chain)
        success &= self._run_iptables([
            "-I", "INPUT", "-m", "mac",
            "--mac-source", mac, "-j", "DROP",
        ])
        # Block forwarded traffic from this MAC (FORWARD chain — covers routing)
        success &= self._run_iptables([
            "-I", "FORWARD", "-m", "mac",
            "--mac-source", mac, "-j", "DROP",
        ])
        # Block outgoing traffic to this IP (OUTPUT chain — secondary defense)
        success &= self._run_iptables([
            "-I", "OUTPUT", "-d", ip, "-j", "DROP",
        ])

        if success:
            self._mark_restricted(mac)
            db.log_event(
                mac_address=mac, ip_address=ip,
                event_type="ENFORCEMENT_STARTED",
                actor="system",
                details=f"iptables rules inserted for MAC={mac}",
            )
        else:
            db.log_event(
                mac_address=mac, ip_address=ip,
                event_type="ERROR",
                actor="system",
                details="Failed to insert iptables rules.",
            )
        return success

    def release(self, mac: str, ip: str, device_id: int) -> bool:
        """Remove iptables rules to unblock the device."""
        logger.info(
            "[FIREWALL] Releasing iptables block for MAC=%s  IP=%s", mac, ip
        )
        success = True
        success &= self._run_iptables([
            "-D", "INPUT", "-m", "mac",
            "--mac-source", mac, "-j", "DROP",
        ])
        success &= self._run_iptables([
            "-D", "FORWARD", "-m", "mac",
            "--mac-source", mac, "-j", "DROP",
        ])
        success &= self._run_iptables([
            "-D", "OUTPUT", "-d", ip, "-j", "DROP",
        ])
        self._unmark_restricted(mac)
        db.log_event(
            mac_address=mac, ip_address=ip,
            event_type="ENFORCEMENT_STOPPED",
            actor="system",
            details=f"iptables rules removed for MAC={mac} (INPUT+FORWARD+OUTPUT)",
        )
        return success

    def _run_iptables(self, args: list) -> bool:
        cmd = ["sudo", self.IPTABLES] + args
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=5
            )
            if result.returncode != 0:
                logger.error(
                    "iptables command failed: %s\nSTDERR: %s",
                    " ".join(cmd), result.stderr,
                )
                return False
            return True
        except Exception as exc:
            logger.error("iptables execution error: %s", exc)
            return False


# ---------------------------------------------------------------------------
# Deny-list mode (in-memory + ARP spoof mitigation)
# ---------------------------------------------------------------------------

class DenylistEnforcement(BaseEnforcement):
    """
    Maintains an in-memory deny list of blocked MACs.
    The scanner checks this list and skips callbacks for blocked devices.
    More portable than iptables — works on macOS and Windows.
    Less powerful (doesn't actually block network-level traffic).
    """

    def restrict(self, mac: str, ip: str, device_id: int) -> bool:
        logger.warning(
            "[DENYLIST] Device added to deny list: MAC=%s  IP=%s", mac, ip
        )
        self._mark_restricted(mac)
        db.log_event(
            mac_address=mac, ip_address=ip,
            event_type="ENFORCEMENT_STARTED",
            actor="system",
            details="Device added to in-memory deny list.",
        )
        return True

    def release(self, mac: str, ip: str, device_id: int) -> bool:
        logger.info(
            "[DENYLIST] Device removed from deny list: MAC=%s  IP=%s", mac, ip
        )
        self._unmark_restricted(mac)
        db.log_event(
            mac_address=mac, ip_address=ip,
            event_type="ENFORCEMENT_STOPPED",
            actor="system",
            details="Device removed from deny list.",
        )
        return True


# ---------------------------------------------------------------------------
# Portal mode (ARP Spoofing + DNS Spoofing + Redirection)
# ---------------------------------------------------------------------------

class ArpSpoofEnforcement(BaseEnforcement):
    """
    Advanced enforcement: Uses ARP Spoofing AND DNS Spoofing to intercept 
    a device's traffic and force it to the local Captive Portal (port 80).
    WARNING: Requires Scapy and root privileges.
    """

    def __init__(self):
        super().__init__()
        self._enforcement_threads: Dict[str, threading.Event] = {}
        self._get_mac_by_ip = None  # Lazy-loaded from Scapy
        
        # Detect Gateway and Local IP dynamically
        self.gateway_ip = self._detect_gateway()
        self.local_ip = self._detect_local_ip()
        logger.info("[PORTAL] Initialized: Gateway=%s  LocalHost=%s", self.gateway_ip, self.local_ip)

    def _ensure_scapy(self):
        """Lazy-load Scapy's getmacbyip. Raises ImportError if not installed."""
        if self._get_mac_by_ip is None:
            try:
                from scapy.all import getmacbyip
                self._get_mac_by_ip = getmacbyip
            except ImportError:
                raise ImportError(
                    "Scapy is required for portal enforcement mode. "
                    "Install it with: pip install scapy"
                )

    def _detect_gateway(self) -> str:
        """Attempt to find the default gateway IP dynamically."""
        try:
            # Linux: read /proc/net/route
            import socket
            import struct
            with open("/proc/net/route") as f:
                for line in f:
                    fields = line.strip().split()
                    if fields[1] == '00000000':
                        return socket.inet_ntoa(struct.pack("<L", int(fields[2], 16)))
        except (FileNotFoundError, Exception):
            pass
        try:
            # macOS / BSD: parse `route -n get default`
            out = subprocess.check_output(
                ["route", "-n", "get", "default"],
                stderr=subprocess.DEVNULL, text=True
            )
            for line in out.splitlines():
                if "gateway:" in line:
                    return line.split(":")[1].strip()
        except Exception:
            pass
        logger.warning("[PORTAL] Could not detect gateway — using fallback 192.168.0.1")
        return "192.168.0.1"  # Safety fallback

    def _detect_local_ip(self) -> str:
        """Detect the IP of this Mac on the active network."""
        try:
            import socket
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"

    def restrict(self, mac: str, ip: str, device_id: int) -> bool:
        self._ensure_scapy()
        logger.warning("[PORTAL] Starting LOCKDOWN (ARP+DNS) for MAC=%s IP=%s", mac, ip)
        
        if mac in self._enforcement_threads:
            return True

        stop_event = threading.Event()
        
        # Start ARP Spoofing Thread
        t_arp = threading.Thread(
            target=self._arp_spoof_loop,
            args=(mac, ip, stop_event),
            daemon=True,
            name=f"arp-spoof-{mac}"
        )
        
        # Start DNS Spoofing Thread (Targets this specific device's requests)
        t_dns = threading.Thread(
            target=self._dns_spoof_loop,
            args=(mac, ip, stop_event),
            daemon=True,
            name=f"dns-spoof-{mac}"
        )
        
        self._enforcement_threads[mac] = stop_event
        t_arp.start()
        t_dns.start()
        
        self._mark_restricted(mac)
        db.log_event(
            mac_address=mac, ip_address=ip,
            event_type="ENFORCEMENT_STARTED",
            actor="system",
            details="ARP+DNS Spoofing active. Device isolated to Captive Portal."
        )
        return True

    def release(self, mac: str, ip: str, device_id: int) -> bool:
        logger.info("[PORTAL] Ending LOCKDOWN for MAC=%s", mac)
        stop_event = self._enforcement_threads.pop(mac, None)
        if stop_event:
            stop_event.set()
            
        self._unmark_restricted(mac)
        db.log_event(
            mac_address=mac, ip_address=ip,
            event_type="ENFORCEMENT_STOPPED",
            actor="system",
            details="Enforcement released. Network access restored."
        )
        return True

    def _arp_spoof_loop(self, target_mac: str, target_ip: str, stop_event: threading.Event):
        """Continuously poison the target's ARP cache."""
        from scapy.all import ARP, Ether, sendp
        
        gateway_mac = self._get_mac_by_ip(self.gateway_ip)
        if not gateway_mac:
            gateway_mac = "ff:ff:ff:ff:ff:ff"

        while not stop_event.is_set():
            try:
                # Poison target: Gateway is AT US
                poison = Ether(dst=target_mac) / ARP(op=2, psrc=self.gateway_ip, pdst=target_ip, hwdst=target_mac)
                sendp(poison, verbose=False)
            except Exception as e:
                logger.error("ARP Loop Error: %s", e)
            stop_event.wait(2)

        # Restore
        restore = Ether(dst=target_mac) / ARP(op=2, psrc=self.gateway_ip, hwsrc=gateway_mac, pdst=target_ip, hwdst=target_mac)
        sendp(restore, count=5, verbose=False)

    def _dns_spoof_loop(self, target_mac: str, target_ip: str, stop_event: threading.Event):
        """Intercept DNS queries from the target and answer with OUR IP."""
        from scapy.all import sniff, IP, UDP, DNS, DNSRR, send
        
        logger.info("[DNS_DEBUG] DNS Sniffer starting for target %s", target_ip)
        
        def dns_callback(pkt):
            if stop_event.is_set(): return
            
            # Check if it's a DNS query from our target
            if pkt.haslayer(DNS) and pkt.getlayer(DNS).qr == 0:
                # Log EVERY DNS query we see from the target
                qname = pkt[DNS].qd.qname.decode()
                logger.warning("[DNS_INTERCEPT] Intercepted request for %s from %s", qname, target_ip)
                
                try:
                    # Forge the response
                    spf_pkt = (IP(dst=pkt[IP].src, src=pkt[IP].dst) /
                              UDP(dport=pkt[UDP].sport, sport=pkt[UDP].dport) /
                              DNS(id=pkt[DNS].id, qd=pkt[DNS].qd, aa=1, qr=1, 
                                  an=DNSRR(rrname=pkt[DNS].qd.qname, ttl=10, rdata=self.local_ip)))
                    send(spf_pkt, verbose=False)
                    logger.warning("[DNS_SUCCESS] Spoofed response sent! Redirecting %s to %s", qname, self.local_ip)
                except Exception as e:
                    logger.error("[DNS_ERROR] Failed to send spoof: %s", e)

        # Sniff only UDP port 53 traffic from the target IP
        sniff_filter = f"udp and port 53 and host {target_ip}"
        
        try:
            while not stop_event.is_set():
                # Sniff in small batches to allow checking stop_event
                sniff(filter=sniff_filter, prn=dns_callback, store=0, count=5, timeout=2)
        except Exception as e:
            logger.error("[DNS_CRITICAL] Sniffer crashed: %s", e)


# ---------------------------------------------------------------------------
# Factory function
# ---------------------------------------------------------------------------

def get_enforcement_engine() -> BaseEnforcement:
    """
    Return the enforcement engine selected by ENFORCEMENT_MODE config.
    Defaults to SimulationEnforcement if mode is unrecognized.
    """
    mode = ENFORCEMENT_MODE.lower()
    if mode == "firewall":
        logger.info("Enforcement mode: FIREWALL (iptables)")
        return FirewallEnforcement()
    elif mode == "denylist":
        logger.info("Enforcement mode: DENYLIST")
        return DenylistEnforcement()
    elif mode == "portal":
        logger.info("Enforcement mode: PORTAL (ARP Spoofing)")
        return ArpSpoofEnforcement()
    else:
        logger.info("Enforcement mode: SIMULATION")
        return SimulationEnforcement()


# ---------------------------------------------------------------------------
# High-level enforcement controller
# ---------------------------------------------------------------------------

class QuarantineController:
    """
    Manages the enforcement lifecycle using the configured backend.
    Call handle_device_decision() after the policy engine returns a result.
    """

    def __init__(self):
        self._engine = get_enforcement_engine()
        # Track which MACs currently have active enforcement
        self._active_enforcement: Dict[str, str] = {}  # mac -> ip
        self.sync_from_db()

    def sync_from_db(self) -> None:
        """Query the database for all currently restricted devices and re-apply enforcement."""
        logger.info("[CONTROLLER] Synchronizing enforcement state from database...")
        try:
            # We want to re-enforce anyone marked BLOCKED or QUARANTINED
            # Note: We only re-apply if we have a known MAC and IP
            restricted_devices = db.get_restricted_devices()
            for dev in restricted_devices:
                mac = dev["mac_address"]
                ip = dev["ip_address"]
                if mac and ip:
                    logger.info("[CONTROLLER] Resuming protection for MAC=%s (Status=%s)", mac, dev["status"])
                    success = self._engine.restrict(mac, ip, dev["id"])
                    if success:
                        self._active_enforcement[mac] = ip
        except Exception as e:
            logger.error("[CONTROLLER] Failed to sync from DB: %s", e)

    def handle_device_decision(self, decision: Dict) -> None:
        """
        React to a decision returned by DecisionEngine.evaluate().

        Args:
            decision: Dict from DecisionEngine.evaluate()
        """
        device  = decision["device"]
        action  = decision["action"]
        mac     = device["mac_address"]
        ip      = device["ip_address"]
        dev_id  = device["id"]

        if action == "enforce":
            if mac not in self._active_enforcement:
                success = self._engine.restrict(mac, ip, dev_id)
                if success:
                    self._active_enforcement[mac] = ip

        elif action == "permit":
            if mac in self._active_enforcement:
                prev_ip = self._active_enforcement.pop(mac)
                self._engine.release(mac, prev_ip, dev_id)

        # 'no_change' — do nothing

    def release_device(self, mac: str) -> None:
        """Manually release enforcement for a device (e.g., after admin approval)."""
        device = db.get_device_by_mac(mac)
        if device and mac in self._active_enforcement:
            prev_ip = self._active_enforcement.pop(mac)
            self._engine.release(mac, prev_ip, device["id"])

    def is_restricted(self, mac: str) -> bool:
        return self._engine.is_restricted(mac)
