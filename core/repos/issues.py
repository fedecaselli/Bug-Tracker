from typing import Iterable, List
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from core.models import Issue, Project
from core.schemas import IssueCreate, IssueUpdate
from core import models
from .exceptions import NotFound
from .tags import get_or_create_tags, update_tags, _normalize_name



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
    
    #TAGSMANAGEMENT
    if data.tag_names:
        tags = get_or_create_tags(db, data.tag_names)
        issue.tags = tags
    
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
    
    if "tag_names" in data and data["tag_names"] is not None:
        tag_names = data.pop("tag_names")
        update_tags(db,issue,tag_names)

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
    tags: List[str] | None = None,
    tags_match_all: bool = True
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
        
    #TAGSMANAGEMENT
    if tags:
        normalized_tags = [_normalize_name(tag) for tag in tags if _normalize_name(tag)]
        if normalized_tags:
            if tags_match_all:
                # Issue must have ALL specified tags
                for tag_name in normalized_tags:
                    query = query.join(models.Issue.tags.and_(models.Tag.name == tag_name))
            else:
                # Issue must have ANY of the specified tags
                query = query.join(models.Issue.tags).filter(models.Tag.name.in_(normalized_tags)).distinct()
    
    return query.offset(skip).limit(limit).all()

    


'''
from .tags import get_or_create_tags  # Import this, NOT update_tag

def update_issue(db: Session, issue_id: int, issue_in: IssueUpdate) -> models.Issue:
    """Update an issue, including its tags."""
    issue = get_issue(db, issue_id)
    
    # Get update data excluding unset fields
    data = issue_in.model_dump(exclude_unset=True)
    
    # Handle tags separately - this REPLACES the tags for this issue
    if "tag_names" in data and data["tag_names"] is not None:
        tag_names = data.pop("tag_names")
        # This gets existing tags or creates new ones automatically
        tags = get_or_create_tags(db, tag_names)  # Uses get_or_create, NOT update_tag
        issue.tags = tags  # Replace all tags for this issue
    
    # Update other fields
    for field, value in data.items():
        setattr(issue, field, value)

    db.commit()
    db.refresh(issue)
    return issue
'''