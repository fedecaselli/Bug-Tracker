# Bug-Tracker 

## Table of Contents
- [Overview](#overview)
- [Features](#features)  
- [Quick Start](#quick-start)
- [Web Interface](#web-interface)
- [Configuration](#configuration)
- [Command Line Interface](#command-line-interface)
- [Architecture](#architecture)
- [Automation Features](#automation-features)
- [Database Schema](#database-schema)
- [API Endpoints](#api-endpoints)
- [CI/CD](#cicd)
- [Testing](#testing)
- [Development](#development)
- [Common Commands](#common-commands)

## Overview

A comprehensive issue tracking system with both web interface and command-line interface, featuring automated tag generation and intelligent assignee suggestions.

Built with FastAPI and Typer CLI, this containerized application is designed for local development and Azure deployment (ACI). It includes health/metrics endpoints, Prometheus monitoring configuration, and complete CI/CD pipelines that run tests with coverage gates and automatically deploy the `main` branch.

**Key Capabilities:**
- Dual interface design (Web + CLI)
- Automation features based on keyword analysis and workload algorithms
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
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

5. Open your browser and navigate to `http://localhost:8000`

## Web Interface

The web interface provides:

- **Dashboard** (`/`) - Overview with statistics and charts
- **Projects** (`/projects`) - Manage projects and view associated issues  
- **Issues** (`/issues`) - Create, edit, filter, and manage issues
- **Tags** (`/tags`) - Manage tags and view usage analytics


## Configuration

The Bug Tracker application can be configured through environment variables. Configuration applies to both the web application and CLI tool.

### Application Configuration

| Variable | Description | Default | Examples |
|----------|-------------|---------|----------|
| `DATABASE_URL` | Database connection string | `sqlite:///./bugtracker.db` | `postgresql://user:pass@host:5432/db` |
| `SECRET_KEY` | Secret key for security (JWT, sessions) | Auto-generated | `your-secret-key-here` |
| `LOG_LEVEL` | Application logging level | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |

### CLI Configuration

| Variable | Description | Default | Examples |
|----------|-------------|---------|----------|
| `API_URL` | Target API endpoint | `http://localhost:8000` | `https://bugtracker-app.northeurope.azurecontainer.io:8000` |
| `API_TOKEN` | Authentication token (reserved for future use) | None | `your-api-token-here` |
| `LOG_LEVEL` | CLI logging level | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |


**Local Development**
```bash
export DATABASE_URL="sqlite:///./bugtracker.db"
export API_URL="http://localhost:8000"
export LOG_LEVEL=INFO
```

**Production (Azure Container Instances)**
```bash
# Secrets configured in GitHub for deploy.yml:
# AZURE_CREDENTIALS, AZURE_REGISTRY_LOGIN_SERVER, AZURE_REGISTRY_USERNAME,
# AZURE_REGISTRY_PASSWORD, AZURE_RESOURCE_GROUP, DATABASE_URL
# Deploy runs automatically after CI success on main.

# To run the built image manually:
docker pull <registry>/bugtracker:latest
docker run -p 8000:8000 -e DATABASE_URL="$DATABASE_URL" <registry>/bugtracker:latest
```

### API Documentation

When the server is running, access the interactive API documentation:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Command Line Interface

The CLI is published on PyPI ([bug-tracker-cli](https://pypi.org/project/bug-tracker-cli/)) and can also be run directly from the repo. Use whichever invocation matches how you installed it:

- Installed from PyPI (or `pip install .`): run commands with `cli ...`
- Running directly from the repo without installing: use `python -m cli ...`

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

The system can automatically suggest tags based on issue content by analyzing title, description, and logs:

```python
# Keywords are analyzed from title, description, and logs
Keywords = {
    "bug": ["error", "bug", "fail", "crash", "broken", "issue"],
    "frontend": ["ui", "frontend", "interface", "button", "form", "page"],
    "backend": ["backend", "server", "api", "database", "db"],
    "performance": ["slow", "performance", "timeout", "lag"]
}
```

**Matching Logic**:
- Keywords use word boundary matching (e.g., "bug" matches "bug" but not "debugging")
- Matching is case-insensitive
- All matching categories are suggested as tags for the issue

### Smart Assignee Assignment

The system intelligently suggests the best team member to handle an issue by analyzing:
- **Tag Expertise**: Success rate with specific tags (calculated as the number of closed issues tagged with that category for each assignee)
- **Current Workload**: Number of open issues currently assigned to each team member

**Assignment Strategy**:
- Prioritizes assignees with highest success rate for the issue's tags
- Among candidates with similar expertise, selects the person with the lowest workload
- Only applies to high-priority, open-status issues (critical issues need immediate attention from best experts)

**Access via API**: `POST /issues/{id}/auto-assign` to automatically assign based on the algorithm

## Database Schema

The system defaults to SQLite locally and runs against Postgres in CI/production.

**Main Entities**:

- **Projects**: Container for organizing issues (unique name, 1-200 characters)
- **Issues**: Core tracking entity with title, description, log, summary, status, priority, assignee; belongs to a project
- **Tags**: Many-to-many labels for issues (1-100 characters per tag name)
- **Issue-Tag Association**: Junction table for flexible tagging

**Field Constraints**:
- Project names: 1-200 characters (required, unique, indexed)
- Tag names: 1-100 characters (required, unique, indexed)
- Issue titles: 1-100 characters (required)
- Issue status: `open`, `in_progress`, or `closed`
- Issue priority: `low`, `medium`, or `high`

**Performance Indexes**:
- Composite index on `(issues.status, issues.priority)` - optimizes filtered issue queries
- Composite index on `(issues.assignee, issues.status)` - optimizes workload calculations
- Individual indexes on `assignee`, `created_at`, `priority`, `project_id`, and `status`

**Database Migrations**:
The application uses Alembic for schema versioning. Migration files are stored in the `migrations/versions/` directory. The most recent migration is applied automatically when the application starts (see `docker-compose.yml` and `Dockerfile`). To manually check or modify migrations, use the Alembic commands in the [Common Commands](#common-commands) section.

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

### Monitoring & Health
- `GET /health` returns basic status with a database connectivity probe.
- `GET /metrics` exposes Prometheus metrics (request count, latency, errors).

**Prometheus Configuration**:
- For local development: Uncomment the `localhost:8000` target in `prometheus.yml` (change `# - localhost:8000` to `- localhost:8000`)
- For production: Update the target to your deployed host (e.g., `bugtracker-app.northeurope.azurecontainer.io:8000`)

**Quick local setup**:
```bash
docker run --rm -p 9090:9090 \
  -v $(pwd)/prometheus.yml:/etc/prometheus/prometheus.yml \
  prom/prometheus
```
Then visit `http://localhost:9090`, go to **Status > Targets** and ensure your host is UP; then open **Graph**, run queries like `http_requests_total` or `http_request_duration_seconds_bucket`, and plot the results.

### API Response Examples

For interactive exploration of response schemas, use the built-in Swagger UI documentation:
- **Swagger UI**: `http://localhost:8000/docs` - Try out API requests and see live responses
- **ReDoc**: `http://localhost:8000/redoc` - Browse detailed schema documentation

**Example Health Check Response**:
```json
{
  "status": "healthy",
  "database": "connected"
}
```

**Example Get Project Response**:
```json
{
  "id": 1,
  "name": "My Project",
  "created_at": "2024-01-15T10:30:00"
}
```

**Example Get Issue Response**:
```json
{
  "id": 42,
  "project_id": 1,
  "title": "Login button not responsive",
  "description": "Button doesn't respond on mobile",
  "priority": "high",
  "status": "open",
  "assignee": "alice",
  "tags": ["frontend", "bug"],
  "created_at": "2024-01-20T14:22:15",
  "updated_at": "2024-01-21T09:45:30"
}
```


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


## Development

### Code Structure

- **Repository Pattern**: Clean separation between business logic and data access through repository classes
- **Schema Validation**: Pydantic schemas ensure data integrity
- **Error Handling**: Consistent exception handling across CLI and API
- **Separation of Concerns**: Clear separation between web, CLI, and core logic; CLI split into client/payloads/formatters/services
- **Config/Logging**: Centralized logging (`core/logging.py`, `LOG_LEVEL` env) and config validation (`config.py`, `cli/config.py`)
- **Observability**: `/health`, `/metrics`, Prometheus config; metrics middleware with duplication guard
- **Testing**: Unit/integration suites with 70% coverage gate in CI

### Exception Handling

The application uses custom exceptions for consistent error handling:

- **`NotFound`** - Raised when a resource (project, issue, or tag) doesn't exist
  - HTTP Response: 404 Not Found
  - CLI Response: Error message with resource details

- **`AlreadyExists`** - Raised when attempting to create a duplicate resource (e.g., project with same name, tag that already exists)
  - HTTP Response: 409 Conflict
  - CLI Response: Error message indicating the resource already exists

- **`ValidationError`** - Raised by Pydantic when input data doesn't match expected schema
  - HTTP Response: 422 Unprocessable Entity
  - CLI Response: Detailed validation error messages

All exceptions are defined in `core/repos/exceptions.py` and automatically converted to appropriate HTTP responses by FastAPI's exception handlers.


## Common Commands

```bash
# Local development
docker-compose up --build      # Start everything
docker-compose down             # Stop everything
docker-compose ps              # Check service status (healthy, starting, exited)
docker-compose logs app         # See app logs
docker-compose logs db          # See database logs
docker-compose exec db psql ... # Access database

# Verify health status
docker-compose ps              # Shows "(healthy)" status for each service
# Expected output:
#   NAME    STATUS
#   app     Up X min (healthy)
#   db      Up X min (healthy)

# Database migrations
alembic current                # Check current migration version
alembic history                # View migration history
alembic revision --autogenerate -m "description"  # Generate new migration
alembic upgrade head           # Apply all pending migrations
alembic downgrade -1           # Revert to previous migration
alembic stamp head             # Mark all migrations as applied (if DB exists)

# View Azure resources
az container show --resource-group bugtracker-rg --name bugtracker-app
az container logs --resource-group bugtracker-rg --name bugtracker-app
```
