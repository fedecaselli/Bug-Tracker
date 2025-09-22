from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core import schemas
from core import models
from core.db import get_db
from core.repos import issues as repo_issues

router = APIRouter(prefix="/issues", tags=["issues"])

@router.post("/", response_model=schemas.IssueOut)
def create_issue(data: schemas.IssueCreate, db: Session = Depends(get_db)):
    return repo_issues.create_issue(db, data)


@router.get("/{issue_id}", response_model=schemas.IssueOut)
def get_issue(issue_id: int, db: Session = Depends(get_db)):
    issue = repo_issues.get_issue(db, issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    return issue


@router.get("/", response_model=list[schemas.IssueOut])
def list_issues(db: Session = Depends(get_db)):
    return repo_issues.list_issues(db)


@router.put("/{issue_id}", response_model=schemas.IssueOut)
def update_issue(issue_id: int, data: schemas.IssueUpdate, db: Session = Depends(get_db)):
    issue = repo_issues.update_issue(db, issue_id, data)
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    return issue


@router.delete("/{issue_id}", response_model=bool)
def delete_issue(issue_id: int, db: Session = Depends(get_db)):
    return repo_issues.delete_issue(db, issue_id)
