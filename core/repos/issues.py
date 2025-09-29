from typing import Iterable
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from core.models import Issue, Project
from core.schemas import IssueCreate, IssueUpdate
from core import models
from .exceptions import NotFound


#CREATE ISSUE
def create_issue(db:Session, data: IssueCreate) -> Issue:
    project = db.query(Project).filter_by(project_id=data.project_id).first()
    if not project:
        raise NotFound(f"Project {data.project_id} not found")
    issue = Issue(
        project_id=data.project_id,
        title=data.title,
        description=data.description,
        log=data.log,
        summary=data.summary,
        priority=data.priority,
        status=data.status,
        assignee=data.assignee,
    )
    
    db.add(issue)
    db.commit()
    db.refresh(issue)
    return issue
    
        
        
#GET ISSUE
def get_issue(db: Session, issue_id: int) -> models.Issue | None:
    #Get issue by ID
    issue = db.query(models.Issue).filter(models.Issue.issue_id == issue_id).first()
    if not issue:
        raise NotFound(f"Issue {issue_id} not found")
    return issue
    
#DELETE ISSUE
def delete_issue(db:Session, issue_id: int) -> bool:
    issue = get_issue(db, issue_id)
    #if not issue will raise > NotFound
    db.delete(issue)
    db.commit()
    return True


#UPDATE ISSUE
def update_issue(db: Session, issue_id: int, issue_in: IssueUpdate) -> models.Issue | None:
    issue = get_issue(db, issue_id)
    #if no issue > not found
    data = issue_in.model_dump(exclude_unset=True)
    if "tags" in data and data["tags"] is not None:
        tag_names = data.pop("tags")
        tags = db.query(models.Tag).filter(models.Tag.name.in_(tag_names)).all()
        issue.tags = tags

    #update other fields by looping
    for field, value in data.items():
        setattr(issue, field, value)

    db.commit()
    db.refresh(issue)
    return issue
    
    
#LIST
'''
def list_issues(db: Session, skip: int = 0, limit: int = 100) -> list[models.Issue]:
    return db.query(models.Issue).offset(skip).limit(limit).all()
'''


def list_issues(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    assignee: str | None = None,
    priority: str | None = None,
    status: str | None = None,
    title: str | None = None,
    project_id: int | None = None,
) -> list[models.Issue]:
    if project_id is not None:
        # make sure project exists
        project = db.query(models.Project).filter(models.Project.project_id == project_id).first()
        if not project:
            raise NotFound(f"Project {project_id} not found")
    query = db.query(models.Issue)
    if project_id:
        query = query.filter(models.Issue.project_id == project_id)
    if assignee:
        query = query.filter(models.Issue.assignee == assignee)
    if priority:
        query = query.filter(models.Issue.priority == priority)
    if status:
        query = query.filter(models.Issue.status == status)
    if title:
        query = query.filter(models.Issue.title == title)
    return query.offset(skip).limit(limit).all()



     


    