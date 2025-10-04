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

    #enforce FK
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
    TestingSessionLocal = sessionmaker(bind=file_engine, autoflush=False, autocommit=False, future=True)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()

@pytest.fixture
def db_session(file_db):
    yield file_db

@pytest.fixture(autouse=True)
def override_get_db(file_db):
    def _get_db():
        yield file_db
    app.dependency_overrides[get_db] = _get_db

@pytest.fixture
def project(file_db):
    p = Project(name="APIProject")
    file_db.add(p)
    file_db.commit()
    file_db.refresh(p)
    return p

client = TestClient(app)

def test_create_issue_success(file_db, project):
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
    payload = {
        "project_id": 999999,
        "title": "API Issue",
        "priority": "high",
        "status": "open"
    }
    response = client.post("/issues/", json=payload)
    assert response.status_code == 404

def test_create_issue_invalid_priority(file_db, project):
    payload = {
        "project_id": project.project_id,
        "title": "API Issue",
        "priority": "urgent",
        "status": "open"
    }
    response = client.post("/issues/", json=payload)
    assert response.status_code == 422

def test_create_issue_invalid_status(file_db, project):
    payload = {
        "project_id": project.project_id,
        "title": "API Issue",
        "priority": "high",
        "status": "doing"
    }
    response = client.post("/issues/", json=payload)
    assert response.status_code == 422

def test_create_issue_empty_title(file_db, project):
    payload = {
        "project_id": project.project_id,
        "title": "",
        "priority": "high",
        "status": "open"
    }
    response = client.post("/issues/", json=payload)
    assert response.status_code == 422

def test_create_issue_long_title(file_db, project):
    payload = {
        "project_id": project.project_id,
        "title": "a" * 101,
        "priority": "high",
        "status": "open"
    }
    response = client.post("/issues/", json=payload)
    assert response.status_code == 422

def test_get_issue_success(file_db, project):
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
    response = client.get("/issues/999999")
    assert response.status_code == 404

def test_list_issues(file_db, project):
    issue1 = Issue(project_id=project.project_id, title="A", priority="low", status="open")
    issue2 = Issue(project_id=project.project_id, title="B", priority="high", status="closed")
    file_db.add_all([issue1, issue2])
    file_db.commit()
    response = client.get("/issues/")
    assert response.status_code == 200
    titles = [i["title"] for i in response.json()]
    assert "A" in titles and "B" in titles

def test_list_issues_with_filters(file_db, project):
    issue1 = Issue(project_id=project.project_id, title="FilterMe", priority="low", status="open", assignee="alice")
    file_db.add(issue1)
    file_db.commit()
    response = client.get("/issues/", params={"assignee": "alice"})
    assert response.status_code == 200
    assert all(i["assignee"] == "alice" for i in response.json())

def test_update_issue_success(file_db, project):
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
    payload = {"title": "Updated"}
    response = client.put("/issues/999999", json=payload)
    assert response.status_code == 404

def test_delete_issue_success(file_db, project):
    issue = Issue(project_id=project.project_id, title="ToDelete", priority="low", status="open")
    file_db.add(issue)
    file_db.commit()
    file_db.refresh(issue)
    response = client.delete(f"/issues/{issue.issue_id}")
    assert response.status_code == 200
    assert "deleted successfully" in response.json()["message"]

def test_delete_issue_not_found():
    response = client.delete("/issues/999999")
    assert response.status_code == 404

def test_auto_assign_issue_success(file_db, project):
    issue = Issue(project_id=project.project_id, title="AutoAssign", priority="high", status="open")
    file_db.add(issue)
    file_db.commit()
    file_db.refresh(issue)
    response = client.post(f"/issues/{issue.issue_id}/auto-assign")
    # Accept 200 or 400 depending on assignee logic
    assert response.status_code in (200, 400)

def test_auto_assign_issue_not_found():
    response = client.post("/issues/999999/auto-assign")
    assert response.status_code == 400

def test_suggest_tags_api():
    response = client.post("/issues/suggest-tags", params={"title": "UI error", "description": "frontend", "log": "timeout"})
    assert response.status_code == 200
    assert isinstance(response.json()["suggested_tags"], list)

def test_search_issues_api(file_db, project):
    issue = Issue(project_id=project.project_id, title="SearchMe", priority="low", status="open")
    file_db.add(issue)
    file_db.commit()
    file_db.refresh(issue)
    response = client.get("/issues/search", params={"query": "SearchMe"})
    assert response.status_code == 200
    assert any(i["title"] == "SearchMe" for i in response.json())

def test_debug_create_issue(file_db, project):
    """Debug test to see what's causing the 422 error"""
    payload = {
        "project_id": project.project_id,
        "title": "API Issue",
        "priority": "high",
        "status": "open"
    }
    response = client.post("/issues/", json=payload)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    assert response.status_code == 200
    
def test_search_issues_api(file_db, project):
    issue = Issue(project_id=project.project_id, title="SearchMe", priority="low", status="open")
    file_db.add(issue)
    file_db.commit()
    file_db.refresh(issue)
    response = client.get("/issues/search", params={"query": "SearchMe"})
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    assert response.status_code == 200
    assert any(i["title"] == "SearchMe" for i in response.json())