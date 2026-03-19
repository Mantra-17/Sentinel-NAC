# Sentinel-NAC: Testing Guide

## Test Environment

All tests are designed to run **without a real network, root access, or live database**.
They use simulation mode and mocked database calls.

---

## Running All Tests

```bash
cd sentinel-nac
source venv/bin/activate

# Run full test suite
python3 -m pytest tests/ -v

# Run specific test file
python3 -m pytest tests/test_scanner.py -v
python3 -m pytest tests/test_policy.py -v
python3 -m pytest tests/test_fingerprinting.py -v
```

---

## Test Cases Covered

### Scanner Tests (`tests/test_scanner.py`)
| Test | Description |
|------|-------------|
| `test_scanner_starts_and_stops` | Scanner starts without errors |
| `test_scanner_calls_callback`   | on_device callback is invoked |
| `test_scanner_deduplicates`     | Same MAC+IP fires callback once only |
| `test_scanner_notifies_on_ip_change` | IP change for same MAC re-triggers |
| `test_scanner_ignores_broadcast` | Broadcast MACs are filtered |
| `test_simulation_mode_detection` | Simulate flag set correctly |

### Policy Tests (`tests/test_policy.py`)
| Test | Description |
|------|-------------|
| `test_new_unknown_device_gets_quarantined` | New device defaults to QUARANTINED |
| `test_allowed_device_gets_permit_action`   | ALLOWED → permit action |
| `test_blocked_existing_device_triggers_alert` | BLOCKED reconnect → alert |
| `test_quarantined_device_action_is_enforce`   | QUARANTINED → enforce |
| `test_admin_allow_calls_update`              | Allow admin action |
| `test_admin_block_calls_update`              | Block admin action |

### Fingerprinting Tests (`tests/test_fingerprinting.py`)
| Test | Description |
|------|-------------|
| `test_vendor_lookup_known_oui`   | Raspberry Pi OUI resolves |
| `test_vendor_lookup_unknown_oui` | Unknown OUI returns None |
| `test_vendor_lookup_vmware`      | VMware OUI resolves exactly |
| `test_ttl_linux_range`           | TTL=64 → Linux/macOS |
| `test_ttl_windows_range`         | TTL=128 → Windows |
| `test_ttl_unknown`               | TTL=1 → None |
| `test_fingerprint_device_returns_dict` | Output has required keys |
| `test_fingerprint_with_no_oui`   | Unknown device → confidence=0 |

---

## Manual Demo Test Plan

Run these scenarios in simulation mode to demonstrate the full workflow:

### Scenario 1: New Device Detection
```bash
python3 backend/main.py --simulate
```
**Expected:** Scanner logs `NEW device` for each simulated MAC.
Dashboard shows devices with QUARANTINED status.

### Scenario 2: Admin Approves Device
1. Open dashboard → `http://localhost/sentinel-nac/`
2. Find device `AA:BB:CC:11:22:33`
3. Click **Allow**
**Expected:** Status changes to ALLOWED in database and dashboard.

### Scenario 3: Admin Blocks a Rogue Device
1. Find device `AA:BB:CC:77:88:99` (quarantined)
2. Click **Block**
**Expected:** Status → BLOCKED. Next re-detection triggers alert in DB.

### Scenario 4: View Event Log
1. Click the logs icon next to any device
**Expected:** Full audit trail of discovery, status changes, and enforcement events.

### Scenario 5: Generate PDF Report
1. Click **Reports** in sidebar
2. Select last 7 days
3. Click **Generate & Download PDF**
**Expected:** PDF downloads with device summary and event timeline.

### Scenario 6: Verify Alert Storage
```sql
SELECT * FROM alerts ORDER BY created_at DESC LIMIT 5;
```
**Expected:** Rows with `NEW_UNKNOWN_DEVICE` and/or `BLOCKED_RECONNECT` type.

---

## Wireshark Verification (Live Mode)

When running in live mode on a private network:

1. Open Wireshark on the Sentinel-NAC laptop
2. Filter: `arp`
3. Connect a test device to the hotspot
4. **Expected:** ARP request appears in Wireshark AND device appears in dashboard

---

## Common Issues

| Problem | Solution |
|---------|----------|
| `Permission denied` on raw socket | Run `sudo python3 backend/main.py` |
| `scapy not found` | Run `pip install scapy` |
| Dashboard shows "Database connection failed" | Check `.env` DB credentials and XAMPP MySQL status |
| Email alerts not sending | Set `ALERT_EMAIL_ENABLED=true` and configure SMTP in `.env` |
| PDF not generating | Run `pip install reportlab` |
| Interface not found | Run `ip link show` to find correct interface name |
