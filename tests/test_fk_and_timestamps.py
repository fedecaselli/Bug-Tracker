'''
Test to ensure deleting a project deletes the associated issues and that updated_at starts as NULL on insert, and gets a timestamp when the row is updated.
'''
from core.models import Project, Issue

#Check that deleting a project deletes the associated issues
def test_cascade_delete_project_removes_issues(db):
    proj = Project(name="Trial1")
    db.add(proj); db.commit(); db.refresh(proj)

    issue = Issue(project_id=proj.project_id,title="Issue1",priority="medium",status="open")
    db.add(issue); db.commit()
    issue_id = issue.issue_id

    # delete project
    db.delete(proj); db.commit()

    # issue should be gone because of CASCADE
    assert db.get(Issue, issue_id) is None

#Check that updated_at starts as NULL on insert, and gets a timestamp when the row is updated.
def test_updated_at_is_null_then_set_on_update(db):
    proj = Project(name="Trial2")
    db.add(proj); db.commit(); db.refresh(proj)

    issue = Issue(project_id=proj.project_id,title="Initial",priority="low",status="open")
    db.add(issue); db.commit(); db.refresh(issue)
    assert issue.updated_at is None  # Check that it is NULL at insert

    # Update something
    issue.title = "Updated"
    db.commit(); db.refresh(issue)
    assert issue.updated_at is not None  # Check that it set by onupdate
