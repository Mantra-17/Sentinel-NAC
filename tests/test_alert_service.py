"""
Sentinel-NAC: Alert Service Unit Tests
Tests alert_event() dispatching and email body construction.
"""
import unittest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from alerts.email_alert import (
    AlertService,
    _build_new_device_email,
    _build_blocked_reconnect_email,
    _build_enforcement_failure_email,
)


class TestAlertTemplates(unittest.TestCase):
    """Test that email templates render correctly with device data."""

    def test_new_device_email_renders_all_fields(self):
        """New device email should include MAC, IP, vendor, and status."""
        device = {
            "mac_address": "AA:BB:CC:11:22:33",
            "ip_address": "192.168.1.10",
            "vendor": "Raspberry Pi Foundation",
            "status": "QUARANTINED",
        }
        subject, body = _build_new_device_email(device)

        self.assertIn("AA:BB:CC:11:22:33", subject)
        self.assertIn("QUARANTINED", subject)
        self.assertIn("AA:BB:CC:11:22:33", body)
        self.assertIn("192.168.1.10", body)
        self.assertIn("Raspberry Pi Foundation", body)
        self.assertIn("QUARANTINED", body)

    def test_new_device_email_handles_missing_vendor(self):
        """Missing vendor should display 'Unknown'."""
        device = {
            "mac_address": "FF:FF:FF:00:00:01",
            "ip_address": "10.0.0.1",
            "vendor": None,
            "status": "QUARANTINED",
        }
        subject, body = _build_new_device_email(device)
        self.assertIn("Unknown", body)

    def test_blocked_reconnect_email(self):
        """Blocked reconnect email should include MAC and IP."""
        device = {
            "mac_address": "AA:BB:CC:77:88:99",
            "ip_address": "192.168.1.30",
        }
        subject, body = _build_blocked_reconnect_email(device)

        self.assertIn("AA:BB:CC:77:88:99", subject)
        self.assertIn("Blocked", subject)
        self.assertIn("192.168.1.30", body)

    def test_enforcement_failure_email(self):
        """Enforcement failure email should include error details."""
        subject, body = _build_enforcement_failure_email(
            "AA:BB:CC:11:22:33", "192.168.1.10", "iptables permission denied"
        )
        self.assertIn("AA:BB:CC:11:22:33", subject)
        self.assertIn("iptables permission denied", body)


class TestAlertServiceDispatch(unittest.TestCase):
    """Test that alert_event() dispatches to the correct handler."""

    @patch('alerts.email_alert.db')
    def test_alert_event_dispatches_new_unknown_device(self, mock_db):
        """alert_event with NEW_UNKNOWN_DEVICE type calls alert_new_unknown_device."""
        mock_db.create_alert.return_value = 1

        service = AlertService(recipient="test@example.com")
        device = {
            "mac_address": "AA:BB:CC:11:22:33",
            "ip_address": "192.168.1.10",
            "vendor": "Test Vendor",
            "status": "QUARANTINED",
        }

        service.alert_event("NEW_UNKNOWN_DEVICE", "AA:BB:CC:11:22:33", "192.168.1.10", details=device)

        # Verify an alert was created in the DB
        mock_db.create_alert.assert_called_once()
        call_args = mock_db.create_alert.call_args
        self.assertEqual(call_args.kwargs.get("alert_type") or call_args[1]["alert_type"], "NEW_UNKNOWN_DEVICE")

    @patch('alerts.email_alert.db')
    def test_alert_event_dispatches_blocked_reconnect(self, mock_db):
        """alert_event with BLOCKED_RECONNECT type calls alert_blocked_reconnect."""
        mock_db.create_alert.return_value = 2

        service = AlertService(recipient="test@example.com")
        device = {
            "mac_address": "AA:BB:CC:77:88:99",
            "ip_address": "192.168.1.30",
            "status": "BLOCKED",
        }

        service.alert_event("BLOCKED_RECONNECT", "AA:BB:CC:77:88:99", "192.168.1.30", details=device)

        mock_db.create_alert.assert_called_once()
        call_args = mock_db.create_alert.call_args
        self.assertEqual(call_args.kwargs.get("alert_type") or call_args[1]["alert_type"], "BLOCKED_RECONNECT")

    @patch('alerts.email_alert.db')
    def test_alert_event_with_device_record_has_correct_keys(self, mock_db):
        """When details is a device DB record, the email template should find all needed keys."""
        mock_db.create_alert.return_value = 3

        service = AlertService(recipient="test@example.com")
        # This is what decision["device"] looks like — full DB record
        device_record = {
            "id": 1,
            "mac_address": "AA:BB:CC:11:22:33",
            "ip_address": "192.168.1.10",
            "hostname": "raspberrypi",
            "vendor": "Raspberry Pi Foundation",
            "probable_os": "Linux (Raspberry Pi)",
            "probable_device_type": "IoT Device",
            "fingerprint_confidence": 75,
            "status": "QUARANTINED",
        }

        # This should NOT crash — the fix ensures device_data has mac_address and status
        service.alert_event("NEW_UNKNOWN_DEVICE", "AA:BB:CC:11:22:33", "192.168.1.10", details=device_record)
        mock_db.create_alert.assert_called_once()


if __name__ == "__main__":
    unittest.main()
