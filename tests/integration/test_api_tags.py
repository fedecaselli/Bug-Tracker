import pytest
import tempfile
import os
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from app import app
from core.db import Base, get_db
from core.models import Project

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

# --- TESTS ---

def test_create_project_success(file_db):
    # Test creating a project with a valid name
    payload = {"name": "NewProject"}
    response = client.post("/projects/", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "NewProject"

def test_create_project_empty_name(file_db):
    # Test creating a project with an empty name (should fail validation)
    payload = {"name": ""}
    response = client.post("/projects/", json=payload)
    assert response.status_code == 422

def test_create_project_whitespace_name(file_db):
    # Test creating a project with only whitespace in the name (should fail validation)
    payload = {"name": "   "}
    response = client.post("/projects/", json=payload)
    assert response.status_code == 422

def test_create_project_long_name(file_db):
    # Test creating a project with a name longer than allowed (should fail validation)
    payload = {"name": "a" * 201}
    response = client.post("/projects/", json=payload)
    assert response.status_code == 422

def test_create_project_duplicate_name(file_db, project):
    # Test creating a project with a name that already exists (should fail with conflict)
    payload = {"name": project.name}
    response = client.post("/projects/", json=payload)
    assert response.status_code == 409

def test_create_project_unicode_name(file_db):
    # Test creating a project with a unicode name (should succeed)
    payload = {"name": "Проект"}
    response = client.post("/projects/", json=payload)
    assert response.status_code == 200
    assert response.json()["name"] == "Проект"

def test_get_project_by_id(file_db, project):
    # Test retrieving a project by its ID (should succeed)
    response = client.get(f"/projects/{project.project_id}")
    assert response.status_code == 200
    assert response.json()["name"] == project.name

def test_get_project_by_invalid_id(file_db):
    # Test retrieving a project by a non-existent ID (should return 404)
    response = client.get("/projects/999999")
    assert response.status_code == 404

def test_list_projects_empty(file_db):
    # Test listing projects when none exist (should return an empty list)
    response = client.get("/projects/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_list_projects_multiple(file_db):
    # Test listing multiple projects (should return all created projects)
    p1 = Project(name="P1")
    p2 = Project(name="P2")
    file_db.add_all([p1, p2])
    file_db.commit()
    response = client.get("/projects/")
    assert response.status_code == 200
    names = [proj["name"] for proj in response.json()]
    assert "P1" in names and "P2" in names

def test_update_project_success(file_db, project):
    # Test updating a project's name to a new valid name (should succeed)
    payload = {"name": "UpdatedProject"}
    response = client.put(f"/projects/{project.project_id}", json=payload)
    assert response.status_code == 200
    assert response.json()["name"] == "UpdatedProject"

def test_update_project_to_existing_name(file_db, project):
    # Test updating a project's name to another existing project's name (should fail with conflict)
    p2 = Project(name="OtherProject")
    file_db.add(p2)
    file_db.commit()
    payload = {"name": "OtherProject"}
    response = client.put(f"/projects/{project.project_id}", json=payload)
    assert response.status_code == 409

def test_update_project_empty_name(file_db, project):
    # Test updating a project with an empty name (should fail validation)
    payload = {"name": ""}
    response = client.put(f"/projects/{project.project_id}", json=payload)
    assert response.status_code == 422

def test_update_project_long_name(file_db, project):
    # Test updating a project with a name longer than allowed (should fail validation)
    payload = {"name": "a" * 201}
    response = client.put(f"/projects/{project.project_id}", json=payload)
    assert response.status_code == 422

def test_update_nonexistent_project(file_db):
    # Test updating a non-existent project (should return 404)
    payload = {"name": "DoesNotExist"}
    response = client.put("/projects/999999", json=payload)
    assert response.status_code == 404

def test_delete_project_success(file_db, project):
    # Test deleting an existing project (should succeed and project should be gone)
    response = client.delete(f"/projects/{project.project_id}")
    assert response.status_code == 200
    # Verify it's deleted
    response = client.get(f"/projects/{project.project_id}")
    assert response.status_code == 404

def test_delete_project_not_found(file_db):
    # Test deleting a non-existent project (should return 404)
    response = client.delete("/projects/999999")
    assert response.status_code == 404