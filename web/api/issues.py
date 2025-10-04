"""
API Endpoints for Managing Issues in the Bug Tracker Application

This module provides the API endpoints for creating, retrieving, updating, deleting, and filtering issues. It also includes endpoints 
for auto-assigning issues to assignees and generating AI-based tag suggestions.

Key Features:
- Create, retrieve, update, and delete issues.
- Filter issues by various criteria such as assignee, priority, status, and tags.
- Auto-assign issues to the best assignee based on workload and expertise.
- Generate tag suggestions using AI-based logic.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, List
from fastapi import Query
from core import schemas
from core.db import get_db
from core.repos import issues as repo_issues
from core.repos.exceptions import NotFound, AlreadyExists
from core.automation.tag_generator import TagGenerator  
from core.automation.assignee_suggestion import AssigneeSuggester  
from core.schemas import IssueOut
from pydantic import ValidationError 


# Initialize the router for issue related endpoints
router = APIRouter(prefix="/issues", tags=["issues"])

def handle_repo_exceptions(func):
    """Decorator to handle repository exceptions with proper HTTP status codes."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except NotFound as e:
            raise HTTPException(status_code=404, detail=str(e))
        except AlreadyExists as e: 
            raise HTTPException(status_code=409, detail=str(e))
        except (ValidationError, ValueError) as e:
            raise HTTPException(status_code=422, detail=str(e))
    return wrapper

#CREATE ISSUE
@router.post("/", response_model=schemas.IssueOut)
@handle_repo_exceptions
def create_issue(data: schemas.IssueCreate, db: Session = Depends(get_db)):
    """
    Create a new issue.

    Args:
        data (schemas.IssueCreate): Data for the new issue.
        db (Session): Database session.

    Returns:
        schemas.IssueOut: The created issue.

    Raises:
        HTTPException: If the associated project is not found.
    """
    return repo_issues.create_issue(db, data)
    
# AUTO-ASSIGN TASK TO ASSIGNEE    
@router.post("/{issue_id}/auto-assign", response_model=dict)
@handle_repo_exceptions
def auto_assign_issue(issue_id: int, db: Session = Depends(get_db)):
    """
    Automatically assign an issue to the best available assignee.

    Args:
        issue_id (int): ID of the issue to assign.
        db (Session): Database session.

    Returns:
        dict: A message indicating the assigned assignee.

    Raises:
        HTTPException: If the issue is not found or auto-assignment fails.
    """
    suggester = AssigneeSuggester()
    success = suggester.auto_assign(db, issue_id)
    if success:
        issue_after = repo_issues.get_issue(db, issue_id)
        return {"assigned_to": issue_after.assignee}
    else:
        raise HTTPException(status_code=400, detail="Could not automatically assign")




# SUGGEST TAGS
@router.post("/suggest-tags", response_model=dict)
def suggest_tags_api(
    title: str = Query(..., description="Issue title"),
    description: Optional[str] = Query(None, description="Issue description"),
    log: Optional[str] = Query(None, description="Error log")
):
    """
    Generate AI-based tag suggestions for an issue.

    Args:
        title (str): Title of the issue.
        description (Optional[str]): Description of the issue.
        log (Optional[str]): Error log associated with the issue.

    Returns:
        dict: Suggested tags for the issue.
    """

    tag_generator = TagGenerator()  
    suggested_tags = tag_generator.generate_tags(
        title=title,
        description=description or "",
        log=log or ""
    )
    
    return {"suggested_tags": suggested_tags}


# GET SPECIFIC ISSUE
@router.get("/{issue_id}", response_model=schemas.IssueOut)
@handle_repo_exceptions
def get_issue(issue_id: int, db: Session = Depends(get_db)):
    """
    Retrieve a specific issue by its ID.

    Args:
        issue_id (int): ID of the issue to retrieve.
        db (Session): Database session.

    Returns:
        schemas.IssueOut: The retrieved issue.

    Raises:
        HTTPException: If the issue is not found.
    """
    return repo_issues.get_issue(db, issue_id)



#LIST ISSUES
@router.get("/", response_model=list[schemas.IssueOut])
@handle_repo_exceptions
def list_issues(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0, description="Number of issues to skip"),
    limit: int = Query(100,ge=0,le=1000, description="Number of issues to return (max 100)"),
    assignee: Optional[str] = Query(None, description="Filter by assignee"),
    priority: Optional[str] = Query(None, description="Filter by priority (low, medium, high)"),
    status: Optional[str] = Query(None, description="Filter by status (open, in_progress, closed)"),
    title: Optional[str] = Query(None, description="Filter by title"),
    project_id: Optional[int] = Query(None, description='Filter by project_id'),
    tags: Optional[str] = Query(None, description="Filter by tags (comma-separated)"),
    tags_match_all: bool = Query(True, description="Return issue with either all or any tag matches")
    
):
    """
    List issues with optional filters.

    Args:
        db (Session): Database session.
        skip (int): Number of issues to skip.
        limit (int): Maximum number of issues to return.
        assignee (Optional[str]): Filter by assignee.
        priority (Optional[str]): Filter by priority.
        status (Optional[str]): Filter by status.
        title (Optional[str]): Filter by title.
        project_id (Optional[int]): Filter by project ID.
        tags (Optional[str]): Filter by tags.
        tags_match_all (bool): Match all or any tags.

    Returns:
        list[schemas.IssueOut]: List of issues matching the filters.
    """
    tag_filter = None
    if tags:
        tag_filter = [tag.strip() for tag in tags.split(",") if tag.strip()]
    return repo_issues.list_issues(db, skip=skip, limit=limit, assignee=assignee, priority=priority, status=status, title=title, project_id=project_id, tags=tag_filter,tags_match_all=tags_match_all)

    
#UPDATE ISSUE
@router.put("/{issue_id}", response_model=schemas.IssueOut)
@handle_repo_exceptions
def update_issue(issue_id: int, data: schemas.IssueUpdate, db: Session = Depends(get_db)):
    """
    Update an existing issue.

    Args:
        issue_id (int): ID of the issue to update.
        data (schemas.IssueUpdate): Updated data for the issue.
        db (Session): Database session.

    Returns:
        schemas.IssueOut: The updated issue.

    Raises:
        HTTPException: If the issue is not found.
    """
    return repo_issues.update_issue(db, issue_id, data)

        
#DELETE ISSUE
@router.delete("/{issue_id}", response_model=dict)
@handle_repo_exceptions
def delete_issue(issue_id: int, db: Session = Depends(get_db)):
    """
    Delete an issue by its ID.

    Args:
        issue_id (int): ID of the issue to delete.
        db (Session): Database session.

    Returns:
        dict: A message confirming the deletion.

    Raises:
        HTTPException: If the issue is not found.
    """
    repo_issues.delete_issue(db, issue_id)
    return {"message": f"Issue {issue_id} deleted successfully"}



# SEARCH ISSUES
@router.get("/search", response_model=List[IssueOut])
@handle_repo_exceptions
def search_issues_api(query: str = Query(..., description="Search query for issues"), db: Session = Depends(get_db)):
    """
    Search for issues by title, description, or tags.

    Args:
        query (str): Search query string.
        db (Session): Database session.

    Returns:
        List[IssueOut]: List of issues matching the search query.
    """
    return repo_issues.search_issues(db, query)


