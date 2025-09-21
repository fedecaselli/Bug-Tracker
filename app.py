from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

app = FastAPI(title = "BugTracker")


@app.get("/health")
def health_check():
    return {"status": "healthy"}

app.mount("/static", StaticFiles(directory="web/static"), name="static")
