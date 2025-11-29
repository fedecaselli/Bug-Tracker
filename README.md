# Bug-Tracker 

## Table of Contents
- [Overview](#overview)
- [Features](#features)  
- [Quick Start](#quick-start)
- [Web Interface](#web-interface)
- [Command Line Interface](#command-line-interface)
- [Architecture](#architecture)
- [API Endpoints](#api-endpoints)
- [CI/CD](#cicd)
- [Testing](#testing)
- [Development](#development)

## Overview

A comprehensive issue tracking system with both web interface and command-line interface, featuring automated tag generation and intelligent assignee suggestions.

Built with FastAPI and Typer CLI, this containerized application is designed for local development and Azure deployment (ACI). It includes health/metrics endpoints, Prometheus monitoring configuration, and complete CI/CD pipelines that run tests with coverage gates and automatically deploy the `main` branch.

**Key Capabilities:**
- Dual interface design (Web + CLI)
- AI-powered automation features
- Production-ready deployment pipeline
- Comprehensive monitoring and observability

## Features

### Core Functionality
- **Web Interface**: Modern, responsive web UI for managing projects, issues, and tags
- **Command Line Interface**: Full CLI for automation and scripting
- **Project Management**: Create and organize projects with associated issues
- **Issue Tracking**: Complete CRUD operations with filtering and search capabilities

### Intelligent Automation
- **Automated Tag Generation**: tag suggestions based on issue content analysis
- **Smart Assignee Assignment**: Intelligent assignee suggestions based on expertise and workload algorithms
- **Tag Management**: Organize and analyze tag usage across projects

### Analytics & Insights
- **Analytics Dashboard**: Visual insights with charts and statistics
- **Usage Analytics**: Track tag usage patterns and team performance
- **Health Monitoring**: Built-in health checks and Prometheus metrics

### DevOps Features
- **Containerized Deployment**: Docker-ready with Azure Container Instances support
- **CI/CD Pipeline**: Automated testing and deployment with coverage gates
- **Monitoring**: Prometheus metrics and observability tools

## Quick Start

### Prerequisites

- Python 3.8 or higher
- Virtual environment (recommended)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd Bug-Tracker
```

2. Create and activate a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Start the web server:
```bash
uvicorn app:app --reload
```

5. Open your browser and navigate to `http://localhost:8000`

## Web Interface

The web interface provides:

- **Dashboard** (`/`) - Overview with statistics and charts
- **Projects** (`/projects`) - Manage projects and view associated issues  
- **Issues** (`/issues`) - Create, edit, filter, and manage issues
- **Tags** (`/tags`) - Manage tags and view usage analytics

### API Documentation

When the server is running, access the interactive API documentation:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Command Line Interface

The CLI is published on PyPI and can also be run directly from the repo. Use whichever invocation matches how you installed it:

- Installed from PyPI (or `pip install .`): run commands with `cli ...`
- Running directly from the repo without installing: use `python -m cli ...`

Environment for CLI:
- `API_URL`: target API (`http://localhost:8000` local; use deployed host for prod).
- `API_TOKEN`: reserved for future auth (unused now).
- `LOG_LEVEL`: DEBUG/INFO/WARNING/ERROR (INFO default).

### Install from PyPI
```bash
pip install bug-tracker-cli

# verify installation
cli --help
```

Changes made via the CLI appear in the web UI after a page refresh.

### Run locally from this repo
```bash
# from the project root without installing
python -m cli --help
```

### Project Management
```bash
# Create a project
cli projects add --name "My Project"

# List projects
cli projects list

# Update project name
cli projects update --old-name "Old Name" --new-name "New Name"

# Delete a project
cli projects rm --name "Project Name"
```

### Issue Management
```bash
# Create an issue
cli issues add --project-name "My Project" --title "Bug Report" --priority high --status open

# Create issue with auto-features
cli issues add --project-id 1 --title "Feature Request" --priority medium --status open --auto-tags --auto-assignee

# List issues with filters
cli issues list --priority high --status open
cli issues list --project-name "My Project" --tags "frontend,bug"

# Update an issue
cli issues update --id 42 --status closed --assignee "john_doe"

# Delete an issue
cli issues rm 42
```

### Tag Management
```bash
# List tags
cli tags list

# Show tag usage statistics
cli tags list --stats

# Rename a tag globally
cli tags rename --old-name "frontend" --new-name "ui"

# Delete a tag
cli tags delete --id 5

# Clean up unused tags
cli tags cleanup
```

## Architecture

### Main project structure
```
Bug-Tracker/
├── app.py                      # FastAPI app (lifespan, metrics, routes)
├── config.py                   # App configuration (DATABASE_URL validation)
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Container image
├── docker-compose.yml          # Local stack
├── prometheus.yml              # Prometheus scrape config
├── .env.example                # Sample environment variables
├── cli/                        # Command line interface
│   ├── __main__.py             # CLI entry point
│   ├── main.py                 # CLI commands
│   ├── client.py               # Thin API client
│   ├── config.py               # CLI config (API_URL/API_TOKEN validation)
│   ├── payloads.py             # Payload builders
│   ├── formatters.py           # Output formatting
│   └── services.py             # Shared CLI utilities
├── core/                       # Core business logic
│   ├── logging.py              # Logging configuration
│   ├── enums.py                # Domain enums
│   ├── db.py                   # DB config/session
│   ├── models.py               # SQLAlchemy models
│   ├── schemas.py              # Pydantic schemas
│   ├── validation.py           # Validation helpers
│   ├── automation/             # Automation features
│   │   ├── tag_generator.py
│   │   └── assignee_suggestion.py
│   └── repos/                  # Data access layer
│       ├── projects.py
│       ├── issues.py
│       └── tags.py
├── web/                        # Web interface
│   ├── api/                    # REST API endpoints
│   │   ├── projects.py
│   │   ├── issues.py
│   │   └── tags.py
│   ├── templates/              # HTML templates
│   └── static/                 # CSS, JS, assets
├── tests/                      # Test suite
│   ├── unit/
│   └── integration/
└── .github/workflows/          # CI/CD pipelines
    ├── ci.yml                  # Tests + coverage gate
    └── deploy.yml              # Deploy to ACI after CI success
```

### Technology Stack

- **Backend**: FastAPI, SQLAlchemy, Alembic
- **CLI**: Typer
- **Monitoring**: Prometheus client, `/metrics`, `/health`
- **Container/Deploy**: Docker, Azure ACI/ACR, GitHub Actions CI/CD
- **Testing**: pytest with coverage gate
- **Automation**: Tag generation, assignee suggestion

## Automation Features

### Automatic Tag Generation

The system can automatically suggest tags based on issue content:

```python
# Keywords are analyzed from title, description, and logs
Keywords = {
    "bug": ["error", "bug", "fail", "crash", "broken", "issue"],
    "frontend": ["ui", "frontend", "interface", "button", "form", "page"],
    "backend": ["backend", "server", "api", "database", "db"],
    "performance": ["slow", "performance", "timeout", "lag"]
}
```

### Smart Assignee Assignment

Assignee suggestions are based on:
- Tag expertise (success rate with specific tags)
- Current workload (number of open issues)

Assignment logic only applies to:
- Status: "open" (unresolved issues)
- Priority: "high" (critical issues need immediate attention by best experts)

## Database Schema

The system defaults to SQLite locally and runs against Postgres in CI/production. 
Main entities:

- **Projects**: Container for organizing issues (unique name)
- **Issues**: Core tracking entity with title, description, log, summary, status, priority, assignee; belongs to a project
- **Tags**: Many-to-many labels for issues
- **Issue-Tag Association**: Junction table for flexible tagging

## API Endpoints

### Projects
- `GET /projects/` - List all projects
- `POST /projects/` - Create new project
- `GET /projects/{id}` - Get project details
- `PUT /projects/{id}` - Update project
- `DELETE /projects/{id}` - Delete project
- `GET /projects/{id}/issues` - Get project issues

### Issues
- `GET /issues/` - List issues (with filtering)
- `POST /issues/` - Create new issue
- `GET /issues/{id}` - Get issue details
- `PUT /issues/{id}` - Update issue
- `DELETE /issues/{id}` - Delete issue
- `POST /issues/{id}/auto-assign` - Auto-assign issue
- `POST /issues/suggest-tags` - Get tag suggestions

### Tags
- `GET /tags/` - List all tags
- `DELETE /tags/{id}` - Delete tag
- `PATCH /tags/rename` - Rename tag globally
- `DELETE /tags/cleanup` - Remove unused tags
- `GET /tags/stats/usage` - Get usage statistics

## Monitoring & Health

- `GET /health` returns basic status with a database connectivity probe.
- `GET /metrics` exposes Prometheus metrics (request count, latency, errors).
- Sample Prometheus config: see `prometheus.yml` (update `targets` to your deployed host, e.g. `bugtracker-app.northeurope.azurecontainer.io:8000`).
- Quick local scrape:
  ```bash
  docker run --rm -p 9090:9090 \
    -v $(pwd)/prometheus.yml:/etc/prometheus/prometheus.yml \
    prom/prometheus
  ```
  UI: visit `http://localhost:9090`, go to **Status > Targets** and ensure your host is UP; then open **Graph**, run queries like `http_requests_total` or `http_request_duration_seconds_bucket`, and plot the results.
  

## CI/CD

- **Pipeline**: CI (`ci.yml`) runs tests with 70% coverage gate on each push/PR
- **Deployment**: Deploy (`deploy.yml`) runs only after CI succeeds on `main` via `workflow_run` 
- **Secrets Required**: `AZURE_CREDENTIALS`, `AZURE_REGISTRY_LOGIN_SERVER`, `AZURE_REGISTRY_USERNAME`, `AZURE_REGISTRY_PASSWORD`, `AZURE_RESOURCE_GROUP`, `DATABASE_URL`
- **Live Endpoint**: http://bugtracker-app.northeurope.azurecontainer.io:8000

### Containerization & Deployment

**Local Testing:**
```bash
docker build -t bugtracker:local .
docker run --rm -p 8000:8000 -e DATABASE_URL="sqlite:///./bugtracker.db" bugtracker:local
```

**Production Deployment:**
- Images tagged with commit SHA and `latest`
- Automated deployment to Azure Container Instances on `main` branch
- **Rollback**: Redeploy using older SHA tag instead of `latest` in ACI create command

**Flow**: PR > CI (tests + coverage) > Deploy (if CI passes) > ACI Updates

## Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/test_api_*.py      # API tests
pytest tests/test_repo_*.py     # Repository tests
pytest tests/test_cli.py        # CLI tests

# Run tests by type
pytest tests/unit/              # Unit tests (isolated, fast)
pytest tests/integration/       # Integration tests (database, API)

# Run with coverage
pytest --cov=. --cov-report=html --cov-fail-under=70
```

## Configuration

The application can be configured through environment variables or `config.py`:

- `DATABASE_URL`: Database connection string (default: SQLite)

## Development

### Code Structure

- **Repository Pattern**: Clean separation between business logic and data access through repository classes
- **Schema Validation**: Pydantic schemas ensure data integrity
- **Error Handling**: Consistent exception handling across CLI and API
- **Separation of Concerns**: Clear separation between web, CLI, and core logic

### Adding New Features

1. Define data models in `core/models.py`
2. Create Pydantic schemas in `core/schemas.py`
3. Implement repository methods in `core/repos/`
4. Add API endpoints in `web/api/`
5. Add CLI commands in `cli/main.py`
6. Create tests in `tests/`



-

## Common Commands

```bash
# Local development
docker-compose up --build      # Start everything
docker-compose down             # Stop everything
docker-compose logs app         # See app logs
docker-compose exec db psql ... # Access database

# Generate migrations
alembic revision --autogenerate -m "description"
alembic upgrade head           # Apply migrations

# View Azure resources
az container show --resource-group bugtracker-rg --name bugtracker-app
az container logs --resource-group bugtracker-rg --name bugtracker-app
```
