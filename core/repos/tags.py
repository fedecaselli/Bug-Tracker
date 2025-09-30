from typing import Iterable, List
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import text
from core.models import Tag, Issue
from core.schemas import TagUpdate
from core import models
from .exceptions import AlreadyExists, NotFound

def _normalize_name(name: str) -> str:
    """Normalize tag name: trim, collapse spaces, lowercase."""
    return ' '.join(name.strip().lower().split())

#GET TAG BY NAME 
def get_tag_by_name(db: Session, name: str) -> models.Tag | None:
    normalized = _normalize_name(name)
    return db.query(models.Tag).filter(models.Tag.name == normalized).first()


def get_or_create_tags(db: Session, names: List[str]) -> List[Tag]:
    """
    Goal: return Tag objects for given names, creating missing ones.
    Normalize input (trim, collapse spaces, lowercase).
    Query existing tags for those normalized names.
    Compute which names are missing; insert them.
    """
    if not names:
        return []
    
    # Normalize all input names and remove duplicates/empty
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
    existing_names = {tag.name for tag in existing_tags}
    
    # Compute which names are missing
    missing_names = [name for name in normalized_names if name not in existing_names]
    
    # Insert missing tags
    new_tags = []
    for name in missing_names:
        tag = Tag(name=name)
        db.add(tag)
        new_tags.append(tag)
    
    if new_tags:
        db.flush()  # Get IDs without committing
    
    # Return all tags (existing + new) in the order requested
    result = []
    for name in normalized_names:
        # Find in existing tags first
        tag = next((t for t in existing_tags if t.name == name), None)
        if not tag:
            # Find in new tags
            tag = next((t for t in new_tags if t.name == name), None)
        if tag:
            result.append(tag)
    
    return result

def update_tags(db: Session, issue: Issue, names: List[str]) -> Issue:
    """
    Goal: set the issue's tags to exactly the provided list (ONLY THAT ISSUE'S TAGS).
    Resolve tags = get_or_create_tags(...).
    Assign: issue.tags = tags (SQLAlchemy will diff the association table).
    Do not delete Tag rows here.
    """
    # Get or create all requested tags
    tags = get_or_create_tags(db, names)
    
    # Assign to issue - SQLAlchemy will handle the association table diff
    issue.tags = tags
    
    # Commit is handled by caller
    return issue

def remove_tags_with_no_issue(db: Session) -> int:
    """
    Goal: garbage-collect orphan tags (no issues referencing them).
    Delete those Tag rows. Return count removed.
    """
    # Find tags with no associated issues
    orphaned_tags = db.query(Tag).filter(~Tag.issues.any()).all()
    count = len(orphaned_tags)
    
    # Delete orphaned tags
    for tag in orphaned_tags:
        db.delete(tag)
    
    db.commit()
    return count

def rename_tags_everywhere(db: Session, old_name: str, new_name: str) -> None:
    """
    Goal: rename a tag everywhere.
    Normalize both names.
    Find old = Tag(old_name); if not found, no-op / raise.
    If new tag exists: Merge by updating issue_tags association.
    Else: Update old.name.
    All issues update automatically because they reference the tag row.
    """
    old_normalized = _normalize_name(old_name)
    new_normalized = _normalize_name(new_name)
    
    if not old_normalized or not new_normalized:
        raise ValueError("Tag names cannot be empty")
    
    if old_normalized == new_normalized:
        return  # No-op if same name
    
    # Find old tag
    old_tag = db.query(Tag).filter(Tag.name == old_normalized).first()
    if not old_tag:
        raise NotFound(f"Tag '{old_name}' not found")
    
    # Check if new tag already exists
    new_tag = db.query(Tag).filter(Tag.name == new_normalized).first()
    
    if new_tag:
        # Merge: update issue_tags to point from old.tag_id → new.tag_id
        db.execute(
            text("UPDATE issue_tags SET tag_id = :new_tag_id WHERE tag_id = :old_tag_id"),
            {"new_tag_id": new_tag.tag_id, "old_tag_id": old_tag.tag_id}
        )
        # Delete old tag
        db.delete(old_tag)
    else:
        # Update old tag's name
        old_tag.name = new_normalized
    
    db.commit()

#GET TAG
def get_tag(db: Session, tag_id: int) -> models.Tag:
    """Get tag by ID."""
    tag = db.query(models.Tag).filter(models.Tag.tag_id == tag_id).first()
    if not tag:
        raise NotFound(f"Tag {tag_id} not found")
    return tag

#DELETE TAG
def delete_tag(db: Session, tag_id: int) -> bool:
    """Delete tag from all issues."""
    tag = get_tag(db, tag_id)
    db.delete(tag)
    db.commit()
    return True



#LIST
def list_tags(db: Session, skip: int = 0, limit: int = 100) -> list[models.Tag]:
    return db.query(models.Tag).offset(skip).limit(limit).all()

#TAG USAGE STATS
def get_tag_usage_stats(db: Session) -> list[dict]:
    """Get statistics about tag usage."""
    from sqlalchemy import func
    
    results = db.query(
        models.Tag.tag_id,
        models.Tag.name,
        func.count(models.Issue.issue_id).label('issue_count')
    ).outerjoin(
        models.Tag.issues
    ).group_by(
        models.Tag.tag_id, models.Tag.name
    ).all()
    
    return [
        {
            "tag_id": result.tag_id,
            "name": result.name,
            "issue_count": result.issue_count
        }
        for result in results
    ]