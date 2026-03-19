# Sentinel-NAC: System Architecture

## Overview

Sentinel-NAC implements a Zero-Trust Network Access Control pipeline
for small local area networks. Every device joining the network is
treated as untrusted by default until an administrator explicitly allows it.

---

## Component Diagram

```
Private Lab Network (Router / Hotspot)
        |
        |  (ARP packets)
        ↓
┌─────────────────────────────────────────────────────────────┐
│                   Sentinel-NAC Engine (Python)               │
│                                                              │
│  ┌────────────────┐    ┌─────────────────┐                  │
│  │  ARP Scanner   │───▶│  Fingerprinting │                  │
│  │  (Scapy)       │    │  (OUI/TTL/DNS)  │                  │
│  └────────────────┘    └────────┬────────┘                  │
│                                 │                            │
│                        ┌────────▼────────┐                  │
│                        │ Policy / Decision│                  │
│                        │ Engine          │                  │
│                        └────────┬────────┘                  │
│                                 │                            │
│              ┌──────────────────┼──────────────────┐        │
│              ▼                  ▼                   ▼        │
│     ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│     │ Quarantine   │  │  Alert Svc   │  │  Logger      │   │
│     │ Engine       │  │  (SMTP)      │  │  (File+DB)   │   │
│     └──────────────┘  └──────────────┘  └──────────────┘   │
│              │                                               │
└──────────────┼───────────────────────────────────────────────┘
               │
               ▼
        ┌─────────────┐
        │  MySQL DB   │  ←──────── PHP Admin Dashboard
        │  sentinel   │             (Browser)
        │  _nac       │
        └─────────────┘
               │
               ▼
        ┌──────────────┐
        │ PDF Reports  │
        │ (reportlab)  │
        └──────────────┘
```

---

## Module Descriptions

### 1. ARP Scanner (`backend/scanner/arp_scanner.py`)
- **Technology:** Python + Scapy
- **Passive mode:** Sniffs ARP broadcast packets in real time
- **Active mode:** Periodically sends ARP sweeps to all IPs in subnet
- **Simulation mode:** Emits pre-defined fake devices for demo
- **Output:** Callback with (MAC, IP, source) for each new/changed device

### 2. Device Fingerprinting (`backend/fingerprinting/fingerprint.py`)
- **OUI lookup:** Maps MAC prefix to hardware vendor using offline table
- **TTL inference:** Pings device and maps TTL to probable OS
- **Reverse DNS:** Looks up hostname from IP
- **Output:** Dict with vendor, probable_os, probable_device_type, confidence

### 3. Policy Engine (`backend/policy/decision_engine.py`)
- **Zero Trust:** All new devices default to QUARANTINED
- **Reads:** Device status from MySQL database
- **Returns:** Action (permit / enforce / no_change) + alert flag
- **Admin actions:** allow / block / quarantine via same interface

### 4. Quarantine Engine (`backend/enforcement/quarantine.py`)
- **Simulation mode:** Logs restriction, no OS changes (safe for demo)
- **Firewall mode:** Uses iptables DROP rules (Linux, requires root)
- **Denylist mode:** In-memory MAC deny list (portable, limited effect)
- **Interface:** Abstract BaseEnforcement for easy extension

### 5. Alert Service (`backend/alerts/email_alert.py`)
- **Triggers:** New unknown device / blocked reconnect / enforcement failure
- **Delivery:** HTML email via SMTP TLS (runs in background thread)
- **Storage:** All alerts stored in DB regardless of email setting

### 6. Report Generator (`backend/reports/report_generator.py`)
- **Library:** reportlab
- **Content:** Status summary, device table, top restricted devices, events
- **Trigger:** CLI or PHP dashboard
- **Output:** PDF file in `reports/output/`

### 7. Admin Dashboard (PHP + Bootstrap 5)
- **Login:** Session-based with bcrypt password verification
- **Device table:** Live, auto-refreshes every 10s via JS reload
- **Actions:** Allow / Block / Quarantine via AJAX (no page reload)
- **Logs view:** Per-device event history
- **Report page:** Date range picker that calls Python PDF generator

---

## Database Schema

```
admins           → admin accounts (username, bcrypt password, role)
devices          → detected devices (MAC, IP, vendor, OS, status, timestamps)
device_events    → full audit trail (event type, old/new status, actor, details)
alerts           → sent notifications (type, recipient, status, body)
system_settings  → runtime config key-value store
```

---

## Data Flow (End-to-End)

```
1. New device joins Wi-Fi / LAN
2. Router sends ARP broadcast
3. ARPScanner captures the packet
4. Fingerprint module enriches device metadata
5. PolicyEngine.evaluate() checks DB → returns action
6. Device is upserted into 'devices' table
7. If action == 'enforce':
     QuarantineController.handle_device_decision() → restriction applied
8. If trigger_alert:
     AlertService.alert_new_unknown_device() → DB entry + SMTP email
9. Admin opens dashboard → sees device with QUARANTINED status
10. Admin clicks "Allow" → AJAX calls action.php → DB updated
11. Next scanner cycle: PolicyEngine sees ALLOWED → releases enforcement
12. Admin clicks "Reports" → PDF generated with full history
```
