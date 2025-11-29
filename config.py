import os

from urllib.parse import urlparse


def _validate_database_url(url: str) -> str:
    if not url:
        raise ValueError("DATABASE_URL is required")
    parsed = urlparse(url)
    if parsed.scheme not in {"sqlite", "postgres", "postgresql"}:
        raise ValueError(f"Unsupported DATABASE_URL scheme: {parsed.scheme}")
    return url


# Database URL
# Defaults to local SQLite for out-of-the-box use. Set DATABASE_URL to your Postgres
# instance (e.g., in CI/prod) for parity.
DATABASE_URL = _validate_database_url(os.getenv("DATABASE_URL", "sqlite:///./bugtracker.db"))

# API_URL = os.getenv("API_URL")  future set > CLI can call the API by HTTP
