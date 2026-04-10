"""
Sentinel-NAC: Fingerprinting Unit Tests
"""
import unittest
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from fingerprinting.fingerprint import lookup_vendor, infer_os_from_ttl

class TestFingerprinting(unittest.TestCase):
    def test_vendor_lookup(self):
        """Verify the OUI lookup works for known prefixes."""
        # Raspberry Pi OUI
        vendor = lookup_vendor("B8:27:EB:11:22:33")
        self.assertIn("Raspberry", vendor)
        
        # Apple OUI
        vendor = lookup_vendor("00:0A:95:11:22:33")
        self.assertIn("Apple", vendor)

    def test_os_inference(self):
        """Verify OS inference based on TTL."""
        os_name, dev_type, conf = infer_os_from_ttl(64)
        self.assertIn("Linux", os_name)
        
        os_name, dev_type, conf = infer_os_from_ttl(128)
        self.assertEqual(os_name, "Windows")

if __name__ == "__main__":
    unittest.main()
