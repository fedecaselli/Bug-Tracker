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
from sqlalchemy.orm import Session
from core import schemas
from core.db import get_db
from core.repos import projects as repo_projects
from core.repos import issues as repo_issues
from core.repos.exceptions import NotFound, AlreadyExists
from pydantic import ValidationError

# Initialize the router for project related endpoints
router = APIRouter(prefix="/projects", tags=["projects"])




# CREATE PROJECT
@router.post("/", response_model=schemas.ProjectOut)
def create_project(data: schemas.ProjectCreate, db: Session = Depends(get_db)):
    """
    Create a new project.

    Args:
        data (schemas.ProjectCreate): Data for the new project.
        db (Session): Database session.

    Returns:
        schemas.ProjectOut: The created project.

    Raises:
        HTTPException: If a project with the same name already exists.
    """
    try:
        return repo_projects.create_project(db, data)
    except NotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    except AlreadyExists as e: 
        raise HTTPException(status_code=409, detail=str(e))
    except (ValidationError, ValueError) as e:
        raise HTTPException(status_code=422, detail=str(e))


# LIST ALL PROJECTS
@router.get("/", response_model=list[schemas.ProjectOut])
def list_projects(db: Session = Depends(get_db)):
    """
    List all projects.

    Args:
        db (Session): Database session.

    Returns:
        list[schemas.ProjectOut]: List of all projects.
    """
    try:
        return repo_projects.list_projects(db)
    except NotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    except AlreadyExists as e: 
        raise HTTPException(status_code=409, detail=str(e))
    except (ValidationError, ValueError) as e:
        raise HTTPException(status_code=422, detail=str(e))

# GET PROJECT
'''
@router.get("/by-name", response_model=schemas.ProjectOut)
def get_project_by_name(name: str, db: Session = Depends(get_db)):
    """
    Retrieve a specific project by its name.

    Args:
        name (int): name of the project to retrieve.
        db (Session): Database session.

    Returns:
        schemas.ProjectOut: The retrieved project.

    Raises:
        HTTPException: If the project is not found.
    """
    try:
        return repo_projects.get_project_by_name(db, name)
    except NotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    except AlreadyExists as e: 
        raise HTTPException(status_code=409, detail=str(e))
    except (ValidationError, ValueError) as e:
        raise HTTPException(status_code=422, detail=str(e))
'''

# LIST ISSUES FOR PROJECT 
@router.get("/{project_id}/issues", response_model=list[schemas.IssueOut])
def list_issues_for_project(project_id: int, db: Session = Depends(get_db)):
    """
    List all issues associated with a specific project.

    Args:
        project_id (int): ID of the project.
        db (Session): Database session.

    Returns:
        list[schemas.IssueOut]: List of issues associated with the project.

    Raises:
        HTTPException: If the project is not found.
    """
    try:
        return repo_issues.list_issues(db, project_id=project_id)
    except NotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    except AlreadyExists as e: 
        raise HTTPException(status_code=409, detail=str(e))
    except (ValidationError, ValueError) as e:
        raise HTTPException(status_code=422, detail=str(e))
    
    

@router.get("/{project_id}", response_model=schemas.ProjectOut)
def get_project(project_id: int, db: Session = Depends(get_db)):
    """
    Retrieve a specific project by its ID.

    Args:
        project_id (int): ID of the project to retrieve.
        db (Session): Database session.

    Returns:
        schemas.ProjectOut: The retrieved project.

    Raises:
        HTTPException: If the project is not found.
    """
    try:
        return repo_projects.get_project(db, project_id)
    except NotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    except AlreadyExists as e: 
        raise HTTPException(status_code=409, detail=str(e))
    except (ValidationError, ValueError) as e:
        raise HTTPException(status_code=422, detail=str(e))



# UPDATE PROJECT
@router.put("/{project_id}", response_model=schemas.ProjectOut)
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
        HTTPException: If the project is not found or if the updated name already exists.
    """
    try:
        return repo_projects.update_project(db, project_id, data)
    except NotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    except AlreadyExists as e: 
        raise HTTPException(status_code=409, detail=str(e))
    except (ValidationError, ValueError) as e:
        raise HTTPException(status_code=422, detail=str(e))



# DELETE PROJECT
@router.delete("/{project_id}", response_model=bool)
def delete_project(project_id: int, db: Session = Depends(get_db)):
    """
    Delete a project by its ID.

    Args:
        project_id (int): ID of the project to delete.
        db (Session): Database session.

    Returns:
        bool: True if the project was successfully deleted.

    Raises:
        HTTPException: If the project is not found.
    """
    try:
        return repo_projects.delete_project(db, project_id)
    except NotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    except AlreadyExists as e: 
        raise HTTPException(status_code=409, detail=str(e))
    except (ValidationError, ValueError) as e:
        raise HTTPException(status_code=422, detail=str(e))




