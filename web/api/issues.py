from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from fastapi import Query

from core import schemas
from core import models
from core.db import get_db
from core.repos import issues as repo_issues
from core.repos.exceptions import NotFound, AlreadyExists
from core.automation.tag_generator import TagGenerator  
from core.automation.assignee_suggestion import AssigneeSuggester  

router = APIRouter(prefix="/issues", tags=["issues"])

#CREATE ISSUE
@router.post("/", response_model=schemas.IssueOut)
def create_issue(data: schemas.IssueCreate, db: Session = Depends(get_db)):
    try:
        return repo_issues.create_issue(db, data)
    except NotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    
# AUTO-ASSIGN TASK TO ASSIGNEE
@router.post("/{issue_id}/auto-assign", response_model=dict)
def auto_assign_issue(issue_id: int,db: Session = Depends(get_db)):
    try:
        suggester = AssigneeSuggester()
        success = suggester.auto_assign(db, issue_id)
        if success:
            issue_after = repo_issues.get_issue(db, issue_id)
            return {"assigned_to": issue_after.assignee}
        else:
            raise HTTPException(status_code=400, detail="Could not automatically assign")

    except NotFound as e:
        raise HTTPException(status_code=404, detail=str(e))


#SUGGEST TAGS
@router.post("/suggest-tags", response_model=dict)
def suggest_tags_api(
    title: str = Query(..., description="Issue title"),
    description: Optional[str] = Query(None, description="Issue description"),
    log: Optional[str] = Query(None, description="Error log")
):
    """Get AI tag suggestions for issue content"""
    
    tag_generator = TagGenerator()  
    suggested_tags = tag_generator.generate_tags(
        title=title,
        description=description or "",
        log=log or ""
    )
    
    return {"suggested_tags": suggested_tags}


#GET SPECIFIC ISSUE
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

#LIST ISSUES
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
    
#UPDATE ISSUE
@router.put("/{issue_id}", response_model=schemas.IssueOut)
def update_issue(issue_id: int, data: schemas.IssueUpdate, db: Session = Depends(get_db)):
    try:
        return repo_issues.update_issue(db, issue_id, data)
    except NotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
        
#DELETE ISSUE
@router.delete("/{issue_id}", response_model=dict)
def delete_issue(issue_id: int, db: Session = Depends(get_db)):
    try:
        repo_issues.delete_issue(db, issue_id)
        return {"message": f"Issue {issue_id} deleted successfully"}
    except NotFound as e:
        raise HTTPException(status_code=404, detail=str(e))


