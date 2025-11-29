import time

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from core.db import engine
from core.logging import configure_logging, get_logger
from core.models import Base
from web.api import projects, tags, issues

configure_logging()
logger = get_logger(__name__)

app = FastAPI(title = "BugTracker")

# Prometheus metrics
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status"],
)
REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "path"],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1, 2, 5),
)
REQUEST_ERRORS = Counter(
    "http_requests_error_total",
    "Total HTTP requests that returned errors (status >= 400)",
    ["method", "path", "status"],
)


@app.on_event("startup")
async def on_startup():
    logger.info("Application startup")


@app.on_event("shutdown")
async def on_shutdown():
    logger.info("Application shutdown")


@app.middleware("http")
async def exception_logging_middleware(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception:
        logger.exception("Unhandled exception for %s %s", request.method, request.url.path)
        raise


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    # Measure request count, latency, and errors for Prometheus
    method = request.method
    path = request.url.path
    start_time = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        duration = time.perf_counter() - start_time
        REQUEST_COUNT.labels(method=method, path=path, status="500").inc()
        REQUEST_ERRORS.labels(method=method, path=path, status="500").inc()
        REQUEST_LATENCY.labels(method=method, path=path).observe(duration)
        raise
    duration = time.perf_counter() - start_time
    status_code = str(response.status_code)
    REQUEST_COUNT.labels(method=method, path=path, status=status_code).inc()
    if response.status_code >= 400:
        REQUEST_ERRORS.labels(method=method, path=path, status=status_code).inc()
    REQUEST_LATENCY.labels(method=method, path=path).observe(duration)
    return response

# Include API routers
app.include_router(projects.router)
app.include_router(issues.router)
app.include_router(tags.router)

# Set up templates
templates = Jinja2Templates(directory="web/templates")

@app.get("/health")
def health_check():
    # Simple health check with database connectivity probe
    db_ok = True
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except SQLAlchemyError:
        db_ok = False
    return {"status": "ok", "database": "ok" if db_ok else "unavailable"}


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

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
