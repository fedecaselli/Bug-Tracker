"""
Repository functions for managing tags.

This module provides the core database operations for tags, including:
- Creating, retrieving, updating, and deleting tags.
- Normalizing tag names and handling tag associations with issues.
- Generating tag usage statistics and cleaning up unused tags.
"""

from typing import List
from sqlalchemy.orm import Session
from core.models import Tag, Issue
from core import models
from .exceptions import NotFound
from sqlalchemy import func
from sqlalchemy import text

# NORMALIZE TAG NAME
def _normalize_name(name: str) -> str:
    """Normalize tag name: trim, collapse spaces, lowercase."""
    return ' '.join(name.strip().lower().split())

# GET TAG BY NAME 
def get_tag_by_name(db: Session, name: str) -> models.Tag | None:
    """
    Retrieve a tag by its name.

    Args:
        db (Session): Database session.
        name (str): Name of the tag to retrieve.

    Returns:
        Tag | None: The retrieved tag, or None if it does not exist.
    """
    normalized = _normalize_name(name)
    return db.query(models.Tag).filter(models.Tag.name == normalized).first()


def get_or_create_tags(db: Session, names: List[str]) -> List[Tag]:
    """
    Retrieve or create tags based on a list of names.

    Args:
        db (Session): Database session.
        names (List[str]): List of tag names to retrieve or create.

    Returns:
        List[Tag]: List of tags, including both existing and newly created ones.
    """
    if not names:
        return []
    
    # Normalize all input names and remove duplicates / empty names
    normalized_names = []
    seen = set()
    for name in names:
        normalized = _normalize_name(name)
        if normalized and normalized not in seen:
            normalized_names.append(normalized)
            seen.add(normalized)
    
    if not normalized_names:
        return []
    
    # Query existing tags for all normalized names
    existing_tags = db.query(Tag).filter(Tag.name.in_(normalized_names)).all()
    existing_names = set()
    for tag in existing_tags:
        existing_names.add(tag.name)
        
    
    # Compute which names are missing
    missing_names = []
    for name in normalized_names:
        if name not in existing_names:
            missing_names.append(name)
    
    # Insert missing tags
    new_tags = []
    for name in missing_names:
        tag = Tag(name=name)
        db.add(tag)
        new_tags.append(tag)
    
    if new_tags:
        db.flush()  # Get IDs without committing
    
    # Return all tags (existing and new)
    result = []
    for name in normalized_names:
        tag = None

        # Search in existing tags
        for existing_tag in existing_tags:
            if existing_tag.name == name:
                tag = existing_tag
                break

        # If not found in existing tags, search in new tags
        if not tag:
            for new_tag in new_tags:
                if new_tag.name == name:
                    tag = new_tag
                    break

        # Add the tag to the result if found
        if tag:
            result.append(tag)
    
    return result

def update_tags(db: Session, issue: Issue, names: List[str]) -> Issue:
    """
    Update the tags associated with an issue.

    Args:
        db (Session): Database session.
        issue (Issue): The issue to update tags for.
        names (List[str]): List of tag names to associate with the issue.

    Returns:
        Issue: The updated issue with the new tags.
    """
    tags = get_or_create_tags(db, names)
    issue.tags = tags
    return issue

def remove_tags_with_no_issue(db: Session) -> int:
    """
    Remove tags that are not associated with any issues.

    Args:
        db (Session): Database session.

    Returns:
        int: The number of tags removed.
    """
    # Find tags with no associated issues
    orphaned_tags = db.query(Tag).filter(~Tag.issues.any()).all()
    count = len(orphaned_tags)
    
    for tag in orphaned_tags:
        db.delete(tag)
    
    db.commit()
    return count

def rename_tags_everywhere(db: Session, old_name: str, new_name: str) -> None:
    """
    Rename a tag globally or merge it with an existing tag.

    Args:
        db (Session): Database session.
        old_name (str): The current name of the tag.
        new_name (str): The new name to assign to the tag.

    Raises:
        ValueError: If the tag names are empty after normalization.
        NotFound: If the tag to rename does not exist.
    """

    old_normalized = _normalize_name(old_name)
    new_normalized = _normalize_name(new_name)
    
    if not old_normalized or not new_normalized:
        raise ValueError("Tag names cannot be empty")
    
    # Handle if old and new name are the same
    if old_normalized == new_normalized:
        return  
    
    # Check that tag to rename exists
    old_tag = get_tag_by_name(db, old_normalized)
    if not old_tag:
        raise NotFound(f"Tag '{old_name}' not found")
    
    # Check if new tag already exists
    new_tag = get_tag_by_name(db, new_normalized)
    
    if new_tag:
        # Merge tags: move all issues from old_tag to new_tag
        # Remove issues that already have both tags to avoid constraint violation
        db.execute(
            text("""
                DELETE FROM issue_tags 
                WHERE tag_id = :old_tag_id 
                AND issue_id IN (
                    SELECT issue_id FROM issue_tags WHERE tag_id = :new_tag_id
                )
            """),
            {"old_tag_id": old_tag.tag_id, "new_tag_id": new_tag.tag_id}
        )
        
        # Update remaining associations to point to new tag
        db.execute(
            text("UPDATE issue_tags SET tag_id = :new_tag_id WHERE tag_id = :old_tag_id"),
            {"new_tag_id": new_tag.tag_id, "old_tag_id": old_tag.tag_id}
        )
        
        # Delete old tag
        db.delete(old_tag)
    else:
        # Rename the old tag to new tag name
        old_tag.name = new_normalized
    
    db.commit()

#GET TAG
def get_tag(db: Session, tag_id: int) -> models.Tag:
    """
    Retrieve a tag by its ID.

    Args:
        db (Session): Database session.
        tag_id (int): ID of the tag to retrieve.

    Returns:
        Tag: The retrieved tag.

    Raises:
        NotFound: If the tag does not exist.
    """
    tag = db.query(models.Tag).filter(models.Tag.tag_id == tag_id).first()
    if not tag:
        raise NotFound(f"Tag {tag_id} not found")
    return tag

#DELETE TAG
def delete_tag(db: Session, tag_id: int) -> bool:
    """
    Delete a tag from all issues.

    Args:
        db (Session): Database session.
        tag_id (int): ID of the tag to delete.

    Returns:
        bool: True if the tag was successfully deleted.
    """
    tag = get_tag(db, tag_id)
    db.delete(tag)
    db.commit()
    return True



#LIST
def list_tags(db: Session, skip: int = 0, limit: int = 100) -> list[models.Tag]:
    """
    List all tags with optional pagination.

    Args:
        db (Session): Database session.
        skip (int): Number of tags to skip.
        limit (int): Maximum number of tags to return.

    Returns:
        list[Tag]: List of tags.
    """
    return db.query(models.Tag).offset(skip).limit(limit).all()

#TAG USAGE STATS
def get_tag_usage_stats(db: Session) -> list[dict]:
    """
    Get statistics about tag usage.

    Args:
        db (Session): Database session.

    Returns:
        list[dict]: List of dictionaries containing tag usage statistics.
    """
    results = db.query(models.Tag.tag_id, 
                       models.Tag.name, 
                       func.count(models.Issue.issue_id).label('issue_count')).outerjoin(models.Tag.issues).group_by(models.Tag.tag_id, models.Tag.name).all()
    result = []
    for result_item in results:
        result.append({
            "tag_id": result_item.tag_id,
            "name": result_item.name,
            "issue_count": result_item.issue_count
        })
    return result
    
    