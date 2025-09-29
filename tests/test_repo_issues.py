"""
Tests for issue repository functions: create, get, update, delete, and list.
"""

import pytest
from core.models import Project
from core.schemas import IssueCreate, IssueUpdate
from core.repos.issues import (
    create_issue,
    get_issue,
    update_issue,
    delete_issue,
    list_issues,
)
from core.repos.exceptions import NotFound

def setup_project(db, name="TestProject"):
    project = Project(name=name)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project

def test_create_and_get_issue(db):
    project = setup_project(db)
    issue = create_issue(db, IssueCreate(
        project_id=project.project_id,
        title="Bug",
        description="desc",
        log="log",
        summary="summary",
        priority="low",
        status="open",
        assignee="Alice"
    ))
    assert issue.title == "Bug"
    fetched = get_issue(db, issue.issue_id)
    assert fetched.issue_id == issue.issue_id

def test_create_issue_invalid_project(db):
    with pytest.raises(NotFound):
        create_issue(db, IssueCreate(
            project_id=999,
            title="Bug",
            description="desc",
            log="log",
            summary="summary",
            priority="low",
            status="open",
            assignee="Alice"
        ))

def test_update_issue(db):
    project = setup_project(db)
    issue = create_issue(db, IssueCreate(
        project_id=project.project_id,
        title="Bug",
        description="desc",
        log="log",
        summary="summary",
        priority="low",
        status="open",
        assignee="Alice"
    ))
    updated = update_issue(db, issue.issue_id, IssueUpdate(title="Fixed", status="closed"))
    assert updated.title == "Fixed"
    assert updated.status == "closed"

def test_delete_issue(db):
    project = setup_project(db)
    issue = create_issue(db, IssueCreate(
        project_id=project.project_id,
        title="Bug",
        description="desc",
        log="log",
        summary="summary",
        priority="low",
        status="open",
        assignee="Alice"
    ))
    assert delete_issue(db, issue.issue_id) is True
    with pytest.raises(NotFound):
        get_issue(db, issue.issue_id)

def test_list_issues(db):
    project = setup_project(db)
    create_issue(db, IssueCreate(
        project_id=project.project_id,
        title="Bug1",
        description="desc",
        log="log",
        summary="summary",
        priority="low",
        status="open",
        assignee="Alice"
    ))
    create_issue(db, IssueCreate(
        project_id=project.project_id,
        title="Bug2",
        description="desc",
        log="log",
        summary="summary",
        priority="medium",
        status="in_progress",
        assignee="Bob"
    ))
    issues = list_issues(db)
    assert len(issues) >= 2
    filtered = list_issues(db, assignee="Alice")
    assert all(i.assignee == "Alice" for i in filtered)