'''
#SQLALCCHEMY ORM STYLE
engine = create_engine(DATABASE_URL)
Base = declarative_base()
print("DB ready")
'''


from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base
from config import DATABASE_URL

# Basic connection to SQLite Database
engine = create_engine(DATABASE_URL,connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Enable SQLite foreign key enforcement
@event.listens_for(engine, "connect") #run every time new DB connection is created
def enable_foreign_keys(dbapi_conn, _):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

#Function responsible for managing database sessions
def get_db():
    db = SessionLocal() #each session is a connection to db
    try:
        yield db
    finally:
        db.close()
