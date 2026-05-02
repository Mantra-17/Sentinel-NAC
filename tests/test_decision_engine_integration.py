"""
Sentinel-NAC: Decision Engine Integration Tests
Tests the full evaluate() → handle_device_decision() flow with mocked DB.
"""
import unittest
from unittest.mock import MagicMock, patch, call
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from policy.decision_engine import DecisionEngine


class TestDecisionEngineIntegration(unittest.TestCase):
    """Integration tests for the policy decision pipeline."""

    @patch('database.db.log_event')
    @patch('database.db.upsert_device')
    @patch('database.db.get_device_by_mac')
    def test_new_device_is_quarantined_and_triggers_alert(self, mock_get, mock_upsert, mock_log):
        """New device → QUARANTINED → enforce + alert."""
        mock_get.return_value = None  # Device not in DB
        mock_upsert.return_value = {
            "id": 1,
            "mac_address": "AA:BB:CC:DD:EE:FF",
            "ip_address": "192.168.1.50",
            "status": "QUARANTINED",
            "vendor": "Lab Test Device",
        }

        engine = DecisionEngine()
        result = engine.evaluate("AA:BB:CC:DD:EE:FF", "192.168.1.50")

        self.assertTrue(result["is_new_device"])
        self.assertEqual(result["action"], "enforce")
        self.assertTrue(result["trigger_alert"])
        self.assertEqual(result["device"]["status"], "QUARANTINED")
        # Verify an event was logged for the new device
        mock_log.assert_called_once()
        log_call = mock_log.call_args
        self.assertEqual(log_call.kwargs.get("event_type"), "DEVICE_DISCOVERED")

    @patch('database.db.log_event')
    @patch('database.db.upsert_device')
    @patch('database.db.get_device_by_mac')
    def test_allowed_device_is_permitted(self, mock_get, mock_upsert, mock_log):
        """Known ALLOWED device → permit, no alert."""
        mock_get.return_value = {"mac_address": "11:22:33:44:55:66", "status": "ALLOWED"}
        mock_upsert.return_value = {
            "id": 2,
            "mac_address": "11:22:33:44:55:66",
            "ip_address": "192.168.1.100",
            "status": "ALLOWED",
        }

        engine = DecisionEngine()
        result = engine.evaluate("11:22:33:44:55:66", "192.168.1.100")

        self.assertFalse(result["is_new_device"])
        self.assertEqual(result["action"], "permit")
        self.assertFalse(result["trigger_alert"])

    @patch('database.db.log_event')
    @patch('database.db.upsert_device')
    @patch('database.db.get_device_by_mac')
    def test_blocked_device_reconnect_triggers_alert(self, mock_get, mock_upsert, mock_log):
        """Known BLOCKED device reconnecting → enforce + alert."""
        mock_get.return_value = {"mac_address": "AA:BB:CC:77:88:99", "status": "BLOCKED"}
        mock_upsert.return_value = {
            "id": 3,
            "mac_address": "AA:BB:CC:77:88:99",
            "ip_address": "192.168.1.30",
            "status": "BLOCKED",
        }

        engine = DecisionEngine()
        result = engine.evaluate("AA:BB:CC:77:88:99", "192.168.1.30")

        self.assertFalse(result["is_new_device"])
        self.assertEqual(result["action"], "enforce")
        self.assertTrue(result["trigger_alert"])

    @patch('database.db.log_event')
    @patch('database.db.upsert_device')
    @patch('database.db.get_device_by_mac')
    def test_quarantined_known_device_no_alert(self, mock_get, mock_upsert, mock_log):
        """Known QUARANTINED (not new) device → enforce, NO alert (alerts only for BLOCKED)."""
        mock_get.return_value = {"mac_address": "AA:BB:CC:11:22:33", "status": "QUARANTINED"}
        mock_upsert.return_value = {
            "id": 4,
            "mac_address": "AA:BB:CC:11:22:33",
            "ip_address": "192.168.1.10",
            "status": "QUARANTINED",
        }

        engine = DecisionEngine()
        result = engine.evaluate("AA:BB:CC:11:22:33", "192.168.1.10")

        self.assertFalse(result["is_new_device"])
        self.assertEqual(result["action"], "enforce")
        self.assertFalse(result["trigger_alert"])  # No alert for quarantined reconnect

    @patch('database.db.log_event')
    @patch('database.db.upsert_device')
    @patch('database.db.get_device_by_mac')
    def test_unknown_status_defensive_fallback(self, mock_get, mock_upsert, mock_log):
        """UNKNOWN status → enforce + alert + audit log (defensive fallback)."""
        mock_get.return_value = {"mac_address": "FF:FF:FF:00:00:01", "status": "UNKNOWN"}
        mock_upsert.return_value = {
            "id": 5,
            "mac_address": "FF:FF:FF:00:00:01",
            "ip_address": "192.168.1.200",
            "status": "UNKNOWN",
        }

        engine = DecisionEngine()
        result = engine.evaluate("FF:FF:FF:00:00:01", "192.168.1.200")

        self.assertEqual(result["action"], "enforce")
        self.assertTrue(result["trigger_alert"])
        # Verify that the UNKNOWN branch now logs an event
        mock_log.assert_called()

    @patch('database.db.log_event')
    @patch('database.db.upsert_device')
    @patch('database.db.get_device_by_mac')
    def test_fingerprint_data_passed_to_upsert(self, mock_get, mock_upsert, mock_log):
        """Fingerprint metadata is forwarded to upsert_device correctly."""
        mock_get.return_value = None
        mock_upsert.return_value = {
            "id": 6,
            "mac_address": "B8:27:EB:AA:BB:CC",
            "ip_address": "192.168.1.42",
            "status": "QUARANTINED",
            "vendor": "Raspberry Pi Foundation",
        }

        fp = {
            "hostname": "raspberrypi",
            "vendor": "Raspberry Pi Foundation",
            "probable_os": "Linux (Raspberry Pi)",
            "probable_device_type": "IoT Device",
            "fingerprint_confidence": 75,
        }

        engine = DecisionEngine()
        engine.evaluate("B8:27:EB:AA:BB:CC", "192.168.1.42", fingerprint=fp)

        mock_upsert.assert_called_once_with(
            mac="B8:27:EB:AA:BB:CC",
            ip="192.168.1.42",
            hostname="raspberrypi",
            vendor="Raspberry Pi Foundation",
            probable_os="Linux (Raspberry Pi)",
            probable_device_type="IoT Device",
            fingerprint_confidence=75,
        )


if __name__ == "__main__":
    unittest.main()
