# Sentinel-NAC: Step-by-Step Setup Guide

## Prerequisites Checklist

- [ ] Python 3.8+ installed
- [ ] MySQL 8.0+ (or MariaDB 10.6+) installed and running
- [ ] XAMPP (Apache + PHP 8.x) installed
- [ ] A private Wi-Fi router or mobile hotspot (for live mode)
- [ ] 2+ test devices (laptops, phones) you own

---

## Part 1: Python Environment Setup

```bash
# Navigate to project directory
cd /path/to/sentinel-nac

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate         # Linux/macOS
# venv\Scripts\activate.bat      # Windows

# Install Python dependencies
pip install -r requirements.txt
```

**Verify installation:**
```bash
python3 -c "import scapy; print('Scapy OK')"
python3 -c "import mysql.connector; print('MySQL connector OK')"
python3 -c "from reportlab.lib import colors; print('Reportlab OK')"
```

---

## Part 2: MySQL Database Setup

```bash
# Log into MySQL
mysql -u root -p

# Run schema creation
mysql> SOURCE /path/to/sentinel-nac/sql/schema.sql;

# Run seed data (optional but recommended for demo)
mysql> SOURCE /path/to/sentinel-nac/sql/seed.sql;

# Create a dedicated database user (recommended)
mysql> CREATE USER 'sentinel_user'@'localhost' IDENTIFIED BY 'YourStrongPass!';
mysql> GRANT ALL PRIVILEGES ON sentinel_nac.* TO 'sentinel_user'@'localhost';
mysql> FLUSH PRIVILEGES;
```

**Verify:**
```bash
mysql -u sentinel_user -p sentinel_nac -e "SHOW TABLES;"
```

---

## Part 3: Configuration (.env File)

```bash
# Copy example to actual config
cp config/.env.example config/.env

# Edit config/.env with your values:
nano config/.env
```

**Key settings to update:**
```
DB_HOST=127.0.0.1
DB_USER=sentinel_user
DB_PASSWORD=YourStrongPass!

# For live mode: your Wi-Fi interface name
SCAN_INTERFACE=wlan0          # Linux
# SCAN_INTERFACE=en0          # macOS
# SCAN_INTERFACE=Wi-Fi        # Windows (run as admin)

SCAN_TARGET=192.168.1.0/24   # Your hotspot subnet

# Start with simulation mode, switch to firewall when ready
ENFORCEMENT_MODE=simulation

# Email alerts (optional)
ALERT_EMAIL_ENABLED=false
```

**Find your interface name:**
```bash
# Linux/macOS
ip link show        # or: ifconfig -a
# Windows
ipconfig /all
```

**Find your subnet:**
```bash
# Linux/macOS
ip route show | grep default
# Windows
ipconfig | grep "Default Gateway"
```

---

## Part 4: PHP / XAMPP Dashboard Setup

1. Start **XAMPP Control Panel** → Start Apache + MySQL

2. Copy the dashboard to XAMPP web root:
   ```bash
   # macOS XAMPP
   cp -r dashboard/ /Applications/XAMPP/xamppfiles/htdocs/sentinel-nac/

   # Linux XAMPP
   cp -r dashboard/ /opt/lampp/htdocs/sentinel-nac/

   # Or create a symlink (faster for development):
   ln -s /path/to/sentinel-nac/dashboard /Applications/XAMPP/xamppfiles/htdocs/sentinel-nac
   ```

3. Open dashboard: `http://localhost/sentinel-nac/`

4. Login with:
   - **Username:** `admin`
   - **Password:** `Admin@1234`

---

## Part 5: Running the Backend

### Option A: Simulation Mode (Recommended for Demo)
```bash
# No root required — emits fake devices
cd sentinel-nac
source venv/bin/activate
python3 backend/main.py --simulate
```

### Option B: Live Mode (Requires Root / Admin)
```bash
# Real network capture on your private lab hotspot
sudo python3 backend/main.py
```

### Option C: No Enforcement (Log Only)
```bash
sudo python3 backend/main.py --no-enforce
```

---

## Part 6: Lab Network Topology

```
[ Laptop running Sentinel-NAC ]
        |
        |  connected to
        ↓
[ Private Mobile Hotspot / Router ]   ←── [ Test Laptop 2 ]
                                      ←── [ Test Phone ]
```

**Setup steps:**
1. Enable mobile hotspot on your phone (e.g., SSID: `SentinelLab`)
2. Connect the Sentinel-NAC laptop to this hotspot
3. Connect your test devices to the same hotspot
4. Set `SCAN_TARGET` to the hotspot's subnet (e.g., `192.168.43.0/24`)
5. Set `SCAN_INTERFACE` to your wireless interface

---

## Part 7: Changing Admin Password

1. Generate a new bcrypt hash in Python:
   ```python
   import bcrypt
   pw = b"YourNewStrongPassword!"
   print(bcrypt.hashpw(pw, bcrypt.gensalt(12)).decode())
   ```
2. Update the database:
   ```sql
   UPDATE admins SET password = '$2y$12$...' WHERE username = 'admin';
   ```

---

## Part 8: Generating a PDF Report

### From Dashboard:
1. Click **Reports** in the sidebar
2. Select a date range
3. Click **Generate & Download PDF**

### From CLI:
```bash
source venv/bin/activate
python3 backend/reports/report_generator.py \
    --start 2024-01-01 \
    --end 2024-12-31 \
    --out reports/output/
```
