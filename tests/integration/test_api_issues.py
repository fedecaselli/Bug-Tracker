"""
Unit tests for FastAPI issues endpoints.
"""

import pytest
import tempfile
import os
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from app import app
from core.db import Base, get_db
from core.models import Project, Issue

# Create a separate engine fixture for this test file only
@pytest.fixture(scope="function")   
def file_engine():
    # Create a temporary file database that can be shared across threads
    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_db.close()
    
    eng = create_engine(f"sqlite:///{temp_db.name}", future=True)

    # Enforce foreign key constraints for SQLite
    @event.listens_for(eng, "connect")
    def set_sqlite_pragma(dbapi_conn, _):
        cur = dbapi_conn.cursor()
        cur.execute("PRAGMA foreign_keys=ON")
        cur.close()

    Base.metadata.create_all(bind=eng)
    yield eng
    
    # Clean up the temporary database file
    try:
        os.unlink(temp_db.name)
    except FileNotFoundError:
        pass

@pytest.fixture()
def file_db(file_engine):
    # Provide a SQLAlchemy session bound to the temporary file database
    TestingSessionLocal = sessionmaker(bind=file_engine, autoflush=False, autocommit=False, future=True)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()

@pytest.fixture
def db_session(file_db):
    # Alias for file_db fixture
    yield file_db

@pytest.fixture(autouse=True)
def override_get_db(file_db):
    # Override FastAPI's get_db dependency to use the test database
    def _get_db():
        yield file_db
    app.dependency_overrides[get_db] = _get_db

@pytest.fixture
def project(file_db):
    # Create and persist a sample project for tests
    p = Project(name="APIProject")
    file_db.add(p)
    file_db.commit()
    file_db.refresh(p)
    return p

client = TestClient(app)

def test_create_issue_success(file_db, project):
    # Test creating an issue with valid data (should succeed)
    payload = {
        "project_id": project.project_id,
        "title": "API Issue",
        "priority": "high",
        "status": "open"
    }
    response = client.post("/issues/", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "API Issue"
    assert data["project_id"] == project.project_id

def test_create_issue_invalid_project(file_db):
    # Test creating an issue with a non-existent project (should return 404)
    payload = {
        "project_id": 999999,
        "title": "API Issue",
        "priority": "high",
        "status": "open"
    }
    response = client.post("/issues/", json=payload)
    assert response.status_code == 404

def test_create_issue_invalid_priority(file_db, project):
    # Test creating an issue with an invalid priority (should fail validation)
    payload = {
        "project_id": project.project_id,
        "title": "API Issue",
        "priority": "urgent",
        "status": "open"
    }
    response = client.post("/issues/", json=payload)
    assert response.status_code == 422

def test_create_issue_invalid_status(file_db, project):
    # Test creating an issue with an invalid status (should fail validation)
    payload = {
        "project_id": project.project_id,
        "title": "API Issue",
        "priority": "high",
        "status": "doing"
    }
    response = client.post("/issues/", json=payload)
    assert response.status_code == 422

def test_create_issue_empty_title(file_db, project):
    # Test creating an issue with an empty title (should fail validation)
    payload = {
        "project_id": project.project_id,
        "title": "",
        "priority": "high",
        "status": "open"
    }
    response = client.post("/issues/", json=payload)
    assert response.status_code == 422

def test_create_issue_long_title(file_db, project):
    # Test creating an issue with a title longer than allowed (should fail validation)
    payload = {
        "project_id": project.project_id,
        "title": "a" * 101,
        "priority": "high",
        "status": "open"
    }
    response = client.post("/issues/", json=payload)
    assert response.status_code == 422

def test_get_issue_success(file_db, project):
    # Test retrieving an issue by its ID (should succeed)
    issue = Issue(
        project_id=project.project_id,
        title="GetMe",
        priority="low",
        status="open"
    )
    file_db.add(issue)
    file_db.commit()
    file_db.refresh(issue)
    response = client.get(f"/issues/{issue.issue_id}")
    assert response.status_code == 200
    assert response.json()["title"] == "GetMe"

def test_get_issue_not_found():
    # Test retrieving an issue by a non-existent ID (should return 404)
    response = client.get("/issues/999999")
    assert response.status_code == 404

def test_list_issues(file_db, project):
    # Test listing all issues (should return all created issues)
    issue1 = Issue(project_id=project.project_id, title="A", priority="low", status="open")
    issue2 = Issue(project_id=project.project_id, title="B", priority="high", status="closed")
    file_db.add_all([issue1, issue2])
    file_db.commit()
    response = client.get("/issues/")
    assert response.status_code == 200
    titles = [i["title"] for i in response.json()]
    assert "A" in titles and "B" in titles

def test_list_issues_with_filters(file_db, project):
    # Test listing issues with filters (should return only matching issues)
    issue1 = Issue(project_id=project.project_id, title="FilterMe", priority="low", status="open", assignee="alice")
    file_db.add(issue1)
    file_db.commit()
    response = client.get("/issues/", params={"assignee": "alice"})
    assert response.status_code == 200
    assert all(i["assignee"] == "alice" for i in response.json())

def test_update_issue_success(file_db, project):
    # Test updating an issue with valid data (should succeed)
    issue = Issue(project_id=project.project_id, title="ToUpdate", priority="low", status="open")
    file_db.add(issue)
    file_db.commit()
    file_db.refresh(issue)
    payload = {
        "title": "Updated",
        "priority": "medium",
        "status": "closed"
    }
    response = client.put(f"/issues/{issue.issue_id}", json=payload)
    assert response.status_code == 200
    assert response.json()["title"] == "Updated"
    assert response.json()["priority"] == "medium"
    assert response.json()["status"] == "closed"

def test_update_issue_not_found():
    # Test updating a non-existent issue (should return 404)
    payload = {"title": "Updated"}
    response = client.put("/issues/999999", json=payload)
    assert response.status_code == 404

def test_delete_issue_success(file_db, project):
    # Test deleting an existing issue (should succeed and issue should be gone)
    issue = Issue(project_id=project.project_id, title="ToDelete", priority="low", status="open")
    file_db.add(issue)
    file_db.commit()
    file_db.refresh(issue)
    response = client.delete(f"/issues/{issue.issue_id}")
    assert response.status_code == 200
    assert "deleted successfully" in response.json()["message"]

def test_delete_issue_not_found():
    # Test deleting a non-existent issue (should return 404)
    response = client.delete("/issues/999999")
    assert response.status_code == 404

def test_auto_assign_issue_success(file_db, project):
    # Test auto-assigning an issue to the best assignee (should succeed or return 400/404 if no assignee found)
    issue = Issue(project_id=project.project_id, title="AutoAssign", priority="high", status="open")
    file_db.add(issue)
    file_db.commit()
    file_db.refresh(issue)
    response = client.post(f"/issues/{issue.issue_id}/auto-assign")
    # Accept 200, 400, or 404 depending on assignee logic
    assert response.status_code in (200, 400, 404)

def test_auto_assign_issue_not_found():
    # Test auto-assigning a non-existent issue (should return 404)
    response = client.post("/issues/999999/auto-assign")
    assert response.status_code == 404

def test_suggest_tags_api():
    # Test suggesting tags for an issue using the AI-based endpoint (should return a list of tags)
    response = client.post("/issues/suggest-tags", params={"title": "UI error", "description": "frontend", "log": "timeout"})
    assert response.status_code == 200
    assert isinstance(response.json()["suggested_tags"], list)

def test_search_issues_api(file_db, project):
    # Test searching for issues by title substring (should return matching issues)
    issue = Issue(project_id=project.project_id, title="SearchMe", priority="low", status="open")
    file_db.add(issue)
    file_db.commit()
    file_db.refresh(issue)
    response = client.get("/issues/search", params={"query": "SearchMe"})
    assert response.status_code == 200
    assert any(i["title"] == "SearchMe" for i in response.json())

def test_debug_create_issue(file_db, project):
    # Debug test to see what's causing the 422 error (should succeed)
    payload = {
        "project_id": project.project_id,
        "title": "API Issue",
        "priority": "high",
        "status": "open"
    }
    response = client.post("/issues/", json=payload)
    assert response.status_code == 200
    
def test_search_issues_api(file_db, project):
    # Test searching for issues by title substring (should return matching issues)
    issue = Issue(project_id=project.project_id, title="SearchMe", priority="low", status="open")
    file_db.add(issue)
    file_db.commit()
    file_db.refresh(issue)
    response = client.get("/issues/search", params={"query": "SearchMe"})
    assert response.status_code == 200
    assert any(i["title"] == "SearchMe" for i in response.json())
    
def test_create_duplicate_issue(db, project):
    # Test that creating a duplicate issue raises AlreadyExists (should return 409)
    issue1_data = {
        "project_id": project.project_id,
        "title": "Bug Report",
        "description": "Critical error",
        "priority": "high",
        "status": "open",
        "assignee": "john@example.com",
        "tag_names": ["bug", "critical"]
    }
    
    response1 = client.post("/issues/", json=issue1_data)
    assert response1.status_code == 200
    
    # Try to create identical issue
    response2 = client.post("/issues/", json=issue1_data)
    assert response2.status_code == 409
    assert "identical issue already exists" in response2.json()["detail"]

def test_create_duplicate_issue_different_case(db, project):
    # Test that issues with same content but different case are considered duplicates
    issue1_data = {
        "project_id": project.project_id,
        "title": "Bug Report",
        "description": "Critical error",
        "priority": "high",
        "status": "open"
    }
    
    response1 = client.post("/issues/", json=issue1_data)
    assert response1.status_code == 200
    
    # Try to create issue with different case in description
    issue2_data = issue1_data.copy()
    issue2_data["description"] = "CRITICAL ERROR"  # Different case
    
    response2 = client.post("/issues/", json=issue2_data)
    assert response2.status_code == 200  # Should succeed - different content
    
    # Try to create truly identical issue
    response3 = client.post("/issues/", json=issue1_data)
    assert response3.status_code == 409

def test_update_issue_to_duplicate(db, project):
    # Test that updating an issue to match another issue raises AlreadyExists (should return 409)
    issue1_data = {
        "project_id": project.project_id,
        "title": "Bug Report 1",
        "description": "First error",
        "priority": "high",
        "status": "open"
    }
    
    issue2_data = {
        "project_id": project.project_id,
        "title": "Bug Report 2", 
        "description": "Second error",
        "priority": "medium",
        "status": "open"
    }
    
    # Create both issues
    response1 = client.post("/issues/", json=issue1_data)
    response2 = client.post("/issues/", json=issue2_data)
    assert response1.status_code == 200
    assert response2.status_code == 200
    
    issue1_id = response1.json()["issue_id"]
    
    # Try to update issue1 to match issue2
    update_data = {
        "title": "Bug Report 2",
        "description": "Second error", 
        "priority": "medium"
    }
    
    response = client.put(f"/issues/{issue1_id}", json=update_data)
    assert response.status_code == 409
    assert "identical issue already exists" in response.json()["detail"]

def test_update_issue_same_data(db, project):
    # Test that updating an issue with the same data doesn't raise error (should succeed)
    issue_data = {
        "project_id": project.project_id,
        "title": "Bug Report",
        "description": "Critical error",
        "priority": "high",
        "status": "open"
    }
    
    response = client.post("/issues/", json=issue_data)
    assert response.status_code == 200
    issue_id = response.json()["issue_id"]
    
    # Update with same data
    response = client.put(f"/issues/{issue_id}", json=issue_data)
    assert response.status_code == 200
    assert response.json()["issue_id"] == issue_id

def test_update_issue_partial_duplicate(db, project):
    # Test that partial updates that create duplicates are caught (should return 409)
    issue1_data = {
        "project_id": project.project_id,
        "title": "Bug Report",
        "description": "Critical error",
        "priority": "high",
        "status": "open",
        "assignee": "john@example.com"
    }
    
    response1 = client.post("/issues/", json=issue1_data)
    assert response1.status_code == 200
    
    # Create second issue with different assignee
    issue2_data = issue1_data.copy()
    issue2_data["assignee"] = "jane@example.com"
    
    response2 = client.post("/issues/", json=issue2_data)
    assert response2.status_code == 200
    issue2_id = response2.json()["issue_id"]
    
    # Try to update issue2 to match issue1 (change assignee)
    update_data = {"assignee": "john@example.com"}
    
    response = client.put(f"/issues/{issue2_id}", json=update_data)
    assert response.status_code == 409
    assert "identical issue already exists" in response.json()["detail"]

def test_duplicate_issue_different_projects(db):
    # Test that identical issues in different projects are allowed (should succeed)
    project1_data = {"name": "Project 1"}
    project2_data = {"name": "Project 2"}
    
    response1 = client.post("/projects/", json=project1_data)
    response2 = client.post("/projects/", json=project2_data)
    assert response1.status_code == 200
    assert response2.status_code == 200
    
    project1_id = response1.json()["project_id"]
    project2_id = response2.json()["project_id"]
    
    # Create identical issues in different projects
    issue_data = {
        "title": "Bug Report",
        "description": "Critical error",
        "priority": "high",
        "status": "open"
    }
    
    issue1_data = {**issue_data, "project_id": project1_id}
    issue2_data = {**issue_data, "project_id": project2_id}
    
    response1 = client.post("/issues/", json=issue1_data)
    response2 = client.post("/issues/", json=issue2_data)
    assert response1.status_code == 200
    assert response2.status_code == 200

def test_duplicate_issue_with_tags(db, project):
    # Test that issues with identical tags are considered duplicates (should return 409)
    issue1_data = {
        "project_id": project.project_id,
        "title": "Bug Report",
        "description": "Critical error",
        "priority": "high",
        "status": "open",
        "tag_names": ["bug", "critical", "urgent"]
    }
    
    response1 = client.post("/issues/", json=issue1_data)
    assert response1.status_code == 200
    
    # Try to create identical issue with same tags
    response2 = client.post("/issues/", json=issue1_data)
    assert response2.status_code == 409
    
    # Try to create issue with different tags (should succeed)
    issue3_data = issue1_data.copy()
    issue3_data["tag_names"] = ["bug", "critical"]  # Different tags
    
    response3 = client.post("/issues/", json=issue3_data)
    assert response3.status_code == 200
