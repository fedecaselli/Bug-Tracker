# Bug-Tracker 

A comprehensive issue tracking system with both web interface and command-line interface, featuring automated tag generation and intelligent assignee suggestions.

## Features

- **Web Interface**: Modern, responsive web UI for managing projects, issues, and tags
- **Command Line Interface**: Full CLI for automation and power users
- **Project Management**: Create and organize projects with associated issues
- **Issue Tracking**: Complete CRUD operations with filtering and search capabilities
- **Automated Tag Generation**: AI-powered tag suggestions based on issue content
- **Smart Assignee Assignment**: Intelligent assignee suggestions based on expertise and workload
- **Analytics Dashboard**: Visual insights with charts
- **Tag Management**: Organize and analyze tag usage across projects

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
python -m venv venv
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

The CLI provides full functionality for automation and scripting:

### Project Management
```bash
# Create a project
python -m cli projects add --name "My Project"

# List projects
python -m cli projects list

# Update project name
python -m cli projects update --old-name "Old Name" --new-name "New Name"

# Delete a project
python -m cli projects rm --name "Project Name"
```

### Issue Management
```bash
# Create an issue
python -m cli issues add --project-name "My Project" --title "Bug Report" --priority high --status open

# Create issue with auto-features
python -m cli issues add --project-id 1 --title "Feature Request" --priority medium --status open --auto-tags --auto-assignee

# List issues with filters
python -m cli issues list --priority high --status open
python -m cli issues list --project-name "My Project" --tags "frontend,bug"

# Update an issue
python -m cli issues update --id 42 --status closed --assignee "john_doe"

# Delete an issue
python -m cli issues rm 42
```

### Tag Management
```bash
# List tags
python -m cli tags list

# Show tag usage statistics
python -m cli tags list --stats

# Rename a tag globally
python -m cli tags rename --old-name "frontend" --new-name "ui"

# Delete a tag
python -m cli tags delete --id 5

# Clean up unused tags
python -m cli tags cleanup
```

## Architecture

### Main project Structure
```
Bug-Tracker/
├── app.py                # FastAPI web application
├── config.py             # Configuration settings
├── requirements.txt      # Python dependencies
├── cli/                  # Command line interface
│   ├── main.py          # CLI commands and logic
│   └── __main__.py      # CLI entry point
├── core/                # Core business logic
│   ├── models.py        # Database models
│   ├── schemas.py       # Pydantic schemas
│   ├── db.py           # Database configuration
│   ├── validation.py   # Data validation
│   ├── automation/     # Automation features
│   │   ├── tag_generator.py      # Auto tag generation
│   │   └── assignee_suggestion.py # Smart assignee assigner
│   └── repos/          # Data access layer
│       ├── projects.py     # Project repository - handles project creation, retrieval, updates, deletion
│       ├── issues.py       # Issue repository - manages issue CRUD, filtering, tag associations, auto-assignment
│       └── tags.py         # Tag repository - tag operations, usage stats, cleanup, renaming
├── web/                 # Web interface
│   ├── api/            # REST API endpoints
│   │   ├── projects.py
│   │   ├── issues.py
│   │   └── tags.py
│   │  
│   ├── templates/      # HTML templates
│   └── static/         # CSS, JavaScript, assets
└── tests/              # Test suite
```

### Technology Stack

- **Backend**: FastAPI, SQLAlchemy, SQLite
- **Frontend**: HTML5, CSS3, JavaScript, Chart.js
- **CLI**: Typer
- **Testing**: pytest
- **Automation Features**: 
  - **Tag Generation**: Custom keyword-based algorithms
  - **Assignee Assignment**: Data-driven expertise and workload analysis

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

The system uses SQLite with the following main entities:

- **Projects**: Container for organizing issues
- **Issues**: Core tracking entity with title, description, log, summary, status, priority, assignee
- **Tags**: Categorization system with many-to-many relationship to issues
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

## Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/test_api_*.py      # API tests
pytest tests/test_repo_*.py     # Repository tests
pytest tests/test_cli.py        # CLI tests

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
