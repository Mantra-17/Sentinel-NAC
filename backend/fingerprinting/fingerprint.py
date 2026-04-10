"""
Sentinel-NAC: Device Fingerprinting Module
File: backend/fingerprinting/fingerprint.py
Purpose: Infer probable OS, device type, and vendor from passive metadata.

Methods used (all passive / safe):
  1. OUI vendor lookup from MAC prefix (local oui.txt if present, else offline table)
  2. TTL-based OS inference from ping response (optional active probe)
  3. DHCP hostname from packet if captured by scanner (passed in as argument)

These are heuristic estimates only — not guaranteed to be accurate.
"""

import logging
import re
import socket
import subprocess
from typing import Optional, Tuple, Dict

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Mini OUI table (first 24 bits of MAC → vendor name)
# A real implementation should use the full IEEE OUI database (~30k entries).
# Students can download it from: https://maclookup.app/downloads/json-database
# ---------------------------------------------------------------------------
_OUI_TABLE: Dict[str, str] = {
    "00:50:56": "VMware",
    "00:0C:29": "VMware",
    "08:00:27": "VirtualBox / Oracle",
    "B8:27:EB": "Raspberry Pi Foundation",
    "DC:A6:32": "Raspberry Pi Foundation",
    "3C:22:FB": "Apple Inc.",
    "F4:5C:89": "Apple Inc.",
    "78:4F:43": "Apple Inc.",
    "A4:C3:F0": "Google / Nest",
    "00:1A:2B": "Cisco Systems",
    "00:1B:63": "Apple Inc.",
    "00:1D:7E": "Cisco-Linksys",
    "00:23:EB": "Cisco Systems",
    "00:50:BA": "D-Link",
    "1C:1B:0D": "Micro-Star International",
    "2C:F0:5D": "Intel Corporate",
    "44:85:00": "Aruba Networks",
    "60:57:18": "Intel Corporate",
    "88:78:73": "Samsung Electronics",
    "B4:6D:83": "Samsung Electronics",
    "E8:2A:EA": "Motorola Mobility",
    "FC:F8:AE": "Samsung Electronics",
    "00:17:C8": "TP-LINK Technologies",
    "F0:D7:AA": "TP-Link Technologies",
    "00:0A:95": "Apple Inc.",
    "AA:BB:CC": "Lab Test Device",   # seed data MACs
}


def lookup_vendor(mac: str) -> Optional[str]:
    """
    Look up the hardware vendor for a MAC address using the OUI prefix.

    Args:
        mac: MAC address in colon-separated format (e.g. "00:50:56:AB:CD:EF")

    Returns:
        Vendor name string or None if not found.
    """
    prefix = mac.upper()[:8]
    vendor = _OUI_TABLE.get(prefix)
    if vendor:
        logger.debug("OUI match: %s → %s", prefix, vendor)
    else:
        logger.debug("OUI not found for prefix: %s", prefix)
    return vendor


# ---------------------------------------------------------------------------
# TTL-based OS inference
# ---------------------------------------------------------------------------
# Common defaults: Linux ≈ 64, Windows ≈ 128, macOS ≈ 64, Cisco ≈ 255
# These are starting TTL values that decrease by 1 per hop.
# ---------------------------------------------------------------------------
_TTL_OS_MAP = [
    (range(60, 66),  "Linux / macOS / Android",  "Laptop/Desktop or Mobile"),
    (range(125, 132), "Windows",                 "Laptop/Desktop"),
    (range(250, 256), "Network Device (Cisco/HP)", "Router/Switch"),
]


def infer_os_from_ttl(ttl: int) -> Tuple[Optional[str], Optional[str], int]:
    """
    Infer probable OS and device type from a TTL value.

    Args:
        ttl: Time-To-Live value from IP header

    Returns:
        Tuple of (probable_os, probable_device_type, confidence_score 0-100)
    """
    for ttl_range, os_name, device_type in _TTL_OS_MAP:
        if ttl in ttl_range:
            confidence = 60  # TTL-only inference is moderate confidence
            logger.debug(
                "TTL=%d → OS=%s  type=%s  confidence=%d",
                ttl, os_name, device_type, confidence,
            )
            return os_name, device_type, confidence

    logger.debug("TTL=%d did not match any known OS fingerprint.", ttl)
    return None, None, 0


def get_ttl_via_ping(ip: str, timeout: int = 1) -> Optional[int]:
    """
    Attempt a single ICMP ping to retrieve the TTL from the response.
    This is an active probe — use only when the device is on your own network.

    Returns:
        TTL integer or None if unreachable / OS does not support ping.
    """
    try:
        # Works on Linux/macOS; -c1 = 1 packet, -W = wait timeout
        result = subprocess.run(
            ["ping", "-c", "1", "-W", str(timeout), ip],
            capture_output=True, text=True, timeout=timeout + 2,
        )
        output = result.stdout
        # Parse TTL from ping output line: "ttl=64" or "TTL=128"
        match = re.search(r"ttl=(\d+)", output, re.IGNORECASE)
        if match:
            ttl = int(match.group(1))
            logger.debug("Ping to %s returned TTL=%d", ip, ttl)
            return ttl
    except Exception as exc:
        logger.debug("Ping to %s failed: %s", ip, exc)
    return None


def get_hostname(ip: str) -> Optional[str]:
    """
    Attempt a reverse DNS lookup to get a hostname for the IP.
    Operates in your local subnet only, so is generally safe.

    Returns:
        Hostname string or None if lookup fails.
    """
    try:
        hostname, _, _ = socket.gethostbyaddr(ip)
        logger.debug("Reverse DNS: %s → %s", ip, hostname)
        return hostname
    except socket.herror:
        return None


# ---------------------------------------------------------------------------
# Main fingerprinting entry point
# ---------------------------------------------------------------------------

def fingerprint_device(
    mac: str,
    ip: str,
    dhcp_hostname: Optional[str] = None,
    run_ping: bool = True,
) -> Dict:
    """
    Run all available fingerprinting heuristics and return a dict of results.

    Args:
        mac:           Device MAC address
        ip:            Device IP address
        dhcp_hostname: Hostname from DHCP if captured earlier
        run_ping:      Whether to attempt an active ping for TTL (default True)

    Returns:
        Dict with keys: mac, ip, hostname, vendor, probable_os,
                        probable_device_type, fingerprint_confidence
    """
    result = {
        "mac":                    mac,
        "ip":                     ip,
        "hostname":               dhcp_hostname,
        "vendor":                 None,
        "probable_os":            None,
        "probable_device_type":   None,
        "fingerprint_confidence": 0,
    }

    confidence_parts = []

    # Step 1: Vendor from OUI
    vendor = lookup_vendor(mac)
    if vendor:
        result["vendor"] = vendor
        confidence_parts.append(20)

        # Refine device type from vendor name
        vendor_lower = vendor.lower()
        if "apple" in vendor_lower:
            result["probable_os"] = "macOS / iOS"
            result["probable_device_type"] = "Apple Device"
            confidence_parts.append(30)
        elif "samsung" in vendor_lower or "motorola" in vendor_lower:
            result["probable_device_type"] = "Mobile/Tablet"
            confidence_parts.append(20)
        elif "cisco" in vendor_lower or "aruba" in vendor_lower or "tp-link" in vendor_lower:
            result["probable_device_type"] = "Network Device"
            confidence_parts.append(25)
        elif "raspberry" in vendor_lower:
            result["probable_os"] = "Linux (Raspberry Pi)"
            result["probable_device_type"] = "IoT Device"
            confidence_parts.append(35)
        elif "vmware" in vendor_lower or "virtualbox" in vendor_lower:
            result["probable_os"] = "Virtual Machine"
            result["probable_device_type"] = "Virtual Machine"
            confidence_parts.append(40)

    # Step 2: Hostname via reverse DNS (if not from DHCP)
    if not result["hostname"]:
        hostname = get_hostname(ip)
        if hostname:
            result["hostname"] = hostname
            confidence_parts.append(15)

    # Step 3: TTL-based OS inference
    if run_ping:
        ttl = get_ttl_via_ping(ip)
        if ttl:
            os_name, device_type, ttl_conf = infer_os_from_ttl(ttl)
            if os_name and not result["probable_os"]:
                result["probable_os"] = os_name
            if device_type and not result["probable_device_type"]:
                result["probable_device_type"] = device_type
            if ttl_conf:
                confidence_parts.append(ttl_conf)

    # Compute overall confidence (capped at 100)
    result["fingerprint_confidence"] = min(sum(confidence_parts), 100)

    logger.info(
        "Fingerprint result for %s: vendor=%s  os=%s  type=%s  confidence=%d",
        mac, result["vendor"], result["probable_os"],
        result["probable_device_type"], result["fingerprint_confidence"],
    )
    return result
