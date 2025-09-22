from typing import Iterable
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from core.models import Tag
from core.schemas import TagCreate, TagUpdate
from core import models


#CREATE TAG
def create_tag(db:Session, data: TagCreate) -> Tag:
    tag = Tag(
        name = data.name
    )
    db.add(tag)
    db.commit()
    db.refresh(tag)
    return tag
    
#GET TAG
def get_tag(db: Session, tag_id: int) -> models.Tag | None:
    #Get tag by ID
    return db.query(models.Tag).filter(models.Tag.tag_id == tag_id).first() #return object
    
#DELETE TAG
def delete_tag(db:Session, tag_id: int) -> bool:
    tag = get_tag(db, tag_id)
    if not tag:
        return False
    
    db.delete(tag)
    db.commit()
    return True

#UPDATE 
def update_tag(db: Session, tag_id: int, tag_in: TagUpdate) -> models.Tag | None:
    tag = get_tag(db, tag_id)
    if not tag:
        return None
    
    # Only update fields that were sent
    for field, value in tag_in.model_dump(exclude_unset=True).items():
        setattr(tag, field, value)
    
    db.commit()
    db.refresh(tag)
    return tag

#LIST
def list_tags(db: Session, skip: int = 0, limit: int = 100) -> list[models.Tag]:
    return db.query(models.Tag).offset(skip).limit(limit).all()

     