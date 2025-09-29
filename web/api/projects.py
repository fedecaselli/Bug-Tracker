from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core import schemas
from core import models
from core.db import get_db
from core.repos import projects as repo_projects
from core.repos import issues as repo_issues
from core.repos.exceptions import NotFound

router = APIRouter(prefix="/projects", tags=["projects"])

@router.post("/", response_model=schemas.ProjectOut)
def create_project(data: schemas.ProjectCreate, db: Session = Depends(get_db)):
    return repo_projects.create_project(db, data)

@router.get("/{project_id}", response_model=schemas.ProjectOut)
def get_project(project_id: int, db: Session = Depends(get_db)):
    try:
        return repo_projects.get_project(db, project_id)
    except NotFound as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/", response_model=list[schemas.ProjectOut])
def list_projects(db: Session = Depends(get_db)):
    return repo_projects.list_projects(db)

@router.put("/{project_id}", response_model=schemas.ProjectOut)
def update_project(project_id: int, data: schemas.ProjectUpdate, db: Session = Depends(get_db)):
    try:
        return repo_projects.update_project(db, project_id, data)
    except NotFound as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{project_id}", response_model=bool)
def delete_project(project_id: int, db: Session = Depends(get_db)):
    return repo_projects.delete_project(db, project_id)

'''
@router.get("/{project_id}/issues", response_model=list[schemas.IssueOut])
def list_issues_for_project(project_id: int, db: Session = Depends(get_db)):
    project = repo_projects.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return repo_issues.list_issues(db, title=None, assignee=None, priority=None, status=None, skip=0, limit=100)
'''

@router.get("/{project_id}/issues", response_model=list[schemas.IssueOut])
def list_issues_for_project(project_id: int, db: Session = Depends(get_db)):
    return repo_issues.list_issues(db, project_id=project_id)