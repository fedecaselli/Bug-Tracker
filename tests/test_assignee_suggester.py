import pytest
from sqlalchemy.orm import Session
from core.models import Project, Issue, Tag
from core.automation.assignee_suggestion import AssigneeSuggester

def setup_project(db: Session, name="TestProject"):
    project = Project(name=name)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project

def setup_issue(db: Session, project, title, assignee=None, status="open", priority="high", tags=None):
    issue = Issue(
        project_id=project.project_id,
        title=title,
        priority=priority,
        status=status,
        assignee=assignee
    )
    db.add(issue)
    db.commit()
    db.refresh(issue)
    if tags:
        for tag_name in tags:
            tag = db.query(Tag).filter_by(name=tag_name).first()
            if not tag:
                tag = Tag(name=tag_name)
                db.add(tag)
                db.commit()
                db.refresh(tag)
            issue.tags.append(tag)
        db.commit()
        db.refresh(issue)
    return issue

@pytest.fixture
def suggester():
    return AssigneeSuggester()

def test_no_assignees_available(db, suggester):
    # No assignees available
    project = setup_project(db)
    result = suggester.suggest_assignee(db, ["bug"], "open", "high")
    assert result is None

def test_no_tags_provided(db, suggester):
    # No tags provided
    project = setup_project(db)
    setup_issue(db, project, "Issue 1", assignee="alice@example.com")
    result = suggester.suggest_assignee(db, [], "open", "high")
    assert result is None

def test_status_not_open(db, suggester):
    # Status not "open"
    project = setup_project(db)
    setup_issue(db, project, "Issue 1", assignee="alice", status="closed")
    result = suggester.suggest_assignee(db, ["bug"], "closed", "high")
    assert result is None

def test_priority_not_high(db, suggester):
    # Priority not "high"
    project = setup_project(db)
    setup_issue(db, project, "Issue 1", assignee="alice@example.com", priority="low")
    result = suggester.suggest_assignee(db, ["bug"], "open", "low")
    assert result is None

def test_assignee_with_highest_success_rate(db, suggester):
    # Assignee with highest success rate for tags
    project = setup_project(db)
    setup_issue(db, project, "Bug 1", assignee="alice@example.com", status="closed", tags=["bug"])
    setup_issue(db, project, "Bug 2", assignee="alice@example.com", status="closed", tags=["bug"])
    setup_issue(db, project, "Bug 3", assignee="bob@example.com", status="closed", tags=["bug"])
    setup_issue(db, project, "Bug 4", assignee="bob@example.com", status="open", tags=["bug"])
    result = suggester.suggest_assignee(db, ["bug"], "open", "high")
    assert result == "alice@example.com"

def test_assignee_with_lowest_workload(db, suggester):
    # Assignee with lowest workload
    project = setup_project(db)
    setup_issue(db, project, "Bug 1", assignee="alice@example.com", status="closed", tags=["bug"])
    setup_issue(db, project, "Bug 2", assignee="bob@example.com", status="closed", tags=["bug"])
    setup_issue(db, project, "Bug 3", assignee="alice@example.com", status="open", tags=["bug"])
    result = suggester.suggest_assignee(db, ["bug"], "open", "high")
    assert result == "bob@example.com"

def test_assignee_with_no_relevant_tag_associations(db, suggester):
    # Assignee with no relevant tag associations
    project = setup_project(db)
    setup_issue(db, project, "Feature 1", assignee="alice@example.com", status="closed", tags=["feature"])
    result = suggester.suggest_assignee(db, ["bug"], "open", "high")
    assert result is None

def test_multiple_assignees_tiebreaker_by_workload(db, suggester):
    # Multiple assignees, tie-breaker by workload
    project = setup_project(db)
    setup_issue(db, project, "Bug 1", assignee="alice@example.com", status="closed", tags=["bug"])
    setup_issue(db, project, "Bug 2", assignee="bob@example.com", status="closed", tags=["bug"])
    setup_issue(db, project, "Bug 3", assignee="alice@example.com", status="open", tags=["bug"])
    setup_issue(db, project, "Bug 4", assignee="bob@example.com", status="open", tags=["feature"])
    result = suggester.suggest_assignee(db, ["bug"], "open", "high")
    assert result == "bob@example.com"

def test_assignee_with_zero_total_tag_count(db, suggester):
    # Assignee with zero total tag count
    project = setup_project(db)
    setup_issue(db, project, "Feature 1", assignee="alice@example.com", status="closed", tags=["feature"])
    result = suggester.suggest_assignee(db, ["bug"], "open", "high")
    assert result is None

def test_assignee_suggestion_with_mixed_tags(db, suggester):
    # Assignee suggestion with mixed tags
    project = setup_project(db)
    setup_issue(db, project, "Bug 1", assignee="alice@example.com", status="closed", tags=["bug"])
    setup_issue(db, project, "Feature 1", assignee="alice@example.com", status="closed", tags=["feature"])
    setup_issue(db, project, "Bug 2", assignee="bob@example.com", status="closed", tags=["bug"])
    result = suggester.suggest_assignee(db, ["bug", "feature"], "open", "high")
    assert result == "alice@example.com"

def test_auto_assign_sets_assignee(db, suggester):
    # Auto-assign actually sets assignee
    project = setup_project(db)
    issue = setup_issue(db, project, "Bug 1", assignee=None, status="open", priority="high", tags=["bug"])
    setup_issue(db, project, "Bug 2", assignee="alice", status="closed", tags=["bug"])
    success = suggester.auto_assign(db, issue.issue_id)
    db.refresh(issue)
    assert success is True
    assert issue.assignee == "alice"

def test_auto_assign_returns_false_if_no_suitable_assignee(db, suggester):
    # Auto-assign returns False if no suitable assignee
    project = setup_project(db)
    issue = setup_issue(db, project, "Bug 1", assignee=None, status="open", priority="high", tags=["bug"])
    success = suggester.auto_assign(db, issue.issue_id)
    assert success is False