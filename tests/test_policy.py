"""
Sentinel-NAC: Policy Engine Unit Tests
"""
import unittest
from unittest.mock import MagicMock, patch
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from policy.decision_engine import DecisionEngine

class TestPolicy(unittest.TestCase):
    @patch('database.db.get_device_by_mac')
    @patch('database.db.upsert_device')
    @patch('database.db.log_event')
    def test_evaluate_new_device(self, mock_log, mock_upsert, mock_get):
        """Verify that a new device is quarantined by default."""
        mock_get.return_value = None
        mock_upsert.return_value = {"status": "QUARANTINED", "mac_address": "AA:BB:CC:DD:EE:FF"}
        
        engine = DecisionEngine()
        result = engine.evaluate("AA:BB:CC:DD:EE:FF", "192.168.1.50")
        
        self.assertTrue(result["is_new_device"])
        self.assertEqual(result["action"], "enforce")
        self.assertTrue(result["trigger_alert"])

if __name__ == "__main__":
    unittest.main()
