import os

# Database URL
# Defaults to local SQLite for out-of-the-box use. Set DATABASE_URL to your Postgres
# instance (e.g., in CI/prod) for parity.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./bugtracker.db")

# API_URL = os.getenv("API_URL")  future set > CLI can call the API by HTTP
