from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from core.db import engine
from core.models import Base

app = FastAPI(title = "BugTracker")


@app.get("/health")
def health_check():
    return {"status": "healthy"}

app.mount("/static", StaticFiles(directory="web/static"), name="static")


#create database tables
Base.metadata.create_all(bind=engine)