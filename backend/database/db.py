"""
Sentinel-NAC: Database Connection Manager (PostgreSQL)
File: backend/database/db.py
Purpose: Provides a thread-safe PostgreSQL connection pool and helper
         functions used by all other backend modules.

NOTE: This project is for authorized, educational lab use only.
"""

import logging
import psycopg2
from psycopg2 import pool, extras, Error as PostgresError
from contextlib import contextmanager
from typing import Optional, List, Dict, Any

# Import project-level settings
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config.settings import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD, DB_URL

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Connection Pool (created once at module import time)
# ---------------------------------------------------------------------------
_POOL_SIZE = 5
_pool: Optional[pool.ThreadedConnectionPool] = None


def _get_pool() -> pool.ThreadedConnectionPool:
    """Lazily create and return the global connection pool."""
    global _pool
    if _pool is None:
        try:
            if DB_URL:
                _pool = pool.ThreadedConnectionPool(
                    minconn=1,
                    maxconn=_POOL_SIZE,
                    dsn=DB_URL
                )
                logger.info("Database connection pool created using DATABASE_URL.")
            else:
                _pool = pool.ThreadedConnectionPool(
                    minconn=1,
                    maxconn=_POOL_SIZE,
                    host=DB_HOST,
                    port=DB_PORT,
                    database=DB_NAME,
                    user=DB_USER,
                    password=DB_PASSWORD
                )
                logger.info("Database connection pool created (size=%d).", _POOL_SIZE)
        except PostgresError as e:
            logger.error("Failed to create connection pool: %s", e)
            raise
    return _pool


@contextmanager
def get_connection():
    """
    Context manager that yields a PostgreSQL connection from the pool.
    Automatically commits on success and rolls back on exception.
    """
    conn = None
    try:
        conn = _get_pool().getconn()
        yield conn
        conn.commit()
    except PostgresError as exc:
        if conn:
            conn.rollback()
        logger.error("Database error: %s", exc)
        raise
    finally:
        if conn:
            _get_pool().putconn(conn)


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
    """
    with get_connection() as conn:
        with conn.cursor(cursor_factory=extras.RealDictCursor) as cursor:
            try:
                cursor.execute(sql, params or ())
                if fetch_one:
                    return cursor.fetchone()
                if fetch:
                    return cursor.fetchall()
                
                # For INSERT/UPDATE/DELETE, return the row count or last inserted ID if applicable
                if cursor.description is not None:
                    return cursor.fetchone()
                return cursor.rowcount
            except Exception as e:
                logger.error("Query execution error: %s\nSQL: %s", e, sql)
                raise


def execute_many(sql: str, params_list: List[tuple]) -> int:
    """Execute a SQL statement for each item in params_list (bulk insert)."""
    with get_connection() as conn:
        with conn.cursor() as cursor:
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
    Insert a new device or update fields for an existing one using PostgreSQL ON CONFLICT.
    """
    from config.settings import DEFAULT_NEW_DEVICE_STATUS
    final_status = status or DEFAULT_NEW_DEVICE_STATUS

    sql = """
        INSERT INTO devices (
            mac_address, ip_address, hostname, vendor, probable_os,
            probable_device_type, fingerprint_confidence, status, last_seen
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
        ON CONFLICT (mac_address) DO UPDATE SET
            ip_address             = EXCLUDED.ip_address,
            hostname               = COALESCE(EXCLUDED.hostname, devices.hostname),
            vendor                 = COALESCE(EXCLUDED.vendor, devices.vendor),
            probable_os            = COALESCE(EXCLUDED.probable_os, devices.probable_os),
            probable_device_type   = COALESCE(EXCLUDED.probable_device_type, devices.probable_device_type),
            fingerprint_confidence = GREATEST(EXCLUDED.fingerprint_confidence, devices.fingerprint_confidence),
            last_seen              = CURRENT_TIMESTAMP
        RETURNING *
    """
    return execute_query(sql, (
        mac, ip, hostname, vendor, probable_os,
        probable_device_type, fingerprint_confidence, final_status
    ), fetch_one=True)


def update_device_status(mac: str, new_status: str, actor: str = "system") -> bool:
    """
    Update a device's status and write an audit event.
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
             new_status, actor, details, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
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
            (mac_address, alert_type, recipient, subject, body, status, created_at)
        VALUES (%s, %s, %s, %s, %s, 'PENDING', CURRENT_TIMESTAMP)
        RETURNING id
    """
    result = execute_query(sql, (mac_address, alert_type, recipient, subject, body), fetch_one=True)
    return result['id'] if result else None


def mark_alert_sent(alert_id: int) -> None:
    sql = "UPDATE alerts SET status='SENT', sent_at=CURRENT_TIMESTAMP WHERE id=%s"
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
