"""
Database Configuration 

This module sets up the database connection, session management, and ORM base class.
It also ensures SQLite foreign key constraints are enforced.
"""


from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base
from config import DATABASE_URL

# Creates a connection to the SQLite database specified in the configuration.
engine = create_engine(DATABASE_URL,connect_args={"check_same_thread": False})

# Provides scoped sessions for database operations.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all ORM models.
Base = declarative_base()

# Ensures foreign key constraints are enforced for SQLite databases.
@event.listens_for(engine, "connect") 
def enable_foreign_keys(dbapi_conn, _):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

# Provides a database session for use in application logic.
def get_db():
    db = SessionLocal() 
    try:
        yield db
    finally:
        db.close()
