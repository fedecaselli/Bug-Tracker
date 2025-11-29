"""
CLI configuration helpers.

Centralizes API settings loaded from environment variables with sensible defaults.
"""

import os
from urllib.parse import urlparse


def _validate_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError(f"Invalid API_URL: {url}")
    return url.rstrip("/")


# Defaults to local development; override via env for deployed API.
API_URL = _validate_url(os.getenv("API_URL", "http://localhost:8000"))

# Optional bearer token for authenticated deployments.
API_TOKEN = os.getenv("API_TOKEN")
