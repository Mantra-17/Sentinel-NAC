-- =============================================================
-- Sentinel-NAC: Seed Data for Testing
-- File: sql/seed.sql
-- Purpose: Insert sample records for development/demo purposes
-- =============================================================

USE sentinel_nac;

-- Default admin account (password: Admin@1234 -- change immediately)
INSERT INTO admins (username, password, email, role) VALUES
    ('admin', '$2y$12$.De1o9wL5hc7nJdaY4MopuEuB/dRnk.VKuuRBptyzp3WUHf8BAQbC', 'admin@lab.local', 'superadmin')
ON DUPLICATE KEY UPDATE username = username;

-- Sample known/allowed device (your own machine)
INSERT INTO devices
    (mac_address, ip_address, hostname, vendor, probable_os,
     probable_device_type, fingerprint_confidence, status, first_seen, last_seen)
VALUES
    ('AA:BB:CC:11:22:33', '192.168.1.10', 'lab-host-1',
     'Intel Corporate', 'Linux/Ubuntu', 'Laptop', 85,
     'ALLOWED',
     NOW() - INTERVAL 2 DAY, NOW() - INTERVAL 1 HOUR),

    ('AA:BB:CC:44:55:66', '192.168.1.20', 'lab-phone',
     'Apple Inc.', 'iOS', 'Mobile/Tablet', 90,
     'ALLOWED',
     NOW() - INTERVAL 1 DAY, NOW() - INTERVAL 30 MINUTE),

    ('AA:BB:CC:77:88:99', '192.168.1.30', NULL,
     'Unknown', 'Windows', 'Laptop', 60,
     'QUARANTINED',
     NOW() - INTERVAL 10 MINUTE, NOW() - INTERVAL 5 MINUTE),

    ('AA:BB:CC:00:FF:EE', '192.168.1.40', 'rogue-device',
     'Samsung Electronics', 'Android', 'Mobile/Tablet', 75,
     'BLOCKED',
     NOW() - INTERVAL 5 HOUR, NOW() - INTERVAL 2 HOUR)
ON DUPLICATE KEY UPDATE last_seen = VALUES(last_seen);

-- Sample events
INSERT INTO device_events (mac_address, ip_address, event_type, old_status, new_status, actor, details) VALUES
    ('AA:BB:CC:77:88:99', '192.168.1.30', 'DEVICE_DISCOVERED', NULL, 'QUARANTINED', 'system', 'First detection via ARP'),
    ('AA:BB:CC:77:88:99', '192.168.1.30', 'ENFORCEMENT_STARTED', 'QUARANTINED', 'QUARANTINED', 'system', 'Quarantine enforcement activated'),
    ('AA:BB:CC:00:FF:EE', '192.168.1.40', 'DEVICE_DISCOVERED', NULL, 'QUARANTINED', 'system', 'First detection via ARP'),
    ('AA:BB:CC:00:FF:EE', '192.168.1.40', 'STATUS_CHANGED', 'QUARANTINED', 'BLOCKED', 'admin', 'Admin blocked device'),
    ('AA:BB:CC:11:22:33', '192.168.1.10', 'DEVICE_DISCOVERED', NULL, 'QUARANTINED', 'system', 'First detection'),
    ('AA:BB:CC:11:22:33', '192.168.1.10', 'STATUS_CHANGED', 'QUARANTINED', 'ALLOWED', 'admin', 'Admin approved lab host');

-- Sample alerts
INSERT INTO alerts (mac_address, alert_type, recipient, subject, body, sent_at, status) VALUES
    ('AA:BB:CC:77:88:99', 'NEW_UNKNOWN_DEVICE', 'admin@lab.local',
     '[Sentinel-NAC] New unknown device detected',
     'A new device (AA:BB:CC:77:88:99) was detected at 192.168.1.30. Status: QUARANTINED.',
     NOW() - INTERVAL 10 MINUTE, 'SENT'),
    ('AA:BB:CC:00:FF:EE', 'BLOCKED_RECONNECT', 'admin@lab.local',
     '[Sentinel-NAC] Blocked device attempted reconnection',
     'Device AA:BB:CC:00:FF:EE (rogue-device) attempted to rejoin the network. It remains BLOCKED.',
     NOW() - INTERVAL 2 HOUR, 'SENT');

