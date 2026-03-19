# Sentinel-NAC: Zero-Trust Network Access Control

> **Authorized Lab Use Only** — This project is for educational cybersecurity purposes.
> Only deploy on networks and devices you own or have explicit permission to monitor.

[![License: Educational](https://img.shields.io/badge/License-Educational-blue.svg)]()
[![Python 3.x](https://img.shields.io/badge/Python-3.x-green.svg)]()
[![PHP 8.x](https://img.shields.io/badge/PHP-8.x-purple.svg)]()
[![MySQL](https://img.shields.io/badge/Database-MySQL-orange.svg)]()

---

## What Is Sentinel-NAC?

Sentinel-NAC is a student-built Zero-Trust Network Access Control system. It
continuously monitors a local lab network for newly connected devices, checks
whether they are authorized, and isolates unknown or blocked devices using a
safe controlled enforcement mechanism.

The system provides a complete security pipeline:

```
Device Joins Network
    ↓
ARP Scanner detects MAC + IP
    ↓
Fingerprinting (OUI vendor, TTL OS, reverse DNS)
    ↓
Policy Engine (Zero Trust decision)
    ↓
Enforce? → Quarantine Engine (simulation / firewall / denylist)
    ↓
Log Event + Send Alert Email
    ↓
Admin Dashboard (view, allow, block)
    ↓
PDF Report Generation
```

---

## Project Structure

```
sentinel-nac/
├── backend/
│   ├── config/          # Settings loader (reads .env)
│   ├── scanner/         # ARP scanner (passive sniff + active sweep)
│   ├── fingerprinting/  # OUI vendor + TTL OS inference
│   ├── policy/          # Zero Trust decision engine
│   ├── enforcement/     # Quarantine: simulation / firewall / denylist
│   ├── alerts/          # SMTP email alert service
│   ├── reports/         # PDF report generator (reportlab)
│   ├── database/        # MySQL pool + all DB helpers
│   ├── logs/            # Logging setup (file + console)
│   └── main.py          # Daemon entry point
├── dashboard/           # PHP admin dashboard
│   ├── index.php        # Login page
│   ├── dashboard.php    # Main dashboard (live device table)
│   ├── report.php       # Report generator UI
│   ├── logout.php       # Logout handler
│   ├── api/
│   │   ├── action.php   # Allow/Block/Quarantine API
│   │   └── logs.php     # Device event log viewer
│   └── includes/
│       ├── db.php        # PDO database connection
│       └── auth.php      # Session login/logout + audit log
├── sql/
│   ├── schema.sql        # Database schema (5 tables)
│   └── seed.sql          # Sample data for testing
├── config/
│   └── .env.example      # Environment variables template
├── docs/
│   ├── architecture.md
│   ├── setup_guide.md
│   ├── testing_guide.md
│   └── ethics_statement.md
├── tests/
│   ├── test_scanner.py
│   ├── test_policy.py
│   └── test_fingerprinting.py
├── reports/
│   └── output/           # Generated PDF reports saved here
└── requirements.txt
```

---

## Quick Start (Simulation Mode — No Root Needed)

```bash
# 1. Clone / copy project
cd sentinel-nac

# 2. Set up Python environment
python3 -m venv venv
source venv/bin/activate   
pip install -r requirements.txt

# 3. Configure
cp config/.env.example config/.env
# Edit config/.env with your DB credentials

# 4. Set up database
mysql -u root -p < sql/schema.sql
mysql -u root -p sentinel_nac < sql/seed.sql

# 5. Run in simulation mode (safe, no root required)
python3 backend/main.py --simulate

# 6. Open dashboard in XAMPP/Apache
# Copy dashboard/ to htdocs/sentinel-nac/
# Open http://localhost/sentinel-nac/
# Login: admin / Admin@1234
```

---

## Live Mode (Real Network — Requires Root)

```bash
# Edit config/.env:
#   SCAN_INTERFACE=wlan0     (your Wi-Fi interface)
#   SCAN_TARGET=192.168.1.0/24
#   ENFORCEMENT_MODE=simulation  (or firewall on Linux)

sudo python3 backend/main.py
```

---

## Default Credentials

| Username | Password   |
|----------|-----------|
| admin    | Admin@1234 |

> **Change this immediately** after first login by updating the bcrypt hash in the `admins` table.

---

## Device Status Values

| Status       | Meaning                                      |
|-------------|----------------------------------------------|
| UNKNOWN     | Seen but no decision made yet                |
| ALLOWED     | Admin-approved, trusted device               |
| BLOCKED     | Explicitly denied by admin                   |
| QUARANTINED | Restricted (default for new unknown devices) |

---

## Running Tests

```bash
cd sentinel-nac
python3 -m pytest tests/ -v
```

No network access or real database required — all tests use simulation/mocks.

---

## Team

| Roll Number | Name          | Role                          |
|-------------|---------------|-------------------------------|
| 24DCS136    | Yashvi Thakkar | Documentation & Alerts       |
| 24DCS076    | Mantra Patel  | Full-Stack / Architecture     |
| 24DCS089    | Tirth Patel   | Python Engine & Reports       |
| 24DCS071    | Dhruv Patel   | Red Team Testing & Wireshark  |

---

## Ethics

This project is for **defensive, educational** cybersecurity only.
See `docs/ethics_statement.md` for the full authorized-use policy.
