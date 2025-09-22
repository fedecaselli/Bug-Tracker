from typing import Iterable
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from core.models import Issue
from core.schemas import IssueCreate, IssueUpdate
from core import models


#CREATE ISSUE
def create_issue(db:Session, data: IssueCreate) -> Issue:
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
    return db.query(models.Issue).filter(models.Issue.issue_id == issue_id).first()
    
#DELETE ISSUE
def delete_issue(db:Session, issue_id: int) -> bool:
    issue = get_issue(db, issue_id)
    if not issue:
        return False
    
    db.delete(issue)
    db.commit()
    return True


#UPDATE ISSUE
def update_issue(db: Session, issue_id: int, issue_in: IssueUpdate) -> models.Issue | None:
    """Update a project if it exists."""
    issue = get_issue(db, issue_id)
    if not issue:
        return None
    
    # Only update fields that were sent
    for field, value in issue_in.model_dump(exclude_unset=True).items():
        setattr(issue, field, value)
    
    db.commit()
    db.refresh(issue)
    return issue
    
    
#LIST
def list_issues(db: Session, skip: int = 0, limit: int = 100) -> list[models.Issue]:
    return db.query(models.Issue).offset(skip).limit(limit).all()

     


    