
import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from core.db import Base
from core import models  

@pytest.fixture(scope="function")   
def engine():
    """
    Create an in-memory SQLite engine for testing.

    Returns:
        Engine: SQLAlchemy engine connected to an in-memory SQLite database.

    Notes:
        - Foreign key constraints are enforced for SQLite.
        - Database schema is created before each test function.
    """
    eng = create_engine("sqlite:///:memory:", future=True)

    #enforce FK
    @event.listens_for(eng, "connect")
    def set_sqlite_pragma(dbapi_conn, _):
        cur = dbapi_conn.cursor()
        cur.execute("PRAGMA foreign_keys=ON")
        cur.close()

    Base.metadata.create_all(bind=eng)
    return eng


@pytest.fixture()
def db(engine):
    """
    Provide a SQLAlchemy session bound to the in-memory test database.

    Args:
        engine: SQLAlchemy engine fixture.

    Yields:
        Session: SQLAlchemy session for database operations.

    Finalizes:
        Closes the session after each test.
    """
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()

