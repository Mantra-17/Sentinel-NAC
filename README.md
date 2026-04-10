# Sentinel-NAC: Industrial-Grade Network Access Control

> **Zero-Trust Network Enforcement** — A professional solution for active network isolation, rogue device identification, and automated quarantine.

Sentinel-NAC is a high-performance Network Access Control (NAC) system built to secure local area networks using active redirection and link-layer enforcement. Unlike simple monitoring tools, Sentinel-NAC actively **intercepts** unauthorized traffic via ARP and DNS poisoning, forcing rogue devices into a professional Isolation Portal until verified by an administrator.

---

## 🛡️ Industrial Enforcement Capabilities

- **Active Isolation (ARP Poisoning)**: Intercepts device traffic at the hardware level, convincing the target that the NAC station is the network gateway.
- **Universal Redirection (DNS Poisoning)**: Captures DNS queries from blocked devices and redirects all domain requests to the NAC Isolation Portal.
- **Zero-Trust Baseline**: Automatically quarantines 100% of new devices by default, requiring explicit "Admin Approval" for network joining.
- **Persistent Protection**: Enforcement state is synced with a PostgreSQL database; isolation remains active even across system restarts.
- **Isolation Portal**: A professional-grade notification server (Port 80) that alerts unauthorized users of their security status.

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
