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
from .exceptions import NotFound, AlreadyExists
from .tags import get_or_create_tags, update_tags
from .duplicate_checker import check_duplicate_issue
from core.automation import (
    AssigneeStrategy,
    TagSuggester,
)
from core.validation import (
    normalize_status,
    normalize_tag_names,
    optional_priority,
    optional_title,
)
from core.enums import IssuePriority, IssueStatus
from sqlalchemy import case


#CREATE ISSUE
def create_issue(
    db: Session,
    data: IssueCreate,
    tag_suggester: TagSuggester,
    assignee_strategy: AssigneeStrategy,
) -> Issue:
    """
    Create a new issue in the database.

    Args:
        db (Session): Database session.
        data (IssueCreate): Data for the new issue.

    Returns:
        Issue: The created issue.

    Raises:
        NotFound: If the project associated with the issue does not exist.
        AlreadyExists: If an identical issue already exists.
    """
        
    # Ensure project exists
    project = db.query(Project).filter_by(project_id=data.project_id).first()
    if not project:
        raise NotFound(f"Project {data.project_id} not found")
    
    # Check for duplicate issue
    if check_duplicate_issue(
        db=db,
        project_id=data.project_id,
        title=data.title,
        description=data.description,
        log=data.log,
        summary=data.summary,
        priority=data.priority,
        status=data.status,
        assignee=data.assignee,
        tag_names=data.tag_names
    ):
        raise AlreadyExists(f"An identical issue already exists in this project")
    
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
        
    # Auto-generate tags if requested
    if data.auto_generate_tags:
        generated_tags = tag_suggester.generate_tags(
            title=data.title,
            description=data.description or "",
            log=data.log or "",
        )
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
        issue_tag_names = [tag.name for tag in issue.tags] if issue.tags else []
        suggested_assignee = assignee_strategy.suggest_assignee(
            db,
            issue_tag_names,
            issue.status,
            issue.priority,
        )
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
        AlreadyExists: If the update would create a duplicate issue.
        ValueError: If no fields are provided to update.
    """
    issue = get_issue(db, issue_id)
    #Pydantic schema
    data = issue_in.model_dump(exclude_unset=True)
    
    if not data:
        raise ValueError("No fields provided to update")
    
    # Prepare the updated values for duplicate check
    updated_title = data.get("title", issue.title)
    updated_description = data.get("description", issue.description)
    updated_log = data.get("log", issue.log)
    updated_summary = data.get("summary", issue.summary)
    updated_priority = data.get("priority", issue.priority)
    updated_status = data.get("status", issue.status)
    updated_assignee = data.get("assignee", issue.assignee)
    updated_tag_names = data.get("tag_names", [tag.name for tag in issue.tags])

    # Check for duplicate issue (excluding current issue)
    if check_duplicate_issue(
        db=db,
        project_id=issue.project_id,
        title=updated_title,
        description=updated_description,
        log=updated_log,
        summary=updated_summary,
        priority=updated_priority,
        status=updated_status,
        assignee=updated_assignee,
        tag_names=updated_tag_names,
        exclude_issue_id=issue_id
    ):
        # Check if it's the same issue (all fields identical to current state)
        current_tag_names = {tag.name for tag in issue.tags}
        if (updated_title == issue.title and
            updated_description == issue.description and
            updated_log == issue.log and
            updated_summary == issue.summary and
            updated_priority == issue.priority and
            updated_status == issue.status and
            updated_assignee == issue.assignee and
            set(updated_tag_names) == current_tag_names):
            # Same issue, no change needed
            return issue
        else:
            # Different issue with same fields
            raise AlreadyExists(f"An identical issue already exists in this project")
    
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
    priority: IssuePriority | str | None = None,
    status: IssueStatus | str | None = None,
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
        ValueError: If pagination parameters are invalid.
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
    priority = optional_priority(priority)
    status = normalize_status(status)
    title = optional_title(title)
    tags = normalize_tag_names(tags, keep_none=True)
        
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




#SEARCH ISSUES
# Add this function at the end of the file

def search_issues(db: Session, query: str) -> list[models.Issue]:
    """
    Search for issues by title.

    Args:
        db (Session): Database session.
        query (str): Search query string.

    Returns:
        list[Issue]: List of issues matching the search query.
    """
    # Search only in title field
    return db.query(models.Issue).filter(models.Issue.title.ilike(f"%{query}%")).order_by(models.Issue.created_at.desc()).all()
