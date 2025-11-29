"""
API Endpoints for Managing Projects in the Bug Tracker Application

This module provides the API endpoints for creating, retrieving, updating, deleting, and listing projects. It also includes endpoints 
for retrieving issues associate with a specific project.

Key Features:
- Create, retrieve, update, and delete projects.
- List all projects.
- Retrieve issues for a specific project.
"""

from fastapi import APIRouter, Depends, HTTPException
from core.logging import get_logger
from sqlalchemy.orm import Session
from core import schemas
from core.db import get_db
from core.repos import projects as repo_projects
from core.repos import issues as repo_issues
from core.repos.exceptions import NotFound, AlreadyExists
from pydantic import ValidationError
from web.api.exceptions import handle_repo_exceptions

# Initialize the router for project related endpoints
router = APIRouter(prefix="/projects", tags=["projects"])
logger = get_logger(__name__)




# CREATE PROJECT
@router.post("/", response_model=schemas.ProjectOut)
@handle_repo_exceptions
def create_project(data: schemas.ProjectCreate, db: Session = Depends(get_db)):
    """
    Create a new project.

    Args:
        data (schemas.ProjectCreate): Data for the new project.
        db (Session): Database session.

    Returns:
        schemas.ProjectOut: The created project.

    Raises:
        404: If no projects are found.
        409: If a conflict occurs.
        422: If validation fails.
    """
    project = repo_projects.create_project(db, data)
    logger.info("Created project '%s' (id=%s)", project.name, project.project_id)
    return project


# LIST ALL PROJECTS
@router.get("/", response_model=list[schemas.ProjectOut])
@handle_repo_exceptions
def list_projects(db: Session = Depends(get_db)):
    """
    List all projects.

    Args:
        db (Session): Database session.

    Returns:
        list[schemas.ProjectOut]: List of all projects.
    Raises:
        404: If no projects are found.
        409: If a conflict occurs.
        422: If validation fails.
    """
    return repo_projects.list_projects(db)


# LIST ISSUES FOR PROJECT 
@router.get("/{project_id}/issues", response_model=list[schemas.IssueOut])
@handle_repo_exceptions
def list_issues_for_project(project_id: int, db: Session = Depends(get_db)):
    """
    List all issues associated with a specific project.

    Args:
        project_id (int): ID of the project.
        db (Session): Database session.

    Returns:
        list[schemas.IssueOut]: List of issues associated with the project.

    Raises:
        404: If no projects are found.
        409: If a conflict occurs.
        422: If validation fails.
    """
    return repo_issues.list_issues(db, project_id=project_id)
    
    

@router.get("/{project_id}", response_model=schemas.ProjectOut)
@handle_repo_exceptions
def get_project(project_id: int, db: Session = Depends(get_db)):
    """
    Retrieve a specific project by its ID.

    Args:
        project_id (int): ID of the project to retrieve.
        db (Session): Database session.

    Returns:
        schemas.ProjectOut: The retrieved project.

    Raises:
        404: If no projects are found.
        409: If a conflict occurs.
        422: If validation fails.
    """
    return repo_projects.get_project(db, project_id)



# UPDATE PROJECT
@router.put("/{project_id}", response_model=schemas.ProjectOut)
@handle_repo_exceptions
def update_project(project_id: int, data: schemas.ProjectUpdate, db: Session = Depends(get_db)):
    """
    Update an existing project.

    Args:
        project_id (int): ID of the project to update.
        data (schemas.ProjectUpdate): Updated data for the project.
        db (Session): Database session.

    Returns:
        schemas.ProjectOut: The updated project.

    Raises:
        404: If no projects are found.
        409: If a conflict occurs.
        422: If validation fails.
    """
    updated = repo_projects.update_project(db, project_id, data)
    logger.info("Updated project id=%s to name='%s'", updated.project_id, updated.name)
    return updated



# DELETE PROJECT
@router.delete("/{project_id}", response_model=bool)
@handle_repo_exceptions
def delete_project(project_id: int, db: Session = Depends(get_db)):
    """
    Delete a project by its ID.

    Args:
        project_id (int): ID of the project to delete.
        db (Session): Database session.

    Returns:
        bool: True if the project was successfully deleted.

    Raises:
        404: If no projects are found.
        409: If a conflict occurs.
        422: If validation fails.
    """
    logger.info("Deleted project id=%s", project_id)
    return repo_projects.delete_project(db, project_id)


