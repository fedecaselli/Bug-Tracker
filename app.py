from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from core.db import engine
from core.models import Base
from web.api import projects, tags, issues

app = FastAPI(title = "BugTracker")

app.include_router(projects.router)
app.include_router(issues.router)
app.include_router(tags.router)

@app.get("/health")
def health_check():
    return {"status": "healthy"}

app.mount("/static", StaticFiles(directory="web/static"), name="static")


#create database tables
Base.metadata.create_all(bind=engine)