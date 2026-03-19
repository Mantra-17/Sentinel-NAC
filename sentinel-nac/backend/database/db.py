"""
Sentinel-NAC: Database Connection Manager
File: backend/database/db.py
Purpose: Provides a thread-safe MySQL connection pool and helper
         functions used by all other backend modules.

NOTE: This project is for authorized, educational lab use only.
"""

import logging
import mysql.connector
from mysql.connector import pooling, Error as MySQLError
from contextlib import contextmanager
from typing import Optional, List, Dict, Any

# Import project-level settings
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config.settings import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Connection Pool (created once at module import time)
# ---------------------------------------------------------------------------
_POOL_SIZE = 5
_pool: Optional[pooling.MySQLConnectionPool] = None


def _get_pool() -> pooling.MySQLConnectionPool:
    """Lazily create and return the global connection pool."""
    global _pool
    if _pool is None:
        _pool = pooling.MySQLConnectionPool(
            pool_name="sentinel_pool",
            pool_size=_POOL_SIZE,
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            autocommit=False,
            charset="utf8mb4",
            collation="utf8mb4_unicode_ci",
        )
        logger.info("Database connection pool created (size=%d).", _POOL_SIZE)
    return _pool


@contextmanager
def get_connection():
    """
    Context manager that yields a MySQL connection from the pool.
    Automatically commits on success and rolls back on exception.

    Usage:
        with get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT ...")
    """
    conn = None
    try:
        conn = _get_pool().get_connection()
        yield conn
        conn.commit()
    except MySQLError as exc:
        if conn:
            conn.rollback()
        logger.error("Database error: %s", exc)
        raise
    finally:
        if conn and conn.is_connected():
            conn.close()


# ---------------------------------------------------------------------------
# Generic query helpers
# ---------------------------------------------------------------------------

def execute_query(
    sql: str,
    params: Optional[tuple] = None,
    fetch: bool = False,
    fetch_one: bool = False,
) -> Any:
    """
    Execute a SQL statement.

    Args:
        sql:       SQL string with %s placeholders.
        params:    Tuple of parameter values.
        fetch:     If True, return all rows as a list of dicts.
        fetch_one: If True, return the first row as a dict (overrides fetch).

    Returns:
        List[dict] | dict | None | int (lastrowid for INSERT)
    """
    with get_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(sql, params or ())
            if fetch_one:
                return cursor.fetchone()
            if fetch:
                return cursor.fetchall()
            return cursor.lastrowid
        finally:
            cursor.close()


def execute_many(sql: str, params_list: List[tuple]) -> int:
    """Execute a SQL statement for each item in params_list (bulk insert)."""
    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.executemany(sql, params_list)
            return cursor.rowcount
        finally:
            cursor.close()


# ---------------------------------------------------------------------------
# Device-specific helpers
# ---------------------------------------------------------------------------

def get_device_by_mac(mac: str) -> Optional[Dict]:
    """Return the device row for a given MAC address, or None."""
    sql = "SELECT * FROM devices WHERE mac_address = %s LIMIT 1"
    return execute_query(sql, (mac,), fetch_one=True)


def upsert_device(
    mac: str,
    ip: str,
    hostname: Optional[str] = None,
    vendor: Optional[str] = None,
    probable_os: Optional[str] = None,
    probable_device_type: Optional[str] = None,
    fingerprint_confidence: int = 0,
    status: Optional[str] = None,
) -> Dict:
    """
    Insert a new device or update ip/last_seen/fingerprint for an existing one.

    Returns:
        The current database row for the device (after upsert).
    """
    existing = get_device_by_mac(mac)

    if existing is None:
        # New device — apply default status from policy
        from config.settings import DEFAULT_NEW_DEVICE_STATUS
        final_status = status or DEFAULT_NEW_DEVICE_STATUS
        sql = """
            INSERT INTO devices
                (mac_address, ip_address, hostname, vendor, probable_os,
                 probable_device_type, fingerprint_confidence, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        execute_query(sql, (
            mac, ip, hostname, vendor, probable_os,
            probable_device_type, fingerprint_confidence, final_status,
        ))
        logger.info("New device inserted: MAC=%s  IP=%s  Status=%s",
                    mac, ip, final_status)
    else:
        # Existing device — update mutable fields, preserve status
        sql = """
            UPDATE devices
               SET ip_address            = %s,
                   hostname              = COALESCE(%s, hostname),
                   vendor                = COALESCE(%s, vendor),
                   probable_os           = COALESCE(%s, probable_os),
                   probable_device_type  = COALESCE(%s, probable_device_type),
                   fingerprint_confidence= GREATEST(%s, fingerprint_confidence),
                   last_seen             = NOW()
             WHERE mac_address = %s
        """
        execute_query(sql, (
            ip, hostname, vendor, probable_os,
            probable_device_type, fingerprint_confidence, mac,
        ))
        logger.debug("Existing device updated: MAC=%s  IP=%s", mac, ip)

    return get_device_by_mac(mac)


def update_device_status(mac: str, new_status: str, actor: str = "system") -> bool:
    """
    Update a device's status and write an audit event.

    Returns True if the device was found and updated.
    """
    device = get_device_by_mac(mac)
    if device is None:
        logger.warning("update_device_status called for unknown MAC: %s", mac)
        return False

    old_status = device["status"]
    if old_status == new_status:
        return True  # No change needed

    execute_query(
        "UPDATE devices SET status = %s WHERE mac_address = %s",
        (new_status, mac),
    )

    log_event(
        mac_address=mac,
        ip_address=device.get("ip_address"),
        event_type="STATUS_CHANGED",
        old_status=old_status,
        new_status=new_status,
        actor=actor,
        details=f"Status changed from {old_status} to {new_status}",
    )
    logger.info("Device %s status: %s → %s (actor=%s)", mac, old_status, new_status, actor)
    return True


def get_all_devices() -> List[Dict]:
    """Return all devices ordered by last_seen descending."""
    return execute_query(
        "SELECT * FROM devices ORDER BY last_seen DESC",
        fetch=True,
    )


# ---------------------------------------------------------------------------
# Event logging helpers
# ---------------------------------------------------------------------------

def log_event(
    mac_address: str,
    event_type: str,
    ip_address: Optional[str] = None,
    old_status: Optional[str] = None,
    new_status: Optional[str] = None,
    actor: str = "system",
    details: Optional[str] = None,
) -> None:
    """Write a row to device_events for audit trail."""
    sql = """
        INSERT INTO device_events
            (mac_address, ip_address, event_type, old_status,
             new_status, actor, details)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    execute_query(sql, (
        mac_address, ip_address, event_type,
        old_status, new_status, actor, details,
    ))


def get_events_for_device(mac: str, limit: int = 50) -> List[Dict]:
    """Return recent events for a specific device."""
    sql = """
        SELECT * FROM device_events
         WHERE mac_address = %s
         ORDER BY created_at DESC
         LIMIT %s
    """
    return execute_query(sql, (mac, limit), fetch=True)


def get_recent_events(limit: int = 100) -> List[Dict]:
    """Return the most recent events across all devices."""
    sql = "SELECT * FROM device_events ORDER BY created_at DESC LIMIT %s"
    return execute_query(sql, (limit,), fetch=True)


# ---------------------------------------------------------------------------
# Alert helpers
# ---------------------------------------------------------------------------

def create_alert(
    alert_type: str,
    recipient: str,
    subject: str,
    body: str,
    mac_address: Optional[str] = None,
) -> int:
    """Insert a pending alert and return its id."""
    sql = """
        INSERT INTO alerts
            (mac_address, alert_type, recipient, subject, body, status)
        VALUES (%s, %s, %s, %s, %s, 'PENDING')
    """
    return execute_query(sql, (mac_address, alert_type, recipient, subject, body))


def mark_alert_sent(alert_id: int) -> None:
    sql = "UPDATE alerts SET status='SENT', sent_at=NOW() WHERE id=%s"
    execute_query(sql, (alert_id,))


def mark_alert_failed(alert_id: int, error_msg: str) -> None:
    sql = "UPDATE alerts SET status='FAILED', error_msg=%s WHERE id=%s"
    execute_query(sql, (error_msg[:512], alert_id))


# ---------------------------------------------------------------------------
# System settings helper
# ---------------------------------------------------------------------------

def get_setting(key: str, default: Optional[str] = None) -> Optional[str]:
    """Read a setting value from system_settings table."""
    row = execute_query(
        "SELECT setting_value FROM system_settings WHERE setting_key=%s",
        (key,), fetch_one=True,
    )
    return row["setting_value"] if row else default
