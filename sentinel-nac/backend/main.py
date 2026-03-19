"""
Sentinel-NAC: Main Entry Point
File: backend/main.py
Purpose: Bootstrap and run the Sentinel-NAC daemon.

WARNING: This software must only be used on networks/devices you own
         or have explicit written authorization to monitor.
         Unauthorized use is illegal and unethical.

Usage:
    # Real network mode (requires root/sudo + interface + .env configured)
    sudo python3 main.py

    # Simulation mode (safe for demo without root)
    python3 main.py --simulate

    # Dry run (no enforcement, just log)
    python3 main.py --simulate --no-enforce
"""

import argparse
import signal
import sys
import time
from pathlib import Path

# Ensure project root is in the path
_BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_BACKEND_DIR))

from logs.logger import setup_logging, get_logger
from config.settings import LOG_LEVEL, LOG_FILE, DEFAULT_NEW_DEVICE_STATUS, ENFORCEMENT_MODE
from scanner.arp_scanner import ARPScanner
from fingerprinting.fingerprint import fingerprint_device
from policy.decision_engine import DecisionEngine
from enforcement.quarantine import QuarantineController
from alerts.email_alert import AlertService

# ---------------------------------------------------------------------------
# Initialize logging FIRST (before any other imports write log messages)
# ---------------------------------------------------------------------------
setup_logging(level=LOG_LEVEL, log_file=LOG_FILE)
logger = get_logger("sentinel_nac")


# ---------------------------------------------------------------------------
# Global objects
# ---------------------------------------------------------------------------
_scanner    : ARPScanner           = None
_policy     : DecisionEngine       = None
_quarantine : QuarantineController = None
_alerts     : AlertService         = None
_running    = True


# ---------------------------------------------------------------------------
# Graceful shutdown
# ---------------------------------------------------------------------------

def _shutdown(signum, frame):
    global _running
    logger.info("Shutdown signal received (signal %d). Stopping Sentinel-NAC...", signum)
    _running = False
    if _scanner:
        _scanner.stop()
    logger.info("Sentinel-NAC stopped cleanly.")
    sys.exit(0)


# ---------------------------------------------------------------------------
# Device event handler (called by ARPScanner)
# ---------------------------------------------------------------------------

def on_device_discovered(mac: str, ip: str, source: str) -> None:
    """
    Main pipeline callback triggered for every new/changed device:
      1. Fingerprint the device
      2. Run policy evaluation
      3. Apply enforcement if needed
      4. Send alerts if triggered
    """
    logger.info(">> Device detected: MAC=%s  IP=%s  source=%s", mac, ip, source)

    try:
        # Step 1: Fingerprint
        fp = fingerprint_device(mac, ip, run_ping=not args.no_ping)

        # Step 2: Policy decision
        decision = _policy.evaluate(mac=mac, ip=ip, fingerprint=fp)

        device     = decision["device"]
        action     = decision["action"]
        is_new     = decision["is_new_device"]
        send_alert = decision["trigger_alert"]

        logger.info(
            "Policy decision for %s: action=%s  is_new=%s  alert=%s",
            mac, action, is_new, send_alert,
        )

        # Step 3: Enforcement
        if not args.no_enforce:
            _quarantine.handle_device_decision(decision)

        # Step 4: Alerts
        if send_alert:
            if is_new:
                _alerts.alert_new_unknown_device(device)
            elif device["status"] == "BLOCKED":
                _alerts.alert_blocked_reconnect(device)

    except Exception as exc:
        logger.error("Error processing device %s: %s", mac, exc, exc_info=True)


# ---------------------------------------------------------------------------
# Parse arguments (module-level so on_device_discovered can read them)
# ---------------------------------------------------------------------------
_parser = argparse.ArgumentParser(
    description="Sentinel-NAC: Zero-Trust Network Access Control Daemon"
)
_parser.add_argument(
    "--simulate",
    action="store_true",
    help="Run in simulation mode (no real packet capture, safe for demo)",
)
_parser.add_argument(
    "--no-enforce",
    action="store_true",
    help="Disable enforcement (log decisions only, no quarantine changes)",
)
_parser.add_argument(
    "--no-ping",
    action="store_true",
    help="Skip active ping during fingerprinting",
)
args, _unknown = _parser.parse_known_args()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    global _scanner, _policy, _quarantine, _alerts

    # Safety banner
    logger.info("=" * 60)
    logger.info("  Sentinel-NAC: Zero-Trust Network Access Control")
    logger.info("  AUTHORIZED LAB USE ONLY — see docs/ethics_statement.md")
    logger.info("=" * 60)
    logger.info("Mode:         %s", "SIMULATION" if args.simulate else "LIVE")
    logger.info("Enforcement:  %s", "DISABLED" if args.no_enforce else ENFORCEMENT_MODE.upper())
    logger.info("Default status for new devices: %s", DEFAULT_NEW_DEVICE_STATUS)

    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT,  _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    # Initialize components
    _policy     = DecisionEngine()
    _quarantine = QuarantineController()
    _alerts     = AlertService()

    # Initialize and start scanner
    _scanner = ARPScanner(
        on_device=on_device_discovered,
        simulate=args.simulate,
    )
    _scanner.start()

    logger.info("Sentinel-NAC is running. Press Ctrl+C to stop.")

    # Keep main thread alive
    while _running:
        time.sleep(1)


if __name__ == "__main__":
    main()
