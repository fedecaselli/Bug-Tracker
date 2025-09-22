'''
Test to ensure priority accepts low, medium, high & status accepts open, in_progress & closed
'''
import pytest
from core.models import Project, Issue

def make_project(db, name="Project"):
    p = Project(name=name)
    db.add(p)
    db.commit()
    db.refresh(p)
    return p

def test_priority_validator_allows_only_valid_values(db):
    p = make_project(db)

    # Valid 
    ok = Issue(project_id=p.project_id, title="ok", priority="low", status="open")
    db.add(ok)
    db.commit()

    # Invalid case
    with pytest.raises(ValueError):
        Issue(project_id=p.project_id, title="bad", priority="urgent", status="open") #priority can only be low, medium or high

def test_status_validator_allows_only_valid_values(db):
    p = make_project(db)

    # Invalid case 
    with pytest.raises(ValueError):
        Issue(project_id=p.project_id, title="bad", priority="low", status="doing") #status can only be open, in_progress or closed
