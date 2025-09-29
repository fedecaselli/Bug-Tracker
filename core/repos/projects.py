from typing import Iterable
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from core.models import Project
from core.schemas import ProjectCreate, ProjectUpdate
from core import models


#CREATE PROJECT
def create_project(db:Session, data: ProjectCreate) -> Project:
    project = Project(name = data.name)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project
    
#GET PROJECT
def get_project(db: Session, project_id: int) -> models.Project | None:
    #Get project by ID
    return db.query(models.Project).filter(models.Project.project_id == project_id).first()
    
#DELETE PROJECT
def delete_project(db:Session, project_id: int) -> bool:
    project = get_project(db, project_id)
    if not project:
        return False
    
    db.delete(project)
    db.commit()
    return True

    
#UPDATE
def update_project(db: Session, project_id: int, project_in: ProjectUpdate) -> models.Project | None:
    """Update a project if it exists."""
    project = get_project(db, project_id)
    if not project:
        return None
    
    # Only update fields that were sent
    for field, value in project_in.model_dump(exclude_unset=True).items():
        setattr(project, field, value)
    
    db.commit()
    db.refresh(project)
    return project

#LIST
def list_projects(db: Session, skip: int = 0, limit: int = 100) -> list[models.Project]:
    return db.query(models.Project).offset(skip).limit(limit).all()
