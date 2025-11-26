"""
Database Configuration

This module sets up the PostgreSQL database connection, session management, and ORM base class.
"""


from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import QueuePool
from sqlalchemy.engine.url import make_url
from config import DATABASE_URL

url = make_url(DATABASE_URL)

# Creates a connection to the database with sensible defaults per backend
if url.drivername.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=False,
    )
else:
    engine = create_engine(
        DATABASE_URL,
        poolclass=QueuePool,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,  # Verify connection is alive before using
        echo=False,
    )

# Provides scoped sessions for database operations.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all ORM models.
Base = declarative_base()

# Provides a database session for use in application logic.
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
