"""
Sentinel-NAC: Centralized Logger Setup
File: backend/logs/logger.py
Purpose: Configure application-wide logging to both console and file.
         All modules should call get_logger(__name__) to get a logger.
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler

# ---------------------------------------------------------------------------
# Attempt to load settings; fall back to safe defaults if not yet configured
# ---------------------------------------------------------------------------
try:
    import sys
    _project_root = Path(__file__).resolve().parent.parent
    if str(_project_root) not in sys.path:
        sys.path.insert(0, str(_project_root))
    from config.settings import LOG_LEVEL, LOG_FILE
except Exception:
    LOG_LEVEL = "INFO"
    LOG_FILE  = "logs/sentinel_nac.log"

_LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
_initialized = False


def _ensure_log_dir(log_file: str) -> None:
    """Create parent directory for log file if it does not exist."""
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)


def setup_logging(
    level: str = LOG_LEVEL,
    log_file: str = LOG_FILE,
) -> None:
    """
    Call once at application startup to configure the root logger.
    Subsequent calls to get_logger() will inherit this configuration.
    """
    global _initialized
    if _initialized:
        return

    _ensure_log_dir(log_file)

    numeric_level = getattr(logging, level.upper(), logging.INFO)

    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    formatter = logging.Formatter(fmt=_LOG_FORMAT, datefmt=_DATE_FORMAT)

    # --- Console handler ---
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # --- Rotating file handler (10 MB per file, keep 5 backups) ---
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(numeric_level)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    _initialized = True
    root_logger.info(
        "Logging initialized — level=%s  file=%s", level.upper(), log_file
    )


def get_logger(name: str) -> logging.Logger:
    """
    Return a named logger. Call setup_logging() first in main entry point.

    Usage:
        from logs.logger import get_logger
        logger = get_logger(__name__)
        logger.info("Hello, Sentinel-NAC")
    """
    return logging.getLogger(name)
