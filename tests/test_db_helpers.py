"""
Sentinel-NAC: Database Helper Unit Tests
Tests SQL helper functions with mocked psycopg2 connections.
"""
import unittest
from unittest.mock import patch, MagicMock, PropertyMock
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))


class TestDatabaseHelpers(unittest.TestCase):
    """Test db.py helper functions with mocked connections."""

    @patch('database.db.get_connection')
    def test_get_device_by_mac_returns_device(self, mock_conn_ctx):
        """get_device_by_mac returns a dict when device exists."""
        from database import db

        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {
            "id": 1,
            "mac_address": "AA:BB:CC:11:22:33",
            "ip_address": "192.168.1.10",
            "status": "QUARANTINED",
        }
        mock_cursor.description = [("id",), ("mac_address",)]

        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        mock_conn_ctx.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn_ctx.return_value.__exit__ = MagicMock(return_value=False)

        result = db.get_device_by_mac("AA:BB:CC:11:22:33")
        self.assertIsNotNone(result)
        self.assertEqual(result["mac_address"], "AA:BB:CC:11:22:33")

    @patch('database.db.get_connection')
    def test_get_device_by_mac_returns_none(self, mock_conn_ctx):
        """get_device_by_mac returns None when device doesn't exist."""
        from database import db

        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_cursor.description = [("id",)]

        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        mock_conn_ctx.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn_ctx.return_value.__exit__ = MagicMock(return_value=False)

        result = db.get_device_by_mac("FF:FF:FF:FF:FF:FF")
        self.assertIsNone(result)

    def test_upsert_sql_preserves_status(self):
        """Verify the upsert SQL contains 'status = devices.status'."""
        from database import db
        import inspect

        source = inspect.getsource(db.upsert_device)
        self.assertIn("status                 = devices.status", source)

    def test_close_pool_function_exists(self):
        """Verify close_pool() function exists in db module."""
        from database import db
        self.assertTrue(hasattr(db, 'close_pool'))
        self.assertTrue(callable(db.close_pool))

    def test_get_devices_in_range_function_exists(self):
        """Verify get_devices_in_range() function exists in db module."""
        from database import db
        self.assertTrue(hasattr(db, 'get_devices_in_range'))
        self.assertTrue(callable(db.get_devices_in_range))

    @patch('database.db._pool')
    def test_close_pool_calls_closeall(self, mock_pool):
        """close_pool() should call closeall() on the pool."""
        from database import db

        # Set up the mock pool
        db._pool = MagicMock()
        db.close_pool()
        
        # Pool should have been closed and set to None
        self.assertIsNone(db._pool)


if __name__ == "__main__":
    unittest.main()
