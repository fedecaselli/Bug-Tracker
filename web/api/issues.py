from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from fastapi import Query

from core import schemas
from core import models
from core.db import get_db
from core.repos import issues as repo_issues
from core.repos.exceptions import NotFound, AlreadyExists

router = APIRouter(prefix="/issues", tags=["issues"])

@router.post("/", response_model=schemas.IssueOut)
def create_issue(data: schemas.IssueCreate, db: Session = Depends(get_db)):
    try:
        return repo_issues.create_issue(db, data)
    except NotFound as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{issue_id}", response_model=schemas.IssueOut)
def get_issue(issue_id: int, db: Session = Depends(get_db)):
    try:
        return repo_issues.get_issue(db, issue_id)
    except NotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
        

'''
@router.get("/", response_model=list[schemas.IssueOut])
def list_issues(db: Session = Depends(get_db)):
    return repo_issues.list_issues(db)
'''


@router.get("/", response_model=list[schemas.IssueOut])
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
    try: 
        tag_filter = None
        if tags:
            tag_filter = [tag.strip() for tag in tags.split(",") if tag.strip()]
        return repo_issues.list_issues(db, skip=skip, limit=limit, assignee=assignee, priority=priority, status=status, title=title, project_id=project_id, tags=tag_filter,tags_match_all=tags_match_all)
    except NotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    

@router.put("/{issue_id}", response_model=schemas.IssueOut)
def update_issue(issue_id: int, data: schemas.IssueUpdate, db: Session = Depends(get_db)):
    try:
        return repo_issues.update_issue(db, issue_id, data)
    except NotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
        

@router.delete("/{issue_id}", response_model=dict)
def delete_issue(issue_id: int, db: Session = Depends(get_db)):
    try:
        repo_issues.delete_issue(db, issue_id)
        return {"message": f"Issue {issue_id} deleted successfully"}
    except NotFound as e:
        raise HTTPException(status_code=404, detail=str(e))


