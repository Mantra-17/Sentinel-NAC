"""
Sentinel-NAC: Email Alert Module
File: backend/alerts/email_alert.py
Purpose: Send SMTP email notifications for security events and store
         alert records in the database.
"""

import logging
import smtplib
import ssl
import threading
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional, Dict

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.settings import (
    ALERT_EMAIL_ENABLED, SMTP_HOST, SMTP_PORT,
    SMTP_USER, SMTP_PASSWORD, SMTP_FROM, ALERT_RECIPIENT,
)
from database import db
from logs.logger import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Internal sending helper
# ---------------------------------------------------------------------------

def _send_smtp(recipient: str, subject: str, body_html: str) -> None:
    """
    Send a single email via SMTP TLS.
    Raises smtplib exceptions on failure.
    """
    msg = MIMEMultipart("alternative")
    msg["From"]    = SMTP_FROM
    msg["To"]      = recipient
    msg["Subject"] = subject

    msg.attach(MIMEText(body_html, "html"))

    ctx = ssl.create_default_context()
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.ehlo()
        server.starttls(context=ctx)
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.sendmail(SMTP_FROM, [recipient], msg.as_string())


def _send_in_thread(alert_id: int, recipient: str, subject: str, body: str) -> None:
    """Send email in a background thread (non-blocking)."""
    try:
        _send_smtp(recipient, subject, body)
        db.mark_alert_sent(alert_id)
        logger.info("Alert email sent to %s (alert_id=%d)", recipient, alert_id)
    except Exception as exc:
        db.mark_alert_failed(alert_id, str(exc))
        logger.error("Failed to send alert email (id=%d): %s", alert_id, exc)


# ---------------------------------------------------------------------------
# Alert templates
# ---------------------------------------------------------------------------

def _build_new_device_email(device: Dict) -> tuple:
    """Return (subject, body_html) for a new unknown/quarantined device."""
    mac    = device.get("mac_address", "N/A")
    ip     = device.get("ip_address", "N/A")
    vendor = device.get("vendor") or "Unknown"
    status = device.get("status", "UNKNOWN")

    subject = f"[Sentinel-NAC] ⚠️  New {status} Device Detected — {mac}"
    body = f"""
    <html><body style="font-family:Arial,sans-serif;color:#333;">
    <h2 style="color:#d9534f;">🔴 Sentinel-NAC Security Alert</h2>
    <p>A new <strong>{status}</strong> device has been detected on your network.</p>
    <table border="1" cellpadding="6" cellspacing="0"
           style="border-collapse:collapse;min-width:350px;">
      <tr><th align="left" bgcolor="#f5f5f5">Field</th><th align="left">Value</th></tr>
      <tr><td>MAC Address</td><td><code>{mac}</code></td></tr>
      <tr><td>IP Address</td><td><code>{ip}</code></td></tr>
      <tr><td>Vendor</td><td>{vendor}</td></tr>
      <tr><td>Status</td><td><strong>{status}</strong></td></tr>
    </table>
    <p>Please review this device in the
       <a href="http://localhost/sentinel-nac/dashboard/">Sentinel-NAC Dashboard</a>
       and allow or block it accordingly.</p>
    <hr/>
    <small>This is an automated message from Sentinel-NAC.
           Do not reply to this email.</small>
    </body></html>
    """
    return subject, body


def _build_blocked_reconnect_email(device: Dict) -> tuple:
    """Return (subject, body_html) for a blocked device that reconnected."""
    mac = device.get("mac_address", "N/A")
    ip  = device.get("ip_address", "N/A")

    subject = f"[Sentinel-NAC] 🚨 Blocked Device Reconnected — {mac}"
    body = f"""
    <html><body style="font-family:Arial,sans-serif;color:#333;">
    <h2 style="color:#d9534f;">🚨 Sentinel-NAC Security Alert</h2>
    <p>A <strong>BLOCKED</strong> device has attempted to reconnect to the network.</p>
    <table border="1" cellpadding="6" cellspacing="0"
           style="border-collapse:collapse;min-width:350px;">
      <tr><th align="left" bgcolor="#f5f5f5">Field</th><th align="left">Value</th></tr>
      <tr><td>MAC Address</td><td><code>{mac}</code></td></tr>
      <tr><td>IP Address</td><td><code>{ip}</code></td></tr>
      <tr><td>Status</td><td><strong>BLOCKED</strong></td></tr>
    </table>
    <p>Enforcement has been re-applied. Visit the
       <a href="http://localhost/sentinel-nac/dashboard/">Dashboard</a> for details.</p>
    </body></html>
    """
    return subject, body


def _build_enforcement_failure_email(mac: str, ip: str, error: str) -> tuple:
    subject = f"[Sentinel-NAC] ❗ Enforcement Failed — {mac}"
    body = f"""
    <html><body style="font-family:Arial,sans-serif;color:#333;">
    <h2 style="color:#e67e22;">⚠️  Enforcement Failure</h2>
    <p>Sentinel-NAC could not enforce quarantine for device <code>{mac}</code> ({ip}).</p>
    <p><strong>Error:</strong> {error}</p>
    <p>Please check the system logs immediately.</p>
    </body></html>
    """
    return subject, body


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

class AlertService:
    """
    High-level alert sender. Call the appropriate method when an event occurs.
    Stores every alert in the database regardless of whether email is enabled.
    """

    def __init__(self, recipient: str = ALERT_RECIPIENT):
        self.recipient = recipient

    def _send(
        self,
        alert_type: str,
        subject: str,
        body: str,
        mac: Optional[str] = None,
    ) -> None:
        """Store alert in DB and optionally send email asynchronously."""
        alert_id = db.create_alert(
            alert_type=alert_type,
            recipient=self.recipient,
            subject=subject,
            body=body,
            mac_address=mac,
        )
        if ALERT_EMAIL_ENABLED:
            t = threading.Thread(
                target=_send_in_thread,
                args=(alert_id, self.recipient, subject, body),
                daemon=True,
            )
            t.start()
        else:
            logger.debug(
                "Email alerts disabled. Alert stored in DB only (id=%d).", alert_id
            )

    def alert_new_unknown_device(self, device: Dict) -> None:
        """Trigger an alert for a newly detected unknown/quarantined device."""
        subject, body = _build_new_device_email(device)
        self._send(
            alert_type="NEW_UNKNOWN_DEVICE",
            subject=subject,
            body=body,
            mac=device.get("mac_address"),
        )

    def alert_blocked_reconnect(self, device: Dict) -> None:
        """Trigger an alert when a blocked device reconnects."""
        subject, body = _build_blocked_reconnect_email(device)
        self._send(
            alert_type="BLOCKED_RECONNECT",
            subject=subject,
            body=body,
            mac=device.get("mac_address"),
        )

    def alert_enforcement_failure(self, mac: str, ip: str, error: str) -> None:
        """Trigger an alert when enforcement fails."""
        subject, body = _build_enforcement_failure_email(mac, ip, error)
        self._send(
            alert_type="ENFORCEMENT_FAILURE",
            subject=subject,
            body=body,
            mac=mac,
        )

    def alert_event(self, alert_type: str, mac: str, ip: str, details: Optional[Dict] = None) -> None:
        """
        Generic entry point for alerts called by the main daemon.
        Dispatches to specific builders based on alert_type.
        """
        device_data = {
            "mac_address": mac,
            "ip_address": ip,
            **(details or {})
        }

        if alert_type == "NEW_UNKNOWN_DEVICE":
            self.alert_new_unknown_device(device_data)
        elif alert_type == "BLOCKED_RECONNECT":
            self.alert_blocked_reconnect(device_data)
        elif alert_type == "ENFORCEMENT_FAILURE":
            self.alert_enforcement_failure(mac, ip, details.get("error") if details else "Unknown error")
        else:
            logger.warning("Unknown alert type requested: %s", alert_type)

    def stop(self) -> None:
        """Graceful shutdown for the alert service."""
        logger.info("Alert Service shutting down.")
