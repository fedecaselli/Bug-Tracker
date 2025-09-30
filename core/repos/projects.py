from typing import Iterable
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from core.models import Project
from core.schemas import ProjectCreate, ProjectUpdate
from core import models
from .exceptions import AlreadyExists, NotFound


#CREATE PROJECT
def create_project(db: Session, data: ProjectCreate) -> Project:
    if db.query(Project).filter_by(name=data.name).first():
        raise AlreadyExists(f"Project {data.name} already exists")
    project = Project(name=data.name)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project
    
    
#DELETE PROJECT
def delete_project(db:Session, project_id: int) -> bool:
    project = get_project(db, project_id)
    if not project:
        raise NotFound(f"Project not found")
    
    db.delete(project)
    db.commit()
    return True

#GET PROJECT
def get_project(db: Session, project_id: int) -> models.Project | None:
    project = db.query(models.Project).filter(models.Project.project_id == project_id).first()
    if not project:
        raise NotFound(f"Project not found")
    return project
    
#GET PROJECT BY NAME
def get_project_by_name(db: Session, name: str) -> models.Project:
    project = db.query(models.Project).filter(models.Project.name == name).first()
    if not project:
        raise NotFound(f"Project with name '{name}' not found")
    return project

#name -> id and then id -> project would be slower.
#name uniqueness makes the lookup "equivalent" to ID lookup
#indexing on the name column in the model gives faster lookup

#UPDATE
def update_project(db: Session, project_id: int, project_in: ProjectUpdate) -> models.Project:
    project = get_project(db, project_id)
    if project_in.name is not None:
        exists = db.query(Project).filter(Project.name == project_in.name, Project.project_id != project_id).first()
        if exists:
            raise AlreadyExists(f"Another project already uses the name '{project_in.name}'")
        project.name = project_in.name
    db.commit()
    db.refresh(project)
    return project

#LIST
def list_projects(db: Session, skip: int = 0, limit: int = 100) -> list[models.Project]:
    return db.query(models.Project).offset(skip).limit(limit).all()
