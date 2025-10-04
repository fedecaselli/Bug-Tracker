import pytest
import tempfile
import os
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from app import app
from core.db import Base, get_db
from core.models import Project, Issue, Tag

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

@pytest.fixture
def issue(file_db, project):
    i = Issue(project_id=project.project_id, title="Test Issue", priority="low", status="open")
    file_db.add(i)
    file_db.commit()
    file_db.refresh(i)
    return i

@pytest.fixture
def tag(file_db):
    t = Tag(name="bug")
    file_db.add(t)
    file_db.commit()
    file_db.refresh(t)
    return t

client = TestClient(app)

def test_get_tag(file_db, tag):
    response = client.get(f"/tags/{tag.tag_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "bug"

def test_get_tag_not_found(file_db):
    response = client.get("/tags/999999")
    assert response.status_code == 404

def test_list_tags(file_db):
    # Create some tags
    tag1 = Tag(name="bug")
    tag2 = Tag(name="urgent")
    file_db.add_all([tag1, tag2])
    file_db.commit()
    
    response = client.get("/tags/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    names = {tag["name"] for tag in data}
    assert names == {"bug", "urgent"}

def test_list_tags_empty(file_db):
    response = client.get("/tags/")
    assert response.status_code == 200
    assert response.json() == []

def test_list_tags_pagination(file_db):
    # Create multiple tags
    tags = [Tag(name=f"tag{i}") for i in range(5)]
    file_db.add_all(tags)
    file_db.commit()
    
    response = client.get("/tags/?skip=2&limit=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2

def test_list_tags_invalid_pagination(file_db):
    response = client.get("/tags/?skip=-1")
    assert response.status_code == 422
    
    response = client.get("/tags/?limit=0")
    assert response.status_code == 422
    
    response = client.get("/tags/?limit=101")
    assert response.status_code == 422

def test_get_tag_usage_stats(file_db, project):
    # Create issues with tags
    issue1 = Issue(project_id=project.project_id, title="Issue 1", priority="low", status="open")
    issue2 = Issue(project_id=project.project_id, title="Issue 2", priority="low", status="open")
    file_db.add_all([issue1, issue2])
    file_db.commit()
    
    # Add tags to issues
    tag1 = Tag(name="bug")
    tag2 = Tag(name="urgent")
    file_db.add_all([tag1, tag2])
    file_db.commit()
    
    issue1.tags.append(tag1)
    issue2.tags.extend([tag1, tag2])
    file_db.commit()
    
    response = client.get("/tags/stats/usage")
    assert response.status_code == 200
    data = response.json()
    stats_dict = {stat["name"]: stat["issue_count"] for stat in data}
    assert stats_dict["bug"] == 2
    assert stats_dict["urgent"] == 1

def test_get_tag_usage_stats_empty(file_db):
    response = client.get("/tags/stats/usage")
    assert response.status_code == 200
    assert response.json() == []

def test_delete_tag(file_db, tag):
    response = client.delete(f"/tags/{tag.tag_id}")
    assert response.status_code == 200
    assert response.json()["message"] == f"Tag {tag.tag_id} deleted successfully"

def test_delete_tag_not_found(file_db):
    response = client.delete("/tags/999999")
    assert response.status_code == 404

def test_rename_tag(file_db, tag):
    response = client.patch("/tags/rename?old_name=bug&new_name=defect")
    assert response.status_code == 200
    assert response.json()["message"] == "Tag 'bug' renamed to 'defect' across all issues"

def test_rename_tag_not_found(file_db):
    response = client.patch("/tags/rename?old_name=nonexistent&new_name=newtag")
    assert response.status_code == 404

def test_rename_tag_empty_name(file_db, tag):
    response = client.patch("/tags/rename?old_name=bug&new_name=")
    assert response.status_code == 422
    
def test_cleanup_unused_tags(file_db):
    tag = Tag(name="orphan")
    file_db.add(tag)
    file_db.commit()
    response = client.delete("/tags/cleanup")
    print(response.json())  # <-- Add this line
    assert response.status_code == 200

def test_cleanup_no_unused_tags(file_db):
    response = client.delete("/tags/cleanup")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 0
    assert "Cleaned up 0 unused tags" in data["message"]