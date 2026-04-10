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
        # Block incoming traffic from this MAC
        success &= self._run_iptables([
            "-I", "INPUT", "-m", "mac",
            "--mac-source", mac, "-j", "DROP",
        ])
        # Block outgoing traffic to this IP
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
            "-D", "OUTPUT", "-d", ip, "-j", "DROP",
        ])
        self._unmark_restricted(mac)
        db.log_event(
            mac_address=mac, ip_address=ip,
            event_type="ENFORCEMENT_STOPPED",
            actor="system",
            details=f"iptables rules removed for MAC={mac}",
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
# Portal mode (ARP Spoofing + Redirection)
# ---------------------------------------------------------------------------

class ArpSpoofEnforcement(BaseEnforcement):
    """
    Advanced enforcement: Uses ARP Spoofing to intercept a device's traffic
    and redirect it to the local Captive Portal (port 80/8080).
    WARNING: Requires Scapy and root privileges.
    """

    def __init__(self):
        super().__init__()
        self._spoof_threads: Dict[str, threading.Event] = {}
        from scapy.all import getmacbyip
        self._get_mac_by_ip = getmacbyip
        # In portal mode, we detect gateway IP from settings or netstat
        self.gateway_ip = "192.168.0.1" # Default common gateway

    def restrict(self, mac: str, ip: str, device_id: int) -> bool:
        logger.warning("[PORTAL] Starting ARP Spoofing/Isolation for MAC=%s IP=%s", mac, ip)
        
        if mac in self._spoof_threads:
            return True

        stop_event = threading.Event()
        t = threading.Thread(
            target=self._spoof_loop,
            args=(mac, ip, stop_event),
            daemon=True,
            name=f"spoof-{mac}"
        )
        self._spoof_threads[mac] = stop_event
        t.start()
        
        self._mark_restricted(mac)
        db.log_event(
            mac_address=mac, ip_address=ip,
            event_type="ENFORCEMENT_STARTED",
            actor="system",
            details="ARP Spoofing started. Traffic redirected to Captive Portal."
        )
        return True

    def release(self, mac: str, ip: str, device_id: int) -> bool:
        logger.info("[PORTAL] Stopping ARP Spoofing for MAC=%s", mac)
        stop_event = self._spoof_threads.pop(mac, None)
        if stop_event:
            stop_event.set()
            
        self._unmark_restricted(mac)
        db.log_event(
            mac_address=mac, ip_address=ip,
            event_type="ENFORCEMENT_STOPPED",
            actor="system",
            details="ARP Spoofing stopped. Device released."
        )
        return True

    def _spoof_loop(self, target_mac: str, target_ip: str, stop_event: threading.Event):
        """Continuously poison the target's ARP cache to point to US."""
        from scapy.all import ARP, Ether, sendp
        
        # We also need the gateway's MAC to convince the device we are the gateway
        gateway_mac = self._get_mac_by_ip(self.gateway_ip)
        if not gateway_mac:
            logger.error("Could not find MAC for gateway %s. ARP spoofing might fail.", self.gateway_ip)
            gateway_mac = "ff:ff:ff:ff:ff:ff"

        logger.debug("ARP Spoof loop started for %s (Gateway: %s)", target_ip, self.gateway_ip)
        
        while not stop_event.is_set():
            try:
                # Poison the target: "I am the gateway"
                # Op=2 is ARP reply
                # psrc=gateway_ip means we claim to be the gateway
                poison_dst = Ether(dst=target_mac) / ARP(op=2, psrc=self.gateway_ip, pdst=target_ip, hwdst=target_mac)
                sendp(poison_dst, verbose=False)
                
                # We can also poison the gateway if we want full man-in-the-middle
                # poison_src = Ether(dst=gateway_mac) / ARP(op=2, psrc=target_ip, pdst=self.gateway_ip, hwdst=gateway_mac)
                # sendp(poison_src, verbose=False)
                
            except Exception as e:
                logger.error("Error in spoof loop for %s: %s", target_ip, e)
            
            stop_event.wait(2) # Send every 2 seconds

        # Cleanup: Re-map the target back to the real gateway
        logger.debug("Sending ARP restoration packets for %s", target_ip)
        restore = Ether(dst=target_mac) / ARP(op=2, psrc=self.gateway_ip, hwsrc=gateway_mac, pdst=target_ip, hwdst=target_mac)
        sendp(restore, count=5, verbose=False)


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
