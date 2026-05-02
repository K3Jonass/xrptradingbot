"""Logging utilities for persistent local logs."""

import logging
from logging.handlers import RotatingFileHandler

from .config import LOG_DIR, LOG_FILE


def setup_logger() -> logging.Logger:
    """Create and return a configured logger shared across the project."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("xrp_bot")
    logger.setLevel(logging.INFO)

    if logger.handlers:
        return logger

    file_handler = RotatingFileHandler(LOG_FILE, maxBytes=1_000_000, backupCount=3)
    console_handler = logging.StreamHandler()

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
