from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from core import schemas
from core import models
from core.db import get_db
from core.repos import tags as repo_tags
from core.repos.exceptions import NotFound

router = APIRouter(prefix="/tags", tags=["tags"])

@router.get("/{tag_id}", response_model=schemas.TagOut)
def get_tag(tag_id: int, db: Session = Depends(get_db)):
    try:
        return repo_tags.get_tag(db, tag_id)
    except NotFound as e:
        raise HTTPException(status_code=404, detail="Tag not found")


@router.get("/", response_model=list[schemas.TagOut])
def list_tags(db: Session = Depends(get_db), 
              skip: int = Query(0, ge=0, description="Number of tags to skip"), 
              limit: int = Query(100, ge=1, le=1000, description="Maximum number of tags to return")):
    return repo_tags.list_tags(db, skip=skip, limit=limit)

#for stats
@router.get("/stats/usage", response_model=list[dict])
def get_tag_usage_stats(db: Session = Depends(get_db)):
    return repo_tags.get_tag_usage_stats(db)


@router.delete("/{tag_id}", response_model=dict)
def delete_tag(tag_id: int, db: Session = Depends(get_db)):
    try:
        repo_tags.delete_tag(db, tag_id)
        return {"message": f"Tag {tag_id} deleted successfully"}
    except NotFound as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/rename", response_model=dict)
def rename_tag(
    old_name: str = Query(..., description="Current tag name"),
    new_name: str = Query(..., description="New tag name"),
    db: Session = Depends(get_db)
):
    try:
        repo_tags.rename_tags_everywhere(db, old_name, new_name)
        return {"message": f"Tag '{old_name}' renamed to '{new_name}' across all issues"}
    except NotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    
@router.post("/cleanup", response_model=dict)
def cleanup_unused_tags(db: Session = Depends(get_db)):
    count = repo_tags.remove_tags_with_no_issue(db)
    return {"message": f"Cleaned up {count} unused tags", "count": count}

