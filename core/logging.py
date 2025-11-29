"""
Lightweight logging setup for the application.

Call `configure_logging()` once at startup (CLI and web) to ensure consistent formatting.
Use `get_logger(__name__)` in modules instead of bare print/echo for structured errors.
"""

import logging
from typing import Optional


def configure_logging(level: int = logging.INFO) -> None:
    """
    Configure a simple console logger if not already configured.
    """
    root = logging.getLogger()
    if root.handlers:
        return

    logging.basicConfig(
        level=level,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Convenience helper to fetch a named logger.
    """
    return logging.getLogger(name if name else __name__)
