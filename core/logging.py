"""
Lightweight logging setup for the application.

Call `configure_logging()` once at startup (CLI and web) to ensure consistent formatting.
Use `get_logger(__name__)` in modules instead of bare print/echo for structured errors.
"""

import logging
import os
from typing import Optional


def configure_logging(level: Optional[int] = None) -> None:
    """
    Configure a simple console logger if not already configured.
    Log level can be set via LOG_LEVEL env var (DEBUG/INFO/WARNING/ERROR).
    """
    root = logging.getLogger()
    if root.handlers:
        return

    level_name = os.getenv("LOG_LEVEL", None)
    if level_name:
        level = getattr(logging, level_name.upper(), logging.INFO)
    if level is None:
        level = logging.INFO

    logging.basicConfig(
        level=level,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Convenience helper to fetch a named logger.
    """
    return logging.getLogger(name if name else __name__)
