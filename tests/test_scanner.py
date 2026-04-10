"""
Sentinel-NAC: Scanner Unit Tests
"""
import sys
import unittest
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from scanner.arp_scanner import ARPScanner

class TestScanner(unittest.TestCase):
    def test_simulation_init(self):
        """Verify scanner can initialize in simulation mode."""
        scanner = ARPScanner(interface="simulate", simulate=True)
        self.assertTrue(scanner.simulate)
        self.assertEqual(scanner.interface, "simulate")

    def test_dedup_logic(self):
        """Verify the deduplication cache works."""
        captured = []
        def callback(mac, ip, source):
            captured.append(mac)
            
        scanner = ARPScanner(on_device=callback, simulate=True)
        
        # Notify same device twice
        scanner._notify("AA:BB:CC:11:22:33", "192.168.1.10", "test")
        scanner._notify("AA:BB:CC:11:22:33", "192.168.1.10", "test")
        
        self.assertEqual(len(captured), 1)
        self.assertEqual(captured[0], "AA:BB:CC:11:22:33")

if __name__ == "__main__":
    unittest.main()
