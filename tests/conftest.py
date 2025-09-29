import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from core.db import Base
from core import models  

@pytest.fixture(scope="function")   
def engine():
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
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()

