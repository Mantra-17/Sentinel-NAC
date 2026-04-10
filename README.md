# Sentinel-NAC: Modern Network Access Control

> **Security Engineering Project** — A Zero-Trust solution for local network monitoring and enforcement.

Sentinel-NAC is an industrial-grade Network Access Control (NAC) system designed to monitor, identify, and manage devices on a local area network. Built on a modern **Next.js & Python** stack, it implements Zero-Trust principles by automatically quarantining unknown devices until explicitly approved by an administrator.

---

## 🚀 Key Features

- **Live ARP Scanning**: Real-time discovery of connected devices using Scapy (sniffing and active sweeping).
- **Zero-Trust Enforcement**: Automatic `QUARANTINED` status for all new discoveries.
- **Administrative Control**: Professional dashboard with Glassmorphic UI to Allow, Block, or Forget devices.
- **Device Fingerprinting**: Automated OUI-based vendor lookup and TTL-based OS estimation.
- **Persistence**: Full state management powered by **PostgreSQL** and **Prisma ORM**.
- **Security Alerts**: Real-time SMTP notifications for critical security events.

---

## 🛠️ Technology Stack

| Component | Technology |
| :--- | :--- |
| **Frontend** | Next.js 14, TailwindCSS, Lucide Icons |
| **Backend Engine** | Python 3.12+, Scapy (Link-Layer) |
| **Database** | PostgreSQL |
| **ORM** | Prisma |
| **Authentication** | NextAuth.js |

---

## 📂 Project Structure

```text
sentinel-nac/
├── backend/            # Python core engine (Scanner, Policy, Alerts)
├── dashboard/          # Next.js administrative dashboard
├── config/             # Shared environment configuration
├── docs/               # Architecture and testing documentation
├── sql/                # Database schemas and seeds
├── venv/               # Python virtual environment (ignored)
└── .gitignore          # Comprehensive exclusion rules
```

---

## 🏁 Quick Start

### 1. Prerequisites
- **Python 3.12+**
- **Node.js 18+**
- **PostgreSQL** (running locally or remotely)

### 2. Environment Configuration
```bash
cp config/.env.example config/.env
# Update config/.env with your DATABASE_URL and network settings
```

### 3. Backend Setup
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
# Start the scanner (sudo required for raw socket access)
sudo ./venv/bin/python backend/main.py
```

### 4. Dashboard Setup
```bash
cd dashboard
npm install
npx prisma db push  # Synchronize schema to PostgreSQL
npm run dev
```
Visit: [http://localhost:3000](http://localhost:3000)

---

## 🛡️ Administrative Actions

| Action | Description |
| :--- | :--- |
| **Allow** | Grants full network access and marks as trusted. |
| **Quarantine** | Restricts device communication (Default for new nodes). |
| **Block** | Explicitly denies all network access. |
| **Forget** | Deletes the device record from the DB for fresh re-discovery. |

---

## 👥 Team

- **Mantra Patel** - Full-Stack Architecture & Security Lead
- **Yashvi Thakkar** - Documentation & Alert Systems
- **Tirth Patel** - Python Engine & Data Engineering
- **Dhruv Patel** - Network Analysis & Testing

---

## ⚖️ License & Ethics

This project is for **education and authorized security research only**. Ensure you have explicit permission to scan and monitor any network where Sentinel-NAC is deployed.
