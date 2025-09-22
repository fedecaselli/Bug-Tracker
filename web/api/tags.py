from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core import schemas
from core import models
from core.db import get_db
from core.repos import tags as repo_tags

router = APIRouter(prefix="/tags", tags=["tags"])

@router.post("/", response_model=schemas.TagOut)
def create_tag(data: schemas.TagCreate, db: Session = Depends(get_db)):
    return repo_tags.create_tag(db, data)


@router.get("/{tag_id}", response_model=schemas.TagOut)
def get_tag(tag_id: int, db: Session = Depends(get_db)):
    tag = repo_tags.get_tag(db, tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    return tag


@router.get("/", response_model=list[schemas.TagOut])
def list_tags(db: Session = Depends(get_db)):
    return repo_tags.list_tags(db)


@router.put("/{tag_id}", response_model=schemas.TagOut)
def update_tag(tag_id: int, data: schemas.TagUpdate, db: Session = Depends(get_db)):
    tag = repo_tags.update_tag(db, tag_id, data)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    return tag

@router.delete("/{tag_id}", response_model=bool)
def delete_tag(tag_id: int, db: Session = Depends(get_db)):
    return repo_tags.delete_tag(db, tag_id)
