"""
Sentinel-NAC: Report Generator Unit Tests
Tests that generate() produces a valid PDF using date-filtered data.
"""
import unittest
from unittest.mock import patch, MagicMock
import sys
import os
import tempfile
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from reports.report_generator import ReportGenerator


class TestReportGenerator(unittest.TestCase):
    """Test the PDF report generation pipeline."""

    def setUp(self):
        """Create a temporary directory for report output."""
        self.test_dir = tempfile.mkdtemp(
            dir=str(Path(__file__).resolve().parent.parent)
        )

    def tearDown(self):
        """Clean up test output files."""
        import shutil
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    @patch('reports.report_generator.db')
    def test_generate_produces_pdf_file(self, mock_db):
        """generate() should create a .pdf file in the output directory."""
        mock_db.get_devices_in_range.return_value = [
            {
                "mac_address": "AA:BB:CC:11:22:33",
                "ip_address": "192.168.1.10",
                "vendor": "Lab Test Device",
                "status": "QUARANTINED",
            },
            {
                "mac_address": "AA:BB:CC:44:55:66",
                "ip_address": "192.168.1.20",
                "vendor": "Apple Inc.",
                "status": "ALLOWED",
            },
        ]

        gen = ReportGenerator(output_dir=self.test_dir)
        path = gen.generate("2026-01-01", "2026-12-31")

        self.assertTrue(os.path.exists(path))
        self.assertTrue(path.endswith(".pdf"))
        # File should not be empty
        self.assertGreater(os.path.getsize(path), 0)

    @patch('reports.report_generator.db')
    def test_generate_calls_date_filtered_query(self, mock_db):
        """generate() should call get_devices_in_range with the correct dates."""
        mock_db.get_devices_in_range.return_value = []

        gen = ReportGenerator(output_dir=self.test_dir)
        gen.generate("2026-04-01", "2026-04-30")

        mock_db.get_devices_in_range.assert_called_once_with("2026-04-01", "2026-04-30")

    @patch('reports.report_generator.db')
    def test_generate_handles_empty_device_list(self, mock_db):
        """Report should be generated even if no devices are found."""
        mock_db.get_devices_in_range.return_value = []

        gen = ReportGenerator(output_dir=self.test_dir)
        path = gen.generate("2026-01-01", "2026-01-31")

        self.assertTrue(os.path.exists(path))
        self.assertGreater(os.path.getsize(path), 0)

    @patch('reports.report_generator.db')
    def test_generate_handles_null_vendor(self, mock_db):
        """Report should handle None vendor gracefully."""
        mock_db.get_devices_in_range.return_value = [
            {
                "mac_address": "FF:FF:FF:00:00:01",
                "ip_address": "10.0.0.1",
                "vendor": None,
                "status": "UNKNOWN",
            }
        ]

        gen = ReportGenerator(output_dir=self.test_dir)
        # Should not raise
        path = gen.generate("2026-01-01", "2026-12-31")
        self.assertTrue(os.path.exists(path))


if __name__ == "__main__":
    unittest.main()
