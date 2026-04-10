"""
Sentinel-NAC: Centralized Logger
File: backend/logs/logger.py
"""
import os
import logging
from logging.handlers import RotatingFileHandler

def setup_logging(level="INFO", log_file="logs/sentinel_nac.log"):
    """Configure logging for the application."""
    # Ensure logs directory exists
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Root logger
    logger = logging.getLogger()
    logger.setLevel(level)

    # Clear existing handlers
    if logger.hasHandlers():
        logger.handlers.clear()

    # Formatter
    formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)-8s %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console Handler
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # File Handler
    try:
        fh = RotatingFileHandler(log_file, maxBytes=1048576, backupCount=5)
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    except Exception as e:
        print(f"Failed to setup file logging: {e}")

def get_logger(name):
    """Utility to get a logger by name."""
    return logging.getLogger(name)
