"""
Repository functions for managing issues

This module provides the core database operations for issues, including:
- Creating, retrieving, updating, and deleting issues.
- Filtering and listing issues with optional criteria.
- Handling tags and auto-assignment logic.
"""

from typing import List
from sqlalchemy.orm import Session
from core.models import Issue, Project
from core.schemas import IssueCreate, IssueUpdate
from core import models
from .exceptions import NotFound
from .tags import get_or_create_tags, update_tags, _normalize_name
from core.automation.tag_generator import TagGenerator
from core.automation.assignee_suggestion import AssigneeSuggester 
from core.validation import (validate_title, validate_priority, validate_status, validate_tag_names)
from sqlalchemy import case

#CREATE ISSUE
def create_issue(db:Session, data: IssueCreate) -> Issue:
    """
    Create a new issue in the database.

    Args:
        db (Session): Database session.
        data (IssueCreate): Data for the new issue.

    Returns:
        Issue: The created issue.

    Raises:
        NotFound: If the project associated with the issue does not exist.
    """
        
    # Ensure project exists
    project = db.query(Project).filter_by(project_id=data.project_id).first()
    if not project:
        raise NotFound(f"Project {data.project_id} not found")
    
    # Create issue object
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
    
    # Handle tags
    if data.tag_names:
        all_tags = list(data.tag_names)
    else:
        all_tags = []
    
    # Auto-generate tags if requestes
    if data.auto_generate_tags:
        tag_generator = TagGenerator()
        generated_tags = tag_generator.generate_tags(title=data.title, description=data.description or "", log=data.log or "")
        for tag in generated_tags:
            if tag not in all_tags:
                all_tags.append(tag)
    
    # Associate tags with issue
    if all_tags:
        tags = get_or_create_tags(db, all_tags)
        issue.tags = tags
                
    # Save issue to database
    db.add(issue)
    db.commit()
    db.refresh(issue)
    
    # Auto-assign an assignee if requested and no assignee is provided
    if data.auto_generate_assignee and not data.assignee:  
        suggester = AssigneeSuggester()
    
        # Get the tag names that were just assigned to the issue
        issue_tag_names = []
        if issue.tags:
            for tag in issue.tags:
                issue_tag_names.append(tag.name)
        
        # Suggest assignee based on predefined logic
        suggested_assignee = suggester.suggest_assignee(db, issue_tag_names, issue.status, issue.priority)
        
        # Update the issue with the suggested assignee
        if suggested_assignee:
            issue.assignee = suggested_assignee
            db.commit()
            db.refresh(issue)
            
    return issue
    
                
#GET ISSUE
def get_issue(db: Session, issue_id: int) -> models.Issue | None:
    """
    Retrieve an issue by its ID.

    Args:
        db (Session): Database session.
        issue_id (int): ID of the issue to retrieve.

    Returns:
        Issue: The retrieved issue.

    Raises:
        NotFound: If the issue does not exist.
    """
    issue = db.query(models.Issue).filter(models.Issue.issue_id == issue_id).first()
    if not issue:
        raise NotFound(f"Issue {issue_id} not found")
    return issue

    
#DELETE ISSUE
def delete_issue(db:Session, issue_id: int) -> bool:
    """
    Delete an issue by its ID.

    Args:
        db (Session): Database session.
        issue_id (int): ID of the issue to delete.

    Returns:
        bool: True if the issue was successfully deleted.

    Raises:
        NotFound: If the issue does not exist.
    """
    issue = get_issue(db, issue_id)
    db.delete(issue)
    db.commit()
    return True


#UPDATE ISSUE
def update_issue(db: Session, issue_id: int, issue_in: IssueUpdate) -> models.Issue | None:
    """
    Update an existing issue.

    Args:
        db (Session): Database session.
        issue_id (int): ID of the issue to update.
        issue_in (IssueUpdate): Data to update the issue with.

    Returns:
        Issue: The updated issue.

    Raises:
        NotFound: If the issue does not exist.
    """
    issue = get_issue(db, issue_id)
    #Pydantic schema
    data = issue_in.model_dump(exclude_unset=True)
    
    if not data:
        raise ValueError("No fields provided to update")
    
    # Update tags if provided
    if "tag_names" in data and data["tag_names"] is not None:
        tag_names = data.pop("tag_names")
        update_tags(db,issue,tag_names)

    # Update other fields 
    for field, value in data.items():
        setattr(issue, field, value)

    db.commit()
    db.refresh(issue)
    return issue

    
#LIST ISSUE
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
    """
    List issues with optional filters.

    Args:
        db (Session): Database session.
        skip (int): Number of issues to skip.
        limit (int): Maximum number of issues to return.
        assignee (str | None): Filter by assignee.
        priority (str | None): Filter by priority.
        status (str | None): Filter by status.
        title (str | None): Filter by title.
        project_id (int | None): Filter by project ID.
        tags (List[str] | None): Filter by tags.
        tags_match_all (bool): If True, match all tags; otherwise, match any tag.

    Returns:
        list[Issue]: List of issues matching the filters.

    Raises:
        NotFound: If the specified project does not exist.
    """
    # Validate pagination parameters
    if skip < 0:
        raise ValueError("Skip must be non-negative")
    if limit <= 0 or limit > 100:
        raise ValueError("Limit must be between 1 and 100")
    
    # Ensure project exists
    if project_id is not None:
        project = db.query(models.Project).filter(models.Project.project_id == project_id).first()
        if not project:
            raise NotFound(f"Project {project_id} not found")

    # Validate and normalize filter values using direct validation functions
    if priority is not None:
        priority = validate_priority(priority)  
    
    if status is not None:
        status = validate_status(status)  
    
    if title is not None:
        title = validate_title(title)  
    
    if tags is not None:
        tags = validate_tag_names(tags)  
        
    query = db.query(models.Issue)
    
    # Apply filters
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
        
    # Filter by tags
    if tags:
        if tags_match_all:
                # Issue must have ALL specified tags
            for tag_name in tags:
                query = query.join(models.Issue.tags).filter(models.Tag.name == tag_name)
        else:
            # Issue must have ANY of the specified tags
            query = query.join(models.Issue.tags).filter(models.Tag.name.in_(tags)).distinct()
    # Order by creation time (consider updated time if present)
    query = query.order_by(case((models.Issue.updated_at != None, models.Issue.updated_at), else_=models.Issue.created_at).desc())
    return query.offset(skip).limit(limit).all()


