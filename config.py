import os

# Database URL
# Default to Postgres for parity; override DATABASE_URL if needed.
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/bugtracker")

# API_URL = os.getenv("API_URL")  future set > CLI can call the API by HTTP
