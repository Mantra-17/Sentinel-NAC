"""
Sentinel-NAC: Policy Engine Tests
File: tests/test_policy.py
Purpose: Unit tests for DecisionEngine using mocked database.
"""

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from policy.decision_engine import DecisionEngine


# ---------------------------------------------------------------------------
# Mock helpers
# ---------------------------------------------------------------------------

def _mock_device(mac, status):
    return {
        "id": 1, "mac_address": mac, "ip_address": "192.168.1.50",
        "status": status, "vendor": None, "probable_os": None,
        "probable_device_type": None, "fingerprint_confidence": 0,
        "hostname": None, "first_seen": "2024-01-01 00:00:00",
        "last_seen":  "2024-01-01 00:00:00",
    }


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@patch("policy.decision_engine.db")
def test_new_unknown_device_gets_quarantined(mock_db):
    """A brand-new device should be assigned QUARANTINED by default."""
    mac = "BB:CC:DD:11:22:33"
    mock_db.get_device_by_mac.return_value = None  # device not in DB yet
    inserted = _mock_device(mac, "QUARANTINED")
    mock_db.upsert_device.return_value = inserted

    engine   = DecisionEngine()
    result   = engine.evaluate(mac=mac, ip="192.168.1.50")

    assert result["is_new_device"]   is True
    assert result["action"]          == "enforce"
    assert result["trigger_alert"]   is True
    mock_db.log_event.assert_called()


@patch("policy.decision_engine.db")
def test_allowed_device_gets_permit_action(mock_db):
    """A device with ALLOWED status should receive 'permit' action."""
    mac = "AA:BB:CC:11:22:33"
    mock_db.get_device_by_mac.return_value = _mock_device(mac, "ALLOWED")
    mock_db.upsert_device.return_value = _mock_device(mac, "ALLOWED")

    engine = DecisionEngine()
    result = engine.evaluate(mac=mac, ip="192.168.1.10")

    assert result["action"]        == "permit"
    assert result["trigger_alert"] is False


@patch("policy.decision_engine.db")
def test_blocked_existing_device_triggers_alert(mock_db):
    """A known BLOCKED device reconnecting should trigger an alert."""
    mac = "AA:BB:CC:00:FF:EE"
    blocked = _mock_device(mac, "BLOCKED")
    mock_db.get_device_by_mac.return_value = blocked
    mock_db.upsert_device.return_value     = blocked

    engine = DecisionEngine()
    result = engine.evaluate(mac=mac, ip="192.168.1.40")

    assert result["action"]        == "enforce"
    assert result["trigger_alert"] is True
    mock_db.log_event.assert_called()


@patch("policy.decision_engine.db")
def test_quarantined_device_action_is_enforce(mock_db):
    """A QUARANTINED device should receive 'enforce' action."""
    mac = "AA:BB:CC:77:88:99"
    q_device = _mock_device(mac, "QUARANTINED")
    mock_db.get_device_by_mac.return_value = q_device
    mock_db.upsert_device.return_value     = q_device

    engine = DecisionEngine()
    result = engine.evaluate(mac=mac, ip="192.168.1.30")

    assert result["action"] == "enforce"


@patch("policy.decision_engine.db")
def test_admin_allow_calls_update(mock_db):
    """admin_allow() should call update_device_status with ALLOWED."""
    mock_db.update_device_status.return_value = True
    engine = DecisionEngine()
    engine.admin_allow("AA:BB:CC:11:22:33", admin_user="admin")
    mock_db.update_device_status.assert_called_once_with(
        "AA:BB:CC:11:22:33", "ALLOWED", actor="admin"
    )


@patch("policy.decision_engine.db")
def test_admin_block_calls_update(mock_db):
    """admin_block() should call update_device_status with BLOCKED."""
    mock_db.update_device_status.return_value = True
    engine = DecisionEngine()
    engine.admin_block("AA:BB:CC:44:55:66", admin_user="admin")
    mock_db.update_device_status.assert_called_once_with(
        "AA:BB:CC:44:55:66", "BLOCKED", actor="admin"
    )


# ---------------------------------------------------------------------------
# Run standalone
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    test_new_unknown_device_gets_quarantined()
    test_allowed_device_gets_permit_action()
    test_blocked_existing_device_triggers_alert()
    test_quarantined_device_action_is_enforce()
    test_admin_allow_calls_update()
    test_admin_block_calls_update()
    print("All policy tests passed ✓")
