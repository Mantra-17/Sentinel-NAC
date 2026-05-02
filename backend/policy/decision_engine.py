"""
Sentinel-NAC: Policy / Decision Engine
File: backend/policy/decision_engine.py
Purpose: Apply Zero Trust policy to every newly detected device.
         Default stance: DENY (treat all unknown devices as untrusted).

Policy rules (in priority order):
  1. Device with status ALLOWED  → no action required.
  2. Device with status BLOCKED  → enforce immediately.
  3. Device with status QUARANTINED → enforce immediately.
  4. Brand new device (UNKNOWN)  → assign default status from config,
                                    then enforce if restricted.
"""

import logging
from typing import Dict, Optional

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.settings import DEFAULT_NEW_DEVICE_STATUS, is_restricted_status
from database import db
from logs.logger import get_logger

logger = get_logger(__name__)


class DecisionEngine:
    """
    Evaluate the policy for every discovered device and return an action.

    All state lives in the database, so multi-process / restart-safe.
    """

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    def evaluate(
        self,
        mac: str,
        ip: str,
        fingerprint: Optional[Dict] = None,
    ) -> Dict:
        """
        Decide what to do with a discovered device.

        Args:
            mac:         MAC address (upper-case colon-separated)
            ip:          Current IP address
            fingerprint: Dict from fingerprint_device() or None

        Returns:
            Result dict:
              - device:         current database row (post-upsert)
              - action:         'permit' | 'enforce' | 'no_change'
              - is_new_device:  True if device was never seen before
              - trigger_alert:  True if an alert should be sent
        """
        existing = db.get_device_by_mac(mac)
        is_new = existing is None

        # Unpack fingerprint data (defaults to empty)
        fp = fingerprint or {}

        # Upsert device record (insert or update last_seen / fingerprint)
        device = db.upsert_device(
            mac=mac,
            ip=ip,
            hostname=fp.get("hostname"),
            vendor=fp.get("vendor"),
            probable_os=fp.get("probable_os"),
            probable_device_type=fp.get("probable_device_type"),
            fingerprint_confidence=fp.get("fingerprint_confidence", 0),
        )

        status = device["status"]

        # Log discovery event for new devices
        if is_new:
            db.log_event(
                mac_address=mac,
                ip_address=ip,
                event_type="DEVICE_DISCOVERED",
                new_status=status,
                actor="system",
                details=f"First detection. Auto-assigned status: {status}",
            )
            logger.info(
                "NEW device: MAC=%s  IP=%s  auto-status=%s", mac, ip, status
            )

        # ------------------------------------------------------------------
        # Apply policy rules
        # ------------------------------------------------------------------
        action        = "no_change"
        trigger_alert = False

        if status == "ALLOWED":
            action = "permit"
            logger.debug("Device %s is ALLOWED — permitted.", mac)

        elif status in {"BLOCKED", "QUARANTINED"}:
            if is_new:
                # New device placed in restricted state automatically
                action        = "enforce"
                trigger_alert = True
            else:
                # Known restricted device seen again
                action        = "enforce"
                trigger_alert = (status == "BLOCKED")  # alert only for explicit blocks
                if status == "BLOCKED":
                    db.log_event(
                        mac_address=mac,
                        ip_address=ip,
                        event_type="RECONNECT_BLOCKED",
                        new_status=status,
                        actor="system",
                        details="Previously blocked device reconnected.",
                    )
                    logger.warning(
                        "BLOCKED device reconnected: MAC=%s  IP=%s", mac, ip
                    )

        elif status == "UNKNOWN":
            # Should not normally happen as upsert assigns a default,
            # but handle defensively.
            action        = "enforce"
            trigger_alert = True
            db.log_event(
                mac_address=mac,
                ip_address=ip,
                event_type="DEVICE_DISCOVERED",
                new_status=status,
                actor="system",
                details="Device has UNKNOWN status (defensive fallback). Enforcing quarantine.",
            )
            logger.warning("Device %s has UNKNOWN status — enforcing as precaution.", mac)

        return {
            "device":        device,
            "action":        action,
            "is_new_device": is_new,
            "trigger_alert": trigger_alert,
        }

    # ------------------------------------------------------------------
    # Admin-driven status changes
    # ------------------------------------------------------------------

    def admin_allow(self, mac: str, admin_user: str = "admin") -> bool:
        """Admin approves a device — set status to ALLOWED."""
        result = db.update_device_status(mac, "ALLOWED", actor=admin_user)
        if result:
            logger.info("Admin '%s' ALLOWED device: %s", admin_user, mac)
        return result

    def admin_block(self, mac: str, admin_user: str = "admin") -> bool:
        """Admin blocks a device — set status to BLOCKED."""
        result = db.update_device_status(mac, "BLOCKED", actor=admin_user)
        if result:
            logger.info("Admin '%s' BLOCKED device: %s", admin_user, mac)
        return result

    def admin_quarantine(self, mac: str, admin_user: str = "admin") -> bool:
        """Admin quarantines a device — set status to QUARANTINED."""
        result = db.update_device_status(mac, "QUARANTINED", actor=admin_user)
        if result:
            logger.info("Admin '%s' QUARANTINED device: %s", admin_user, mac)
        return result
