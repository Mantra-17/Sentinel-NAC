"""
Sentinel-NAC: Configuration Loader
File: backend/config/settings.py
Purpose: Load environment variables from .env file and expose
         typed configuration constants throughout the application.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Load .env file from the config directory (two levels up from this file)
# ---------------------------------------------------------------------------
_BASE_DIR = Path(__file__).resolve().parent.parent.parent  # project root
_ENV_FILE = _BASE_DIR / "config" / ".env"

if _ENV_FILE.exists():
    load_dotenv(dotenv_path=_ENV_FILE)
else:
    # Fall back to system environment variables for CI/CD or Docker
    load_dotenv()


# ---------------------------------------------------------------------------
# Database settings
# ---------------------------------------------------------------------------
DB_HOST      = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT      = int(os.getenv("DB_PORT", "5432"))
DB_NAME      = os.getenv("DB_NAME", "sentinel_nac")
DB_USER      = os.getenv("DB_USER", "postgres")
DB_PASSWORD  = os.getenv("DB_PASSWORD", "")
DB_URL       = os.getenv("DATABASE_URL", None)


# ---------------------------------------------------------------------------
# Network scanner settings
# ---------------------------------------------------------------------------
SCAN_INTERFACE = os.getenv("SCAN_INTERFACE", "wlan0")
SCAN_TARGET    = os.getenv("SCAN_TARGET", "192.168.1.0/24")
SCAN_INTERVAL  = int(os.getenv("SCAN_INTERVAL", "10"))


# ---------------------------------------------------------------------------
# Policy engine settings
# ---------------------------------------------------------------------------
DEFAULT_NEW_DEVICE_STATUS = os.getenv(
    "DEFAULT_NEW_DEVICE_STATUS", "QUARANTINED"
).upper()

VALID_STATUSES = {"UNKNOWN", "ALLOWED", "BLOCKED", "QUARANTINED"}


# ---------------------------------------------------------------------------
# Enforcement settings
# ---------------------------------------------------------------------------
ENFORCEMENT_MODE = os.getenv("ENFORCEMENT_MODE", "simulation").lower()
# Valid values: simulation | firewall | denylist | portal

# Admin name displayed on the captive portal page (avoid hardcoding real names)
SYSTEM_ADMIN_NAME = os.getenv("SYSTEM_ADMIN_NAME", "System Administrator")


# ---------------------------------------------------------------------------
# Email / Alert settings
# ---------------------------------------------------------------------------
ALERT_EMAIL_ENABLED = os.getenv("ALERT_EMAIL_ENABLED", "false").lower() == "true"
SMTP_HOST           = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT           = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER           = os.getenv("SMTP_USER", "")
SMTP_PASSWORD       = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM           = os.getenv("SMTP_FROM", "sentinel-nac@lab.local")
ALERT_RECIPIENT     = os.getenv("ALERT_RECIPIENT", "admin@lab.local")


# ---------------------------------------------------------------------------
# Logging settings
# ---------------------------------------------------------------------------
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_FILE  = os.getenv("LOG_FILE", "logs/sentinel_nac.log")


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------
REPORT_OUTPUT_DIR = os.getenv("REPORT_OUTPUT_DIR", "reports/output")


# ---------------------------------------------------------------------------
# Derived helpers
# ---------------------------------------------------------------------------
def is_restricted_status(status: str) -> bool:
    """Return True if a device should be subject to enforcement."""
    return status in {"BLOCKED", "QUARANTINED"}
