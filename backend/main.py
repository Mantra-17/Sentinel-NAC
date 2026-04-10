"""
Sentinel-NAC: Main Backend Daemon
File: backend/main.py
Purpose: Entry point for the NAC system. Orchestrates scanner, policy,
         enforcement, and alert modules.
"""

import sys
import time
import signal
import logging
import argparse
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

# Import modules
from config.settings import LOG_LEVEL, LOG_FILE, SCAN_INTERFACE, SCAN_TARGET, ENFORCEMENT_MODE
from logs.logger import setup_logging
from scanner.arp_scanner import ARPScanner
from policy.decision_engine import DecisionEngine
from fingerprinting.fingerprint import fingerprint_device
from enforcement.quarantine import QuarantineController
from enforcement.portal import CaptivePortalServer
from alerts.email_alert import AlertService

# Setup global logger
setup_logging(level=LOG_LEVEL, log_file=LOG_FILE)
logger = logging.getLogger("sentinel_nac")

class SentinelNAC:
    def __init__(self, simulate=False, no_enforce=False):
        self.simulate = simulate
        self.no_enforce = no_enforce
        
        self.policy_engine = DecisionEngine()
        self.enforcement = QuarantineController()
        self.alerts = AlertService()
        self.portal = CaptivePortalServer(port=80) 
        
        self.scanner = ARPScanner(
            interface=SCAN_INTERFACE if not simulate else "simulate",
            target=SCAN_TARGET,
            on_device=self.on_device_discovered,
            simulate=simulate
        )
        
        self.running = True

    def on_device_discovered(self, mac: str, ip: str, source: str):
        """Callback for whenever a device is seen on the network."""
        logger.info("Processing discovery: MAC=%s IP=%s Source=%s", mac, ip, source)
        
        # 1. Fingerprint
        metadata = fingerprint_device(mac, ip, run_ping=not self.simulate)
        
        # 2. Evaluate Policy
        decision = self.policy_engine.evaluate(mac, ip, fingerprint=metadata)
        
        # 3. Enforce if required
        if not self.no_enforce:
            self.enforcement.handle_device_decision(decision)
        else:
            logger.info("Enforcement skipped (no-enforce mode)")
            
        # 4. Alert if required
        if decision["trigger_alert"]:
            alert_type = "NEW_UNKNOWN_DEVICE" if decision["is_new_device"] else "BLOCKED_RECONNECT"
            self.alerts.alert_event(alert_type, mac, ip, details=metadata)

    def run(self):
        """Start the scanner and wait for shutdown signal."""
        try:
            self.portal.start()
            self.scanner.start()
            logger.info("Sentinel-NAC Backend started and listening...")
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()
        except Exception as e:
            logger.error("Unexpected error in main loop: %s", e)
            self.stop()

    def stop(self):
        """Graceful shutdown."""
        logger.info("Shutting down Sentinel-NAC...")
        self.running = False
        self.scanner.stop()
        self.portal.stop()
        self.alerts.stop()
        logger.info("Shutdown complete.")

def main():
    parser = argparse.ArgumentParser(description="Sentinel-NAC Backend Daemon")
    parser.add_argument("--simulate", action="store_true", help="Run in simulation mode (no root required)")
    parser.add_argument("--no-enforce", action="store_true", help="Disable network enforcement (log/alert only)")
    args = parser.parse_args()

    nac = SentinelNAC(simulate=args.simulate, no_enforce=args.no_enforce)
    
    # Register signal handlers
    def signal_handler(sig, frame):
        nac.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    nac.run()

if __name__ == "__main__":
    main()
