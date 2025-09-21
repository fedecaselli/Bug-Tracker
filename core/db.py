from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from config import DATABASE_URL

#SQLALCCHEMY ORM STYLE
engine = create_engine(DATABASE_URL)

Base = declarative_base()

print("DB ready")