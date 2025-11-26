import os

# Database URL - PostgreSQL configuration for production and development
# Format: postgresql://user:password@host:port/database
# Local docker-compose: postgresql://postgres:postgres@db:5432/bugtracker
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/bugtracker")

# API_URL = os.getenv("API_URL")  future set > CLI can call the API by HTTP