"""
API Endpoints for Managing Tags in the Bug Tracker Application

This module provides the API endpoints for creating, retrieving, updating, deleting, and managing tags. It also includes endpoints for 
retrieving tag usage statistics and cleaning up unused tags.

Key Features:
- Retrieve a specific tag by its ID.
- List all tags with optional pagination.
- Retrieve tag usage statistics.
- Delete a tag by its ID.
- Rename a tag across all issues.
- Clean up unused tags.
"""


from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from core import schemas
from core.db import get_db
from core.logging import get_logger
from core.repos import tags as repo_tags
from core.repos.exceptions import NotFound, AlreadyExists
from pydantic import ValidationError
from web.api.exceptions import handle_repo_exceptions


router = APIRouter(prefix="/tags", tags=["tags"])
logger = get_logger(__name__)



# LIST ALL TAGS
@router.get("/", response_model=list[schemas.TagOut])
@handle_repo_exceptions
def list_tags(db: Session = Depends(get_db), 
              skip: int = Query(0, ge=0, description="Number of tags to skip"), 
              limit: int = Query(100, ge=1, le=1000, description="Maximum number of tags to return")):
    """
    List all tags with optional pagination.

    Args:
        db (Session): Database session.
        skip (int): Number of tags to skip.
        limit (int): Maximum number of tags to return.

    Returns:
        list[schemas.TagOut]: List of tags.
        
    Raises:
        404: If no tags are found.
        409: If a conflict occurs.
        422: If validation fails.
    """
    return repo_tags.list_tags(db, skip=skip, limit=limit)


# CLEAN UP UNUSED TAGS
@router.delete("/cleanup", response_model=dict)
@handle_repo_exceptions
def cleanup_unused_tags(db: Session = Depends(get_db)):
    """
    Remove all tags that are not associated with any issues.

    Args:
        db (Session): Database session.

    Returns:
        dict: A message confirming the cleanup and the number of tags removed.
    
    Raises:
        404: If no tags are found.
        409: If a conflict occurs.
        422: If validation fails.
    """
    count = repo_tags.remove_tags_with_no_issue(db)
    logger.info("Cleaned up %s unused tags", count)
    return {"message": f"Cleaned up {count} unused tags", "count": count}
    


# RENAME TAG 
@router.patch("/rename", response_model=dict)
@handle_repo_exceptions
def rename_tag(
    old_name: str = Query(..., description="Current tag name"),
    new_name: str = Query(..., description="New tag name"),
    db: Session = Depends(get_db)
):
    """
    Rename a tag across all issues.

    Args:
        old_name (str): Current name of the tag.
        new_name (str): New name for the tag.
        db (Session): Database session.

    Returns:
        dict: A message confirming the renaming.

    Raises:
        404: If no tags are found.
        409: If a conflict occurs.
        422: If validation fails.
    """
    repo_tags.rename_tags_everywhere(db, old_name, new_name)
    logger.info("Renamed tag '%s' to '%s'", old_name, new_name)
    return {"message": f"Tag '{old_name}' renamed to '{new_name}' across all issues"}

# GET TAG USAGE STATISTICS
@router.get("/stats/usage", response_model=list[dict])
@handle_repo_exceptions
def get_tag_usage_stats(db: Session = Depends(get_db)):
    """
    Retrieve usage statistics for all tags.

    Args:
        db (Session): Database session.

    Returns:
        list[dict]: List of tag usage statistics.
    
    Raises:
        404: If no tags are found.
        409: If a conflict occurs.
        422: If validation fails.
    """
    return repo_tags.get_tag_usage_stats(db)
    
# DELETE TAG 
@router.delete("/{tag_id}", response_model=dict)
@handle_repo_exceptions
def delete_tag(tag_id: int, db: Session = Depends(get_db)):
    """
    Delete a tag by its ID.

    Args:
        tag_id (int): ID of the tag to delete.
        db (Session): Database session.

    Returns:
        dict: A message confirming the deletion.

    Raises:
        404: If no tags are found.
        409: If a conflict occurs.
        422: If validation fails.
    """
    repo_tags.delete_tag(db, tag_id)
    logger.info("Deleted tag id=%s", tag_id)
    return {"message": f"Tag {tag_id} deleted successfully"}

# GET TAG BY ID
@router.get("/{tag_id}", response_model=schemas.TagOut)
@handle_repo_exceptions
def get_tag(tag_id: int, db: Session = Depends(get_db)):
    """
    Retrieve a specific tag by its ID.

    Args:
        tag_id (int): ID of the tag to retrieve.
        db (Session): Database session.

    Returns:
        schemas.TagOut: The retrieved tag.

    Raises:
        404: If no tags are found.
        409: If a conflict occurs.
        422: If validation fails.
    """
    return repo_tags.get_tag(db, tag_id)
