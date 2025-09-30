from typing import Iterable, List
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from core.models import Tag
from core.schemas import TagCreate, TagUpdate
from core import models
from .exceptions import AlreadyExists, NotFound


#GET TAG BY NAME 
def get_tag_by_name(db: Session, name: str) -> models.Tag | None:
    return db.query(models.Tag).filter(models.Tag.name == name.strip().lower()).first()

def get_or_create_tags(db: Session, tag_names: List[str]) -> List[Tag]:
    #Ensure same tag maps to same IDs
    tags = []
    for tag_name in tag_names:
        tag_name = tag_name.strip().lower()  # Normalize
        if not tag_name:  # skip empty tags
            continue
            
        # Try to find existing tag first
        tag = get_tag_by_name(db, tag_name)
        if not tag:
            # only create if it doesn't exist
            tag = Tag(name=tag_name)
            db.add(tag)
            db.flush()  # Get the ID without committing
        tags.append(tag)
    return tags
    
#GET TAG
def get_tag(db: Session, tag_id: int) -> models.Tag | None:
    #Get tag by ID
    tag = db.query(models.Tag).filter(models.Tag.tag_id == tag_id).first() #return object
    if not tag:
        raise NotFound(f"Tag {tag_id} not found")
    return tag

    
#DELETE TAG
#delete tag from all issues
def delete_tag(db:Session, tag_id: int) -> bool:
    tag = get_tag(db, tag_id)
    db.delete(tag)
    db.commit()
    return True

#UPDATE 
#rename a tag globally
def update_tag(db: Session, tag_id: int, tag_in: TagUpdate) -> models.Tag | None:
    tag = get_tag(db, tag_id)
    
    # Only update fields that were sent
    for field, value in tag_in.model_dump(exclude_unset=True).items():
        if field == "name":
            value = value.strip().lower()
            # Check if new name conflicts with existing tag
            existing = get_tag_by_name(db, value)
            if existing and existing.tag_id != tag_id:
                raise AlreadyExists(f"Tag '{value}' already exists")
        setattr(tag, field, value)
    
    db.commit()
    db.refresh(tag)
    return tag

#LIST
def list_tags(db: Session, skip: int = 0, limit: int = 100) -> list[models.Tag]:
    return db.query(models.Tag).offset(skip).limit(limit).all()

     