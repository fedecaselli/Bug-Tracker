from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from core.db import engine
from core.models import Base
from web.api import projects, tags, issues

app = FastAPI(title = "BugTracker")

# Include API routers
app.include_router(projects.router)
app.include_router(issues.router)
app.include_router(tags.router)

# Set up templates
templates = Jinja2Templates(directory="web/templates")

@app.get("/health")
def health_check():
    return {"status": "healthy"}

# Frontend routes
@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/projects", response_class=HTMLResponse)
async def projects_page(request: Request):
    return templates.TemplateResponse("projects.html", {"request": request})

@app.get("/issues", response_class=HTMLResponse)
async def issues_page(request: Request):
    return templates.TemplateResponse("issues.html", {"request": request})

@app.get("/tags", response_class=HTMLResponse)
async def tags_page(request: Request):
    return templates.TemplateResponse("tags.html", {"request": request})

app.mount("/static", StaticFiles(directory="web/static"), name="static")
