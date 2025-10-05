"""
Unit tests for SQLAlchemy ORM models: Project, Issue, Tag, and their relationships.
"""

import pytest
from sqlalchemy.exc import IntegrityError, DataError
from core.models import Project, Issue, Tag, issue_tags
from sqlalchemy.orm import Session

# --- PROJECT MODEL TESTS ---

def test_create_project_valid(db: Session):
    # Create project with valid name
    project = Project(name="Alpha")
    db.add(project)
    db.commit()
    db.refresh(project)
    assert project.project_id is not None
    assert project.name == "Alpha"

def test_create_project_duplicate_name(db: Session):
    # Create project with duplicate name (should fail)
    project1 = Project(name="Beta")
    db.add(project1)
    db.commit()
    project2 = Project(name="Beta")
    db.add(project2)
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()

def test_create_project_empty_name(db: Session):
    # Create project with empty name (should fail)
    project = Project(name="")
    db.add(project)
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()

def test_create_project_long_name(db: Session):
    # Create project with name exceeding 200 chars (should fail)
    project = Project(name="a" * 201)
    db.add(project)
    with pytest.raises(IntegrityError):  
        db.commit()
    db.rollback()

def test_project_has_multiple_issues(db: Session):
    # Project can have multiple issues
    project = Project(name="Gamma")
    db.add(project)
    db.commit()
    db.refresh(project)
    issue1 = Issue(title="Bug1", priority="high", status="open", project_id=project.project_id)
    issue2 = Issue(title="Bug2", priority="low", status="open", project_id=project.project_id)
    db.add_all([issue1, issue2])
    db.commit()
    assert len(project.issues) == 2

def test_project_cascade_delete_issues(db: Session):
    # Deleting a project cascades and deletes its issues
    project = Project(name="Delta")
    db.add(project)
    db.commit()
    db.refresh(project)
    issue = Issue(title="Bug", priority="high", status="open", project_id=project.project_id)
    db.add(issue)
    db.commit()
    db.delete(project)
    db.commit()
    assert db.query(Issue).filter_by(project_id=project.project_id).count() == 0

def test_project_created_at_timestamp(db: Session):
    # Project created_at is set on creation
    project = Project(name="Epsilon")
    db.add(project)
    db.commit()
    db.refresh(project)
    assert project.created_at is not None

# --- ISSUE MODEL TESTS ---

def test_create_issue_valid(db: Session):
    # Create issue with valid data
    project = Project(name="Zeta")
    db.add(project)
    db.commit()
    db.refresh(project)
    issue = Issue(title="Bug", priority="high", status="open", project_id=project.project_id)
    db.add(issue)
    db.commit()
    db.refresh(issue)
    assert issue.issue_id is not None

def test_create_issue_invalid_priority(db: Session):
    # Create issue with invalid priority (should fail)
    project = Project(name="Eta")
    db.add(project)
    db.commit()
    db.refresh(project)
    issue = Issue(title="Bug", priority="urgent", status="open", project_id=project.project_id)
    db.add(issue)
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()

def test_create_issue_invalid_status(db: Session):
    # Create issue with invalid status (should fail)
    project = Project(name="Theta")
    db.add(project)
    db.commit()
    db.refresh(project)
    issue = Issue(title="Bug", priority="high", status="not_a_status", project_id=project.project_id)
    db.add(issue)
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()

def test_create_issue_empty_title(db: Session):
    # Create issue with empty title (should fail)
    project = Project(name="Iota")
    db.add(project)
    db.commit()
    db.refresh(project)
    issue = Issue(title="", priority="high", status="open", project_id=project.project_id)
    db.add(issue)
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()

def test_create_issue_long_title(db: Session):
    # Create issue with title exceeding 100 chars (should fail)
    project = Project(name="Kappa")
    db.add(project)
    db.commit()
    db.refresh(project)
    issue = Issue(title="a" * 101, priority="high", status="open", project_id=project.project_id)
    db.add(issue)
    with pytest.raises(IntegrityError):  # <-- Change from DataError to IntegrityError
        db.commit()
    db.rollback()


def test_create_issue_missing_project_id(db: Session):
    # Create issue with missing project_id (should fail)
    issue = Issue(title="Bug", priority="high", status="open")
    db.add(issue)
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()

def test_issue_optional_fields(db: Session):
    # Create issue with optional fields as None
    project = Project(name="Lambda")
    db.add(project)
    db.commit()
    db.refresh(project)
    issue = Issue(title="Bug", priority="high", status="open", project_id=project.project_id,
                  description=None, log=None, summary=None, assignee=None)
    db.add(issue)
    db.commit()
    db.refresh(issue)
    assert issue.description is None
    assert issue.log is None
    assert issue.summary is None
    assert issue.assignee is None

def test_issue_belongs_to_project(db: Session):
    # Issue belongs to a project
    project = Project(name="Mu")
    db.add(project)
    db.commit()
    db.refresh(project)
    issue = Issue(title="Bug", priority="high", status="open", project_id=project.project_id)
    db.add(issue)
    db.commit()
    db.refresh(issue)
    assert issue.project == project

def test_issue_created_at_and_updated_at(db: Session):
    # Issue created_at is set, updated_at is None on creation
    project = Project(name="Nu")
    db.add(project)
    db.commit()
    db.refresh(project)
    issue = Issue(title="Bug", priority="high", status="open", project_id=project.project_id)
    db.add(issue)
    db.commit()
    db.refresh(issue)
    assert issue.created_at is not None
    assert issue.updated_at is None

def test_issue_has_multiple_tags(db: Session):
    # Issue can have multiple tags
    project = Project(name="Xi")
    db.add(project)
    db.commit()
    db.refresh(project)
    tag1 = Tag(name="frontend")
    tag2 = Tag(name="backend")
    db.add_all([tag1, tag2])
    db.commit()
    db.refresh(tag1)
    db.refresh(tag2)
    issue = Issue(title="Bug", priority="high", status="open", project_id=project.project_id)
    issue.tags.extend([tag1, tag2])
    db.add(issue)
    db.commit()
    db.refresh(issue)
    assert set(t.name for t in issue.tags) == {"frontend", "backend"}

def test_issue_delete_removes_tag_associations(db: Session):
    # Deleting an issue removes its tag associations
    project = Project(name="Omicron")
    db.add(project)
    db.commit()
    db.refresh(project)
    tag = Tag(name="devops")
    db.add(tag)
    db.commit()
    db.refresh(tag)
    issue = Issue(title="Bug", priority="high", status="open", project_id=project.project_id)
    issue.tags.append(tag)
    db.add(issue)
    db.commit()
    db.refresh(issue)
    db.delete(issue)
    db.commit()
    assert db.query(issue_tags).filter_by(tag_id=tag.tag_id).count() == 0

def test_issue_priority_constraint(db: Session):
    # Priority constraint enforced at DB level
    project = Project(name="Pi")
    db.add(project)
    db.commit()
    db.refresh(project)
    issue = Issue(title="Bug", priority="medium", status="open", project_id=project.project_id)
    db.add(issue)
    db.commit()
    db.refresh(issue)
    assert issue.priority == "medium"

def test_issue_status_constraint(db: Session):
    # Status constraint enforced at DB level
    project = Project(name="Rho")
    db.add(project)
    db.commit()
    db.refresh(project)
    issue = Issue(title="Bug", priority="high", status="closed", project_id=project.project_id)
    db.add(issue)
    db.commit()
    db.refresh(issue)
    assert issue.status == "closed"

# --- TAG MODEL TESTS ---

def test_create_tag_valid(db: Session):
    # Create tag with valid name
    tag = Tag(name="api")
    db.add(tag)
    db.commit()
    db.refresh(tag)
    assert tag.tag_id is not None
    assert tag.name == "api"

def test_create_tag_duplicate_name(db: Session):
    # Create tag with duplicate name (should fail)
    tag1 = Tag(name="infra")
    db.add(tag1)
    db.commit()
    tag2 = Tag(name="infra")
    db.add(tag2)
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()

def test_create_tag_empty_name(db: Session):
    # Create tag with empty name (should fail)
    tag = Tag(name="")
    db.add(tag)
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()

def test_create_tag_long_name(db: Session):
    # Create tag with name exceeding 100 chars (should fail)
    tag = Tag(name="a" * 101)
    db.add(tag)
    with pytest.raises(IntegrityError):  
        db.commit()
    db.rollback()

def test_tag_assigned_to_multiple_issues(db: Session):
    # Tag can be assigned to multiple issues
    project = Project(name="Sigma")
    db.add(project)
    db.commit()
    db.refresh(project)
    tag = Tag(name="security")
    db.add(tag)
    db.commit()
    db.refresh(tag)
    issue1 = Issue(title="Bug1", priority="high", status="open", project_id=project.project_id)
    issue2 = Issue(title="Bug2", priority="low", status="open", project_id=project.project_id)
    issue1.tags.append(tag)
    issue2.tags.append(tag)
    db.add_all([issue1, issue2])
    db.commit()
    assert tag in issue1.tags and tag in issue2.tags

def test_tag_delete_removes_associations(db: Session):
    # Deleting a tag removes its associations from issues
    project = Project(name="Tau")
    db.add(project)
    db.commit()
    db.refresh(project)
    tag = Tag(name="ops")
    db.add(tag)
    db.commit()
    db.refresh(tag)
    issue = Issue(title="Bug", priority="high", status="open", project_id=project.project_id)
    issue.tags.append(tag)
    db.add(issue)
    db.commit()
    db.refresh(issue)
    db.delete(tag)
    db.commit()
    assert tag not in issue.tags

# --- MANY-TO-MANY TESTS ---

def test_issue_tags_many_to_many(db: Session):
    # Assign multiple tags to a single issue and single tag to multiple issues
    project = Project(name="Upsilon")
    db.add(project)
    db.commit()
    db.refresh(project)
    tag1 = Tag(name="frontend")
    tag2 = Tag(name="backend")
    db.add_all([tag1, tag2])
    db.commit()
    db.refresh(tag1)
    db.refresh(tag2)
    issue1 = Issue(title="Bug1", priority="high", status="open", project_id=project.project_id)
    issue2 = Issue(title="Bug2", priority="low", status="open", project_id=project.project_id)
    issue1.tags.extend([tag1, tag2])
    issue2.tags.append(tag1)
    db.add_all([issue1, issue2])
    db.commit()
    assert tag1 in issue1.tags and tag2 in issue1.tags and tag1 in issue2.tags

def test_unicode_and_special_char_names(db: Session):
    # Unicode and special characters in names
    project = Project(name="Проект")
    db.add(project)
    db.commit()
    db.refresh(project)
    tag = Tag(name="фронтенд!")
    db.add(tag)
    db.commit()
    db.refresh(tag)
    issue = Issue(title="Ошибка @ вход", priority="high", status="open", project_id=project.project_id)
    db.add(issue)
    db.commit()
    db.refresh(issue)
    issue.tags.append(tag)
    db.commit()
    assert tag in issue.tags


def test_create_issue_invalid_project_id(db: Session):
    # Attempt to create issue with non-existent project_id (should fail)
    issue = Issue(title="Bug", priority="high", status="open", project_id=999999)
    db.add(issue)
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()

def test_assign_duplicate_tag_to_issue(db: Session):
    # Attempt to assign same tag multiple times to an issue (should not duplicate)
    project = Project(name="Chi")
    db.add(project)
    db.commit()
    db.refresh(project)
    tag = Tag(name="repeat")
    db.add(tag)
    db.commit()
    db.refresh(tag)
    issue = Issue(title="Bug", priority="high", status="open", project_id=project.project_id)
    issue.tags.append(tag)
    issue.tags.append(tag)
    db.add(issue)
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()