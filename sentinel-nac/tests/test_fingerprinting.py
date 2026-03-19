"""
Sentinel-NAC: Fingerprinting Tests
File: tests/test_fingerprinting.py
Purpose: Unit tests for OUI vendor lookup and TTL OS inference.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from fingerprinting.fingerprint import lookup_vendor, infer_os_from_ttl, fingerprint_device


def test_vendor_lookup_known_oui():
    """Known OUI prefix should return a vendor name."""
    vendor = lookup_vendor("B8:27:EB:11:22:33")
    assert vendor is not None
    assert "Raspberry" in vendor


def test_vendor_lookup_unknown_oui():
    """Unknown OUI prefix should return None."""
    vendor = lookup_vendor("12:34:56:78:90:AB")
    assert vendor is None


def test_vendor_lookup_vmware():
    vendor = lookup_vendor("00:50:56:AA:BB:CC")
    assert vendor == "VMware"


def test_ttl_linux_range():
    """TTL=64 should be inferred as Linux/macOS/Android."""
    os_name, dev_type, confidence = infer_os_from_ttl(64)
    assert os_name is not None
    assert "Linux" in os_name or "macOS" in os_name
    assert confidence > 0


def test_ttl_windows_range():
    """TTL=128 should be inferred as Windows."""
    os_name, dev_type, confidence = infer_os_from_ttl(128)
    assert os_name == "Windows"
    assert confidence > 0


def test_ttl_unknown():
    """TTL=1 should not match any known OS."""
    os_name, dev_type, confidence = infer_os_from_ttl(1)
    assert os_name is None
    assert confidence == 0


def test_fingerprint_device_returns_dict():
    """fingerprint_device should always return a dict with expected keys."""
    result = fingerprint_device(
        mac="B8:27:EB:11:22:33",
        ip="192.168.1.5",
        run_ping=False,  # skip real network probe in test
    )
    assert isinstance(result, dict)
    assert "vendor" in result
    assert "probable_os" in result
    assert "fingerprint_confidence" in result
    # Raspberry Pi OUI → vendor should be non-null
    assert result["vendor"] is not None


def test_fingerprint_with_no_oui():
    """Fingerprinting an unknown OUI should still return a valid dict."""
    result = fingerprint_device(
        mac="12:34:56:78:90:AB",
        ip="192.168.1.99",
        run_ping=False,
    )
    assert isinstance(result, dict)
    assert result["fingerprint_confidence"] == 0  # no OUI, no ping → 0


# ---------------------------------------------------------------------------
# Standalone
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    test_vendor_lookup_known_oui()
    test_vendor_lookup_unknown_oui()
    test_vendor_lookup_vmware()
    test_ttl_linux_range()
    test_ttl_windows_range()
    test_ttl_unknown()
    test_fingerprint_device_returns_dict()
    test_fingerprint_with_no_oui()
    print("All fingerprinting tests passed ✓")
