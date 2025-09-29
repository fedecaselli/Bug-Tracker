from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from fastapi import Query

from core import schemas
from core import models
from core.db import get_db
from core.repos import issues as repo_issues
from core.repos.exceptions import NotFound

router = APIRouter(prefix="/issues", tags=["issues"])

@router.post("/", response_model=schemas.IssueOut)
def create_issue(data: schemas.IssueCreate, db: Session = Depends(get_db)):
    return repo_issues.create_issue(db, data)


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
    skip: int = 0,
    limit: int = 100,
    assignee: Optional[str] = Query(None, description="Filter by assignee"),
    priority: Optional[str] = Query(None, description="Filter by priority (low, medium, high)"),
    status: Optional[str] = Query(None, description="Filter by status (open, in_progress, closed)"),
    title: Optional[str] = Query(None, description="Filter by title"),
):
    return repo_issues.list_issues(db, skip=skip, limit=limit, assignee=assignee, priority=priority, status=status, title=title)


@router.put("/{issue_id}", response_model=schemas.IssueOut)
def update_issue(issue_id: int, data: schemas.IssueUpdate, db: Session = Depends(get_db)):
    try:
        return repo_issues.update_issue(db, issue_id, data)
    except NotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
        

@router.delete("/{issue_id}", response_model=bool)
def delete_issue(issue_id: int, db: Session = Depends(get_db)):
    return repo_issues.delete_issue(db, issue_id)


