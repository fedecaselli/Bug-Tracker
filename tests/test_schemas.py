import pytest
from pydantic import ValidationError
from core.schemas import (
    TagBase, TagOut, ProjectBase, ProjectCreate, ProjectUpdate, ProjectOut,
    IssueBase, IssueCreate, IssueUpdate, IssueOut
)
from datetime import datetime

# --- TAG SCHEMAS ---

def test_tagbase_valid_name():
    # Valid tag name
    tag = TagBase(name="frontend")
    assert tag.name == "frontend"

def test_tagbase_empty_name():
    # Empty tag name should raise error
    with pytest.raises(ValidationError):
        TagBase(name="")

def test_tagbase_whitespace_name():
    # Whitespace tag name should raise error
    with pytest.raises(ValidationError):
        TagBase(name="   ")

def test_tagbase_long_name():
    # Tag name too long should raise error
    with pytest.raises(ValidationError):
        TagBase(name="a" * 101)

def test_tagbase_normalization():
    # Tag name normalization (trim, lowercase)
    tag = TagBase(name="  FrOnTend  ")
    assert tag.name == "frontend"

def test_tagout_from_orm():
    # ORM conversion for TagOut
    tag = TagOut.model_validate({"tag_id": 1, "name": "backend"})
    assert tag.tag_id == 1
    assert tag.name == "backend"

# --- PROJECT SCHEMAS ---

def test_projectbase_valid_name():
    # Valid project name
    project = ProjectBase(name="MyProject")
    assert project.name == "MyProject"

def test_projectbase_empty_name():
    # Empty project name should raise error
    with pytest.raises(ValidationError):
        ProjectBase(name="")

def test_projectbase_whitespace_name():
    # Whitespace project name should raise error
    with pytest.raises(ValidationError):
        ProjectBase(name="   ")

def test_projectbase_long_name():
    # Project name too long should raise error
    with pytest.raises(ValidationError):
        ProjectBase(name="a" * 201)

def test_projectbase_normalization():
    # Project name normalization (trim)
    project = ProjectBase(name="  MyProject  ")
    assert project.name == "MyProject"

def test_projectcreate_valid():
    # Valid creation
    project = ProjectCreate(name="NewProject")
    assert project.name == "NewProject"

def test_projectupdate_valid():
    # Valid update
    update = ProjectUpdate(name="UpdatedProject")
    assert update.name == "UpdatedProject"

def test_projectupdate_none_name():
    # None name accepted for update
    update = ProjectUpdate(name=None)
    assert update.name is None

def test_projectupdate_long_name():
    # Too long name should raise error
    with pytest.raises(ValidationError):
        ProjectUpdate(name="a" * 201)

def test_projectout_from_orm():
    # ORM conversion for ProjectOut
    project = ProjectOut.model_validate({
        "project_id": 1,
        "name": "TestProject",
        "created_at": datetime.now()
    })
    assert project.project_id == 1
    assert project.name == "TestProject"

# --- ISSUE SCHEMAS ---

def test_issuebase_valid():
    # Valid issue
    issue = IssueBase(
        title="Bug found",
        priority="high",
        status="open"
    )
    assert issue.title == "Bug found"
    assert issue.priority == "high"
    assert issue.status == "open"

def test_issuebase_empty_title():
    # Empty title should raise error
    with pytest.raises(ValidationError):
        IssueBase(title="", priority="high", status="open")

def test_issuebase_long_title():
    # Title too long should raise error
    with pytest.raises(ValidationError):
        IssueBase(title="a" * 101, priority="high", status="open")

def test_issuebase_invalid_priority():
    # Invalid priority should raise error
    with pytest.raises(ValidationError):
        IssueBase(title="Bug", priority="urgent", status="open")

def test_issuebase_invalid_status():
    # Invalid status should raise error
    with pytest.raises(ValidationError):
        IssueBase(title="Bug", priority="high", status="not_a_status")

def test_issuebase_status_default():
    # Status missing defaults to "open"
    issue = IssueBase(title="Bug", priority="high")
    assert issue.status == "open"

def test_issuebase_assignee_optional():
    # Assignee optional
    issue = IssueBase(title="Bug", priority="high", status="open", assignee=None)
    assert issue.assignee is None

def test_issuebase_description_optional():
    # Description/log/summary optional
    issue = IssueBase(title="Bug", priority="high", status="open", description=None, log=None, summary=None)
    assert issue.description is None
    assert issue.log is None
    assert issue.summary is None

def test_issuecreate_valid():
    # Valid creation
    issue = IssueCreate(
        title="Bug",
        priority="high",
        status="open",
        project_id=1,
        tag_names=["frontend", "backend"]
    )
    assert issue.project_id == 1
    assert issue.tag_names == ["frontend", "backend"]

def test_issuecreate_missing_project_id():
    # Missing project_id should raise error
    with pytest.raises(ValidationError):
        IssueCreate(title="Bug", priority="high", status="open")

def test_issuecreate_tag_names_normalization():
    # Tag names normalization
    issue = IssueCreate(
        title="Bug",
        priority="high",
        status="open",
        project_id=1,
        tag_names=["  FrOnTend  ", "BACKEND"]
    )
    assert issue.tag_names == ["frontend", "backend"]

def test_issuecreate_auto_generate_flags():
    # Auto_generate_tags and auto_generate_assignee True/False
    issue = IssueCreate(
        title="Bug",
        priority="high",
        status="open",
        project_id=1,
        auto_generate_tags=True,
        auto_generate_assignee=True
    )
    assert issue.auto_generate_tags is True
    assert issue.auto_generate_assignee is True

def test_issueupdate_partial_update():
    # Partial update
    update = IssueUpdate(title="New Title")
    assert update.title == "New Title"

def test_issueupdate_long_title():
    # Title too long should raise error
    with pytest.raises(ValidationError):
        IssueUpdate(title="a" * 101)

def test_issueupdate_invalid_priority():
    # Invalid priority should raise error
    with pytest.raises(ValidationError):
        IssueUpdate(priority="urgent")

def test_issueupdate_invalid_status():
    # Invalid status should raise error
    with pytest.raises(ValidationError):
        IssueUpdate(status="not_a_status")

def test_issueupdate_tag_names_normalization():
    # Tag names normalization in update
    update = IssueUpdate(tag_names=["  FrOnTend  ", "BACKEND"])
    assert update.tag_names == ["frontend", "backend"]

def test_issueupdate_none_fields():
    # None fields accepted
    update = IssueUpdate(title=None, priority=None, status=None, tag_names=None)
    assert update.title is None
    assert update.priority is None
    assert update.status is None
    assert update.tag_names is None

def test_issueout_from_orm():
    # ORM conversion for IssueOut
    issue = IssueOut.model_validate({
        "issue_id": 1,
        "project_id": 1,
        "title": "Bug",
        "priority": "high",
        "status": "open",
        "created_at": datetime.now(),
        "tags": []
    })
    assert issue.issue_id == 1
    assert issue.project_id == 1
    assert issue.title == "Bug"
    assert isinstance(issue.tags, list)

def test_unicode_names():
    # Unicode in names
    tag = TagBase(name="фронтенд")
    project = ProjectBase(name="Проект")
    issue = IssueBase(title="Ошибка", priority="high", status="open")
    assert tag.name == "фронтенд"
    assert project.name == "Проект"
    assert issue.title == "Ошибка"

def test_special_char_names():
    # Special characters in names
    tag = TagBase(name="front-end!")
    project = ProjectBase(name="My_Project#1")
    issue = IssueBase(title="Bug @ login", priority="high", status="open")
    assert tag.name == "front-end!"
    assert project.name == "My_Project#1"
    assert issue.title == "Bug @ login"

def test_model_config_from_attributes():
    # Model config from_attributes for ORM conversion
    tag = TagOut.model_validate({"tag_id": 1, "name": "backend"})
    project = ProjectOut.model_validate({
        "project_id": 1,
        "name": "TestProject",
        "created_at": datetime.now()
    })
    issue = IssueOut.model_validate({
        "issue_id": 1,
        "project_id": 1,
        "title": "Bug",
        "priority": "high",
        "status": "open",
        "created_at": datetime.now(),
        "tags": []
    })
    assert tag.tag_id == 1
    assert project.project_id == 1
    assert issue.issue_id == 1