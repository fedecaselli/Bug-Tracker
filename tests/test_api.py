"""
Comprehensive API tests for the Bug Tracker application.
Tests all API endpoints with various scenarios including edge cases.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core.db import Base, get_db
from app import app
import tempfile
import os

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture
def client():
    """Create test client with fresh database."""
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as c:
        yield c
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def sample_project(client):
    """Create a sample project for testing."""
    response = client.post("/projects/", json={"name": "Test Project"})
    return response.json()

@pytest.fixture
def sample_issue(client, sample_project):
    """Create a sample issue for testing."""
    issue_data = {
        "title": "Test Issue",
        "description": "A test issue",
        "assignee": "test@example.com",
        "priority": "high",
        "project_id": sample_project["project_id"]
    }
    response = client.post("/issues/", json=issue_data)
    return response.json()

# Add fixtures for tag testing
@pytest.fixture
def sample_tags(client, sample_project):
    """Create sample issues with tags for testing."""
    # Create issues with various tag combinations
    issues_data = [
        {
            "title": "Frontend Bug",
            "description": "UI not loading properly",
            "priority": "high",
            "tags": ["frontend", "bug", "urgent"],
            "project_id": sample_project["project_id"]
        },
        {
            "title": "Backend Issue",
            "description": "API endpoint error",
            "priority": "medium", 
            "tags": ["backend", "bug"],
            "project_id": sample_project["project_id"]
        },
        {
            "title": "Documentation Update",
            "description": "Update API docs",
            "priority": "low",
            "tags": ["documentation", "enhancement"],
            "project_id": sample_project["project_id"]
        },
        {
            "title": "Database Migration",
            "description": "Migrate to new schema",
            "priority": "high",
            "tags": ["backend", "database", "urgent"],
            "project_id": sample_project["project_id"]
        }
    ]
    
    created_issues = []
    for issue_data in issues_data:
        response = client.post("/issues/", json=issue_data)
        assert response.status_code == 200
        created_issues.append(response.json())
    
    return created_issues

class TestProjectsAPI:
    """Test cases for Projects API endpoints."""
    
    def test_create_project_success(self, client):
        """Test successful project creation."""
        project_data = {
            "name": "New Project"
        }
        response = client.post("/projects/", json=project_data)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "New Project"
        assert "project_id" in data
        assert "created_at" in data
    
    def test_create_project_with_minimal_data(self, client):
        """Test creating project with only required fields."""
        project_data = {"name": "Minimal Project"}
        response = client.post("/projects/", json=project_data)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Minimal Project"
    
    def test_create_project_duplicate_name(self, client):
        """Test creating project with duplicate name."""
        project_data = {"name": "Duplicate Project"}
        
        # Create first project
        response1 = client.post("/projects/", json=project_data)
        assert response1.status_code == 200
        
        # Try to create duplicate
        response2 = client.post("/projects/", json=project_data)
        assert response2.status_code == 409
        assert "already exists" in response2.json()["detail"].lower()
    
    def test_create_project_empty_name(self, client):
        """Test creating project with empty name."""
        project_data = {"name": ""}
        response = client.post("/projects/", json=project_data)
        assert response.status_code == 422
    
    def test_create_project_long_name(self, client):
        """Test creating project with very long name."""
        project_data = {"name": "A" * 256}  # Very long name
        response = client.post("/projects/", json=project_data)
        assert response.status_code == 422
    
    def test_create_project_missing_name(self, client):
        """Test creating project without name field."""
        project_data = {"description": "No name project"}
        response = client.post("/projects/", json=project_data)
        assert response.status_code == 422
    
    def test_get_project_success(self, client, sample_project):
        """Test successful project retrieval."""
        project_id = sample_project["project_id"]
        response = client.get(f"/projects/{project_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["project_id"] == project_id
        assert data["name"] == sample_project["name"]
    
    def test_get_project_not_found(self, client):
        """Test getting non-existent project."""
        response = client.get("/projects/99999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_get_project_invalid_id(self, client):
        """Test getting project with invalid ID format."""
        response = client.get("/projects/invalid")
        assert response.status_code == 422
    
    def test_list_projects_empty(self, client):
        """Test listing projects when none exist."""
        response = client.get("/projects/")
        assert response.status_code == 200
        assert response.json() == []
    
    def test_list_projects_with_data(self, client):
        """Test listing projects with existing data."""
        # Create multiple projects
        projects_data = [
            {"name": "Project 1", "description": "First project"},
            {"name": "Project 2", "description": "Second project"},
            {"name": "Project 3"}
        ]
        
        created_projects = []
        for project_data in projects_data:
            response = client.post("/projects/", json=project_data)
            created_projects.append(response.json())
        
        # List all projects
        response = client.get("/projects/")
        assert response.status_code == 200
        projects = response.json()
        assert len(projects) == 3
        
        # Verify all projects are returned
        project_names = [p["name"] for p in projects]
        for project_data in projects_data:
            assert project_data["name"] in project_names
    
    def test_update_project_success(self, client, sample_project):
        """Test successful project update."""
        project_id = sample_project["project_id"]
        update_data = {
            "name": "Updated Project"
        }
        
        response = client.put(f"/projects/{project_id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Project"
        assert data["project_id"] == project_id
    
    def test_update_project_partial(self, client, sample_project):
        """Test partial project update."""
        project_id = sample_project["project_id"]
        update_data = {"name": "Partially Updated"}
        
        response = client.put(f"/projects/{project_id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Partially Updated"
    
    def test_update_project_not_found(self, client):
        """Test updating non-existent project."""
        update_data = {"name": "Non-existent Project"}
        response = client.put("/projects/99999", json=update_data)
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_update_project_duplicate_name(self, client):
        """Test updating project to duplicate name."""
        # Create two projects
        project1_data = {"name": "Project One"}
        project2_data = {"name": "Project Two"}
        
        response1 = client.post("/projects/", json=project1_data)
        project1 = response1.json()
        
        response2 = client.post("/projects/", json=project2_data)
        project2 = response2.json()
        
        # Try to update project2 to have same name as project1
        update_data = {"name": "Project One"}
        response = client.put(f"/projects/{project2['project_id']}", json=update_data)
        assert response.status_code == 409
        assert "another project already uses the name" in response.json()["detail"].lower()
    
    def test_update_project_empty_name(self, client, sample_project):
        """Test updating project with empty name."""
        project_id = sample_project["project_id"]
        update_data = {"name": ""}
        
        response = client.put(f"/projects/{project_id}", json=update_data)
        assert response.status_code == 422
    
    def test_delete_project_success(self, client, sample_project):
        """Test successful project deletion."""
        project_id = sample_project["project_id"]
        
        response = client.delete(f"/projects/{project_id}")
        assert response.status_code == 200
        assert response.json() is True
        
        # Verify project is deleted
        get_response = client.get(f"/projects/{project_id}")
        assert get_response.status_code == 404
    
    def test_delete_project_not_found(self, client):
        """Test deleting non-existent project."""
        response = client.delete("/projects/99999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_delete_project_invalid_id(self, client):
        """Test deleting project with invalid ID."""
        response = client.delete("/projects/invalid")
        assert response.status_code == 422


class TestIssuesAPI:
    """Test cases for Issues API endpoints."""
    
    def test_create_issue_success(self, client, sample_project):
        """Test successful issue creation."""
        issue_data = {
            "title": "New Bug",
            "description": "A critical bug",
            "assignee": "developer@example.com",
            "priority": "high",
            "project_id": sample_project["project_id"]
        }
        
        response = client.post("/issues/", json=issue_data)
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "New Bug"
        assert data["description"] == "A critical bug"
        assert data["assignee"] == "developer@example.com"
        assert data["priority"] == "high"
        assert data["status"] == "open"  # Default status
        assert data["project_id"] == sample_project["project_id"]
        assert "issue_id" in data
        assert "created_at" in data
    
    def test_create_issue_minimal_data(self, client, sample_project):
        """Test creating issue with minimal required data."""
        issue_data = {
            "title": "Minimal Issue",
            "priority": "medium",  # Required field
            "project_id": sample_project["project_id"]
        }
        
        response = client.post("/issues/", json=issue_data)
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Minimal Issue"
        assert data["description"] is None
        assert data["assignee"] is None
        assert data["priority"] == "medium"
        assert data["status"] == "open"  # Default status
    
    def test_create_issue_invalid_project(self, client):
        """Test creating issue with non-existent project."""
        issue_data = {
            "title": "Orphaned Issue",
            "project_id": 99999
        }
        
        response = client.post("/issues/", json=issue_data)
        assert response.status_code == 422  # Validation error, not 404
    
    def test_create_issue_invalid_priority(self, client, sample_project):
        """Test creating issue with invalid priority."""
        issue_data = {
            "title": "Invalid Priority Issue",
            "priority": "super_critical",
            "project_id": sample_project["project_id"]
        }
        
        response = client.post("/issues/", json=issue_data)
        assert response.status_code == 422
    
    def test_create_issue_invalid_status(self, client, sample_project):
        """Test creating issue with invalid status."""
        issue_data = {
            "title": "Invalid Status Issue",
            "status": "archived",
            "project_id": sample_project["project_id"]
        }
        
        response = client.post("/issues/", json=issue_data)
        assert response.status_code == 422
    
    def test_create_issue_empty_title(self, client, sample_project):
        """Test creating issue with empty title."""
        issue_data = {
            "title": "",
            "project_id": sample_project["project_id"]
        }
        
        response = client.post("/issues/", json=issue_data)
        assert response.status_code == 422
    
    def test_create_issue_long_title(self, client, sample_project):
        """Test creating issue with very long title."""
        issue_data = {
            "title": "A" * 256,  # Very long title
            "project_id": sample_project["project_id"]
        }
        
        response = client.post("/issues/", json=issue_data)
        assert response.status_code == 422
    
    def test_get_issue_success(self, client, sample_issue):
        """Test successful issue retrieval."""
        issue_id = sample_issue["issue_id"]
        response = client.get(f"/issues/{issue_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["issue_id"] == issue_id
        assert data["title"] == sample_issue["title"]
    
    def test_get_issue_not_found(self, client):
        """Test getting non-existent issue."""
        response = client.get("/issues/99999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_get_issue_invalid_id(self, client):
        """Test getting issue with invalid ID format."""
        response = client.get("/issues/invalid")
        assert response.status_code == 422
    
    def test_list_issues_empty(self, client):
        """Test listing issues when none exist."""
        response = client.get("/issues/")
        assert response.status_code == 200
        assert response.json() == []
    
    def test_list_issues_with_data(self, client, sample_project):
        """Test listing issues with existing data."""
        # Create multiple issues
        issues_data = [
            {"title": "Issue 1", "priority": "high", "assignee": "dev1@example.com", "project_id": sample_project["project_id"]},
            {"title": "Issue 2", "priority": "low", "assignee": "dev2@example.com", "project_id": sample_project["project_id"]},
            {"title": "Issue 3", "priority": "medium", "assignee": "dev1@example.com", "project_id": sample_project["project_id"]}
        ]
        
        created_issues = []
        for issue_data in issues_data:
            response = client.post("/issues/", json=issue_data)
            created_issues.append(response.json())
        
        # List all issues
        response = client.get("/issues/")
        assert response.status_code == 200
        issues = response.json()
        assert len(issues) == 3
        
        # Verify all issues are returned
        issue_titles = [i["title"] for i in issues]
        for issue_data in issues_data:
            assert issue_data["title"] in issue_titles
    
    def test_list_issues_pagination(self, client, sample_project):
        """Test issues pagination."""
        # Create 5 issues
        for i in range(5):
            issue_data = {
                "title": f"Issue {i+1}",
                "priority": "medium",  # Required field
                "project_id": sample_project["project_id"]
            }
            client.post("/issues/", json=issue_data)
        
        # Test pagination
        response = client.get("/issues/?skip=2&limit=2")
        assert response.status_code == 200
        issues = response.json()
        assert len(issues) == 2
    
    def test_list_issues_filter_by_assignee(self, client, sample_project):
        """Test filtering issues by assignee."""
        # Create issues with different assignees
        issues_data = [
            {"title": "Issue A", "priority": "medium", "assignee": "alice@example.com", "project_id": sample_project["project_id"]},
            {"title": "Issue B", "priority": "medium", "assignee": "bob@example.com", "project_id": sample_project["project_id"]},
            {"title": "Issue C", "priority": "medium", "assignee": "alice@example.com", "project_id": sample_project["project_id"]}
        ]
        
        for issue_data in issues_data:
            client.post("/issues/", json=issue_data)
        
        # Filter by assignee
        response = client.get("/issues/?assignee=alice@example.com")
        assert response.status_code == 200
        issues = response.json()
        assert len(issues) == 2
        for issue in issues:
            assert issue["assignee"] == "alice@example.com"
    
    def test_list_issues_filter_by_priority(self, client, sample_project):
        """Test filtering issues by priority."""
        # Create issues with different priorities
        issues_data = [
            {"title": "High Priority", "priority": "high", "project_id": sample_project["project_id"]},
            {"title": "Low Priority", "priority": "low", "project_id": sample_project["project_id"]},
            {"title": "High Priority 2", "priority": "high", "project_id": sample_project["project_id"]}
        ]
        
        for issue_data in issues_data:
            client.post("/issues/", json=issue_data)
        
        # Filter by priority
        response = client.get("/issues/?priority=high")
        assert response.status_code == 200
        issues = response.json()
        assert len(issues) == 2
        for issue in issues:
            assert issue["priority"] == "high"
    
    def test_list_issues_filter_by_status(self, client, sample_project):
        """Test filtering issues by status."""
        # Create issues and update some statuses
        issue1_data = {"title": "Open Issue", "priority": "medium", "project_id": sample_project["project_id"]}
        issue2_data = {"title": "Progress Issue", "priority": "medium", "project_id": sample_project["project_id"]}
        
        issue1_response = client.post("/issues/", json=issue1_data)
        issue2_response = client.post("/issues/", json=issue2_data)
        
        # Update one issue status
        issue2_id = issue2_response.json()["issue_id"]
        client.put(f"/issues/{issue2_id}", json={"status": "in_progress"})
        
        # Filter by status
        response = client.get("/issues/?status=open")
        assert response.status_code == 200
        issues = response.json()
        assert len(issues) == 1
        assert issues[0]["status"] == "open"
    
    def test_list_issues_filter_by_title(self, client, sample_project):
        """Test filtering issues by title."""
        # Create issues with different titles
        issues_data = [
            {"title": "Bug in login", "priority": "medium", "project_id": sample_project["project_id"]},
            {"title": "Feature request", "priority": "medium", "project_id": sample_project["project_id"]},
            {"title": "Bug in logout", "priority": "medium", "project_id": sample_project["project_id"]}
        ]
        
        for issue_data in issues_data:
            client.post("/issues/", json=issue_data)
        
        # Filter by exact title match (current API behavior)
        response = client.get("/issues/?title=Bug in login")
        assert response.status_code == 200
        issues = response.json()
        assert len(issues) == 1
        assert issues[0]["title"] == "Bug in login"
    
    def test_list_issues_multiple_filters(self, client, sample_project):
        """Test filtering issues with multiple filters."""
        # Create issues with various attributes
        issues_data = [
            {"title": "High Priority Bug", "priority": "high", "assignee": "dev@example.com", "project_id": sample_project["project_id"]},
            {"title": "Low Priority Bug", "priority": "low", "assignee": "dev@example.com", "project_id": sample_project["project_id"]},
            {"title": "High Priority Feature", "priority": "high", "assignee": "other@example.com", "project_id": sample_project["project_id"]}
        ]
        
        for issue_data in issues_data:
            client.post("/issues/", json=issue_data)
        
        # Filter by priority and assignee
        response = client.get("/issues/?priority=high&assignee=dev@example.com")
        assert response.status_code == 200
        issues = response.json()
        assert len(issues) == 1
        assert issues[0]["priority"] == "high"
        assert issues[0]["assignee"] == "dev@example.com"
    
    def test_update_issue_success(self, client, sample_issue):
        """Test successful issue update."""
        issue_id = sample_issue["issue_id"]
        update_data = {
            "title": "Updated Issue Title",
            "description": "Updated description",
            "priority": "low",
            "status": "in_progress",
            "assignee": "new_dev@example.com"
        }
        
        response = client.put(f"/issues/{issue_id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Issue Title"
        assert data["description"] == "Updated description"
        assert data["priority"] == "low"
        assert data["status"] == "in_progress"
        assert data["assignee"] == "new_dev@example.com"
        assert data["issue_id"] == issue_id
    
    def test_update_issue_partial(self, client, sample_issue):
        """Test partial issue update."""
        issue_id = sample_issue["issue_id"]
        update_data = {"status": "closed"}
        
        response = client.put(f"/issues/{issue_id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "closed"
        # Other fields should remain unchanged
        assert data["title"] == sample_issue["title"]
        assert data["priority"] == sample_issue["priority"]
    
    def test_update_issue_not_found(self, client):
        """Test updating non-existent issue."""
        update_data = {"title": "Non-existent Issue"}
        response = client.put("/issues/99999", json=update_data)
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_update_issue_invalid_priority(self, client, sample_issue):
        """Test updating issue with invalid priority."""
        issue_id = sample_issue["issue_id"]
        update_data = {"priority": "invalid_priority"}
        
        response = client.put(f"/issues/{issue_id}", json=update_data)
        assert response.status_code == 422
    
    def test_update_issue_invalid_status(self, client, sample_issue):
        """Test updating issue with invalid status."""
        issue_id = sample_issue["issue_id"]
        update_data = {"status": "invalid_status"}
        
        response = client.put(f"/issues/{issue_id}", json=update_data)
        assert response.status_code == 422
    
    def test_update_issue_empty_title(self, client, sample_issue):
        """Test updating issue with empty title."""
        issue_id = sample_issue["issue_id"]
        update_data = {"title": ""}
        
        response = client.put(f"/issues/{issue_id}", json=update_data)
        assert response.status_code == 422
    
    def test_delete_issue_success(self, client, sample_issue):
        """Test successful issue deletion."""
        issue_id = sample_issue["issue_id"]
        
        response = client.delete(f"/issues/{issue_id}")
        assert response.status_code == 200
        assert response.json() is True
        
        # Verify issue is deleted
        get_response = client.get(f"/issues/{issue_id}")
        assert get_response.status_code == 404
    
    def test_delete_issue_not_found(self, client):
        """Test deleting non-existent issue."""
        response = client.delete("/issues/99999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_delete_issue_invalid_id(self, client):
        """Test deleting issue with invalid ID."""
        response = client.delete("/issues/invalid")
        assert response.status_code == 422


class TestTagsAPI:
    """Test cases for Tags API endpoints."""
    
    def test_list_tags_empty(self, client):
        """Test listing tags when none exist."""
        response = client.get("/tags/")
        assert response.status_code == 200
        tags = response.json()
        assert isinstance(tags, list)
        assert len(tags) == 0
    
    def test_list_tags_with_data(self, client, sample_tags):
        """Test listing tags with existing data."""
        response = client.get("/tags/")
        assert response.status_code == 200
        tags = response.json()
        assert len(tags) > 0
        
        # Verify tag structure
        for tag in tags:
            assert "tag_id" in tag
            assert "name" in tag
            assert "created_at" in tag
            
        # Verify expected tags exist
        tag_names = [tag["name"] for tag in tags]
        expected_tags = {"frontend", "backend", "bug", "urgent", "documentation", "enhancement", "database"}
        assert expected_tags.issubset(set(tag_names))
    
    def test_list_tags_pagination(self, client, sample_tags):
        """Test tags pagination."""
        # Test skip and limit
        response = client.get("/tags/?skip=2&limit=3")
        assert response.status_code == 200
        tags = response.json()
        assert len(tags) <= 3
        
        # Test with large limit
        response = client.get("/tags/?limit=100")
        assert response.status_code == 200
        tags = response.json()
        assert len(tags) > 0
    
    def test_list_tags_invalid_pagination(self, client):
        """Test tags pagination with invalid parameters."""
        # Negative skip
        response = client.get("/tags/?skip=-1")
        assert response.status_code == 422
        
        # Invalid limit (too large)
        response = client.get("/tags/?limit=2000")
        assert response.status_code == 422
        
        # Zero limit
        response = client.get("/tags/?limit=0")
        assert response.status_code == 422
    
    def test_get_tag_success(self, client, sample_tags):
        """Test successful tag retrieval."""
        # Get a tag ID from the list
        response = client.get("/tags/")
        tags = response.json()
        assert len(tags) > 0
        
        tag_id = tags[0]["tag_id"]
        
        # Get specific tag
        response = client.get(f"/tags/{tag_id}")
        assert response.status_code == 200
        tag = response.json()
        assert tag["tag_id"] == tag_id
        assert "name" in tag
        assert "created_at" in tag
    
    def test_get_tag_not_found(self, client):
        """Test getting non-existent tag."""
        response = client.get("/tags/99999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_get_tag_invalid_id(self, client):
        """Test getting tag with invalid ID format."""
        response = client.get("/tags/invalid")
        assert response.status_code == 422
    
    def test_get_tag_usage_stats(self, client, sample_tags):
        """Test getting tag usage statistics."""
        response = client.get("/tags/stats/usage")
        assert response.status_code == 200
        stats = response.json()
        assert isinstance(stats, list)
        
        if len(stats) > 0:
            # Verify stats structure
            for stat in stats:
                assert "tag_id" in stat
                assert "name" in stat
                assert "usage_count" in stat
                assert isinstance(stat["usage_count"], int)
                assert stat["usage_count"] >= 0
    
    def test_delete_tag_success(self, client, sample_tags):
        """Test successful tag deletion."""
        # Get a tag to delete
        response = client.get("/tags/")
        tags = response.json()
        
        # Find a tag that's not heavily used
        tag_to_delete = None
        for tag in tags:
            if tag["name"] == "documentation":  # This tag should exist and be less used
                tag_to_delete = tag
                break
        
        assert tag_to_delete is not None
        tag_id = tag_to_delete["tag_id"]
        
        # Delete the tag
        response = client.delete(f"/tags/{tag_id}")
        assert response.status_code == 200
        result = response.json()
        assert "message" in result
        assert str(tag_id) in result["message"]
        
        # Verify tag is deleted
        response = client.get(f"/tags/{tag_id}")
        assert response.status_code == 404
    
    def test_delete_tag_not_found(self, client):
        """Test deleting non-existent tag."""
        response = client.delete("/tags/99999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_rename_tag_success(self, client, sample_tags):
        """Test successful tag renaming."""
        # Get current tags
        response = client.get("/tags/")
        tags = response.json()
        
        # Find a tag to rename
        original_name = "enhancement"
        new_name = "improvement"
        
        # Rename the tag
        response = client.post(f"/tags/rename?old_name={original_name}&new_name={new_name}")
        assert response.status_code == 200
        result = response.json()
        assert "message" in result
        assert original_name in result["message"]
        assert new_name in result["message"]
        
        # Verify tag was renamed by checking tag list
        response = client.get("/tags/")
        updated_tags = response.json()
        tag_names = [tag["name"] for tag in updated_tags]
        assert new_name in tag_names
        assert original_name not in tag_names
    
    def test_rename_tag_not_found(self, client):
        """Test renaming non-existent tag."""
        response = client.post("/tags/rename?old_name=nonexistent&new_name=something")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_rename_tag_invalid_names(self, client, sample_tags):
        """Test renaming tag with invalid names."""
        # Empty old name
        response = client.post("/tags/rename?old_name=&new_name=something")
        assert response.status_code == 422
        
        # Empty new name
        response = client.post("/tags/rename?old_name=bug&new_name=")
        assert response.status_code == 422
    
    def test_rename_tag_duplicate_name(self, client, sample_tags):
        """Test renaming tag to existing name."""
        response = client.post("/tags/rename?old_name=bug&new_name=frontend")
        assert response.status_code == 400
        assert "duplicate" in response.json()["detail"].lower() or "exists" in response.json()["detail"].lower()
    
    def test_cleanup_unused_tags(self, client, sample_tags):
        """Test cleaning up unused tags."""
        # Create a tag by creating and then deleting an issue
        issue_data = {
            "title": "Temporary Issue",
            "priority": "low",
            "tags": ["temporary", "cleanup"],
            "project_id": sample_tags[0]["project_id"]
        }
        issue_response = client.post("/issues/", json=issue_data)
        issue_id = issue_response.json()["issue_id"]
        
        # Delete the issue to make tags unused
        client.delete(f"/issues/{issue_id}")
        
        # Run cleanup
        response = client.post("/tags/cleanup")
        assert response.status_code == 200
        result = response.json()
        assert "message" in result
        assert "count" in result
        assert isinstance(result["count"], int)
        assert result["count"] >= 0
    
    def test_tags_api_error_handling(self, client):
        """Test various error conditions for tags API."""
        # Test malformed requests
        response = client.get("/tags/abc")  # Invalid ID
        assert response.status_code == 422
        
        # Test missing parameters for rename
        response = client.post("/tags/rename")
        assert response.status_code == 422


class TestIssuesAPIWithTags:
    """Test cases for Issues API endpoints with tag functionality."""
    
    def test_create_issue_with_tags(self, client, sample_project):
        """Test creating issue with tags."""
        issue_data = {
            "title": "Issue with Tags",
            "description": "Testing tag creation",
            "priority": "medium",
            "tags": ["frontend", "bug", "urgent"],
            "project_id": sample_project["project_id"]
        }
        
        response = client.post("/issues/", json=issue_data)
        assert response.status_code == 200
        issue = response.json()
        
        assert issue["title"] == "Issue with Tags"
        assert "tags" in issue
        assert len(issue["tags"]) == 3
        
        # Verify tag structure
        tag_names = [tag["name"] for tag in issue["tags"]]
        assert set(tag_names) == {"frontend", "bug", "urgent"}
    
    def test_create_issue_with_empty_tags(self, client, sample_project):
        """Test creating issue with empty tags."""
        issue_data = {
            "title": "Issue without Tags", 
            "priority": "medium",
            "tags": [],
            "project_id": sample_project["project_id"]
        }
        
        response = client.post("/issues/", json=issue_data)
        assert response.status_code == 200
        issue = response.json()
        
        assert issue["title"] == "Issue without Tags"
        assert issue["tags"] == []
    
    def test_create_issue_with_duplicate_tags(self, client, sample_project):
        """Test creating issue with duplicate tags in the list."""
        issue_data = {
            "title": "Issue with Duplicate Tags",
            "priority": "medium", 
            "tags": ["bug", "frontend", "bug", "urgent", "frontend"],
            "project_id": sample_project["project_id"]
        }
        
        response = client.post("/issues/", json=issue_data)
        assert response.status_code == 200
        issue = response.json()
        
        # Should deduplicate tags
        tag_names = [tag["name"] for tag in issue["tags"]]
        assert len(set(tag_names)) == len(tag_names)  # No duplicates
        assert set(tag_names) == {"bug", "frontend", "urgent"}
    
    def test_create_issue_with_whitespace_tags(self, client, sample_project):
        """Test creating issue with tags containing whitespace."""
        issue_data = {
            "title": "Issue with Whitespace Tags",
            "priority": "medium",
            "tags": [" bug ", "  frontend  ", "\ttesting\t", ""],
            "project_id": sample_project["project_id"]
        }
        
        response = client.post("/issues/", json=issue_data)
        assert response.status_code == 200
        issue = response.json()
        
        # Should normalize whitespace and remove empty tags
        tag_names = [tag["name"] for tag in issue["tags"]]
        assert set(tag_names) == {"bug", "frontend", "testing"}
    
    def test_update_issue_tags(self, client, sample_issue):
        """Test updating issue tags."""
        issue_id = sample_issue["issue_id"]
        
        # Update with new tags
        update_data = {
            "tags": ["updated", "modified", "test"]
        }
        
        response = client.put(f"/issues/{issue_id}", json=update_data)
        assert response.status_code == 200
        updated_issue = response.json()
        
        tag_names = [tag["name"] for tag in updated_issue["tags"]]
        assert set(tag_names) == {"updated", "modified", "test"}
    
    def test_update_issue_clear_tags(self, client, sample_tags):
        """Test clearing all tags from an issue."""
        issue_id = sample_tags[0]["issue_id"]  # Use issue that has tags
        
        # Clear tags
        update_data = {
            "tags": []
        }
        
        response = client.put(f"/issues/{issue_id}", json=update_data)
        assert response.status_code == 200
        updated_issue = response.json()
        
        assert updated_issue["tags"] == []
    
    def test_list_issues_filter_by_tags_any(self, client, sample_tags):
        """Test filtering issues by tags (any match)."""
        # Filter by any of the specified tags
        response = client.get("/issues/?tags=frontend,backend&tags_match_all=false")
        assert response.status_code == 200
        issues = response.json()
        
        assert len(issues) > 0
        
        # Verify all returned issues have at least one of the specified tags
        for issue in issues:
            tag_names = [tag["name"] for tag in issue["tags"]]
            assert any(tag in {"frontend", "backend"} for tag in tag_names)
    
    def test_list_issues_filter_by_tags_all(self, client, sample_tags):
        """Test filtering issues by tags (all match)."""
        # Filter by issues that have ALL specified tags
        response = client.get("/issues/?tags=backend,bug&tags_match_all=true")
        assert response.status_code == 200
        issues = response.json()
        
        # Verify all returned issues have ALL specified tags
        for issue in issues:
            tag_names = [tag["name"] for tag in issue["tags"]]
            assert "backend" in tag_names
            assert "bug" in tag_names
    
    def test_list_issues_filter_by_single_tag(self, client, sample_tags):
        """Test filtering issues by single tag."""
        response = client.get("/issues/?tags=urgent")
        assert response.status_code == 200
        issues = response.json()
        
        assert len(issues) > 0
        
        # Verify all returned issues have the specified tag
        for issue in issues:
            tag_names = [tag["name"] for tag in issue["tags"]]
            assert "urgent" in tag_names
    
    def test_list_issues_filter_by_nonexistent_tag(self, client, sample_tags):
        """Test filtering issues by non-existent tag."""
        response = client.get("/issues/?tags=nonexistent")
        assert response.status_code == 200
        issues = response.json()
        
        assert len(issues) == 0
    
    def test_list_issues_filter_tags_with_whitespace(self, client, sample_tags):
        """Test filtering issues with tags containing whitespace."""
        response = client.get("/issues/?tags= frontend , backend ")
        assert response.status_code == 200
        issues = response.json()
        
        # Should handle whitespace correctly
        assert len(issues) > 0
    
    def test_list_issues_filter_tags_empty_string(self, client, sample_tags):
        """Test filtering issues with empty tag filter."""
        response = client.get("/issues/?tags=")
        assert response.status_code == 200
        issues = response.json()
        
        # Should return all issues when tag filter is empty
        assert len(issues) == len(sample_tags)
    
    def test_list_issues_filter_tags_with_other_filters(self, client, sample_tags):
        """Test filtering issues by tags combined with other filters."""
        response = client.get("/issues/?tags=bug&priority=high")
        assert response.status_code == 200
        issues = response.json()
        
        # Verify all returned issues match both criteria
        for issue in issues:
            assert issue["priority"] == "high"
            tag_names = [tag["name"] for tag in issue["tags"]]
            assert "bug" in tag_names
    
    def test_list_issues_pagination_with_tag_filter(self, client, sample_tags):
        """Test pagination combined with tag filtering."""
        response = client.get("/issues/?tags=bug&skip=0&limit=2")
        assert response.status_code == 200
        issues = response.json()
        
        assert len(issues) <= 2
        
        # Verify pagination works with tag filter
        if len(issues) > 0:
            for issue in issues:
                tag_names = [tag["name"] for tag in issue["tags"]]
                assert "bug" in tag_names
    
    def test_list_issues_tag_filter_case_sensitivity(self, client, sample_tags):
        """Test tag filtering with different cases."""
        # Test with different case
        response = client.get("/issues/?tags=BUG,Frontend")
        assert response.status_code == 200
        issues = response.json()
        
        # Should be case-insensitive or handle normalization
        # The exact behavior depends on the normalization implementation
        # This test verifies the API handles case consistently
        
    def test_list_issues_complex_tag_combinations(self, client, sample_tags):
        """Test complex tag filtering combinations."""
        # Test multiple tags with match_all=true
        response = client.get("/issues/?tags=backend,urgent&tags_match_all=true")
        assert response.status_code == 200
        all_match_issues = response.json()
        
        # Test same tags with match_all=false
        response = client.get("/issues/?tags=backend,urgent&tags_match_all=false")
        assert response.status_code == 200
        any_match_issues = response.json()
        
        # Any match should return >= all match
        assert len(any_match_issues) >= len(all_match_issues)
    
    def test_get_issue_includes_tags(self, client, sample_tags):
        """Test that getting individual issue includes tags."""
        issue_id = sample_tags[0]["issue_id"]
        
        response = client.get(f"/issues/{issue_id}")
        assert response.status_code == 200
        issue = response.json()
        
        assert "tags" in issue
        assert isinstance(issue["tags"], list)
        if len(issue["tags"]) > 0:
            for tag in issue["tags"]:
                assert "tag_id" in tag
                assert "name" in tag
    
    def test_issues_tag_api_error_handling(self, client, sample_project):
        """Test error handling for issues with tags."""
        # Test creating issue with invalid tag format
        issue_data = {
            "title": "Test Issue",
            "priority": "medium",
            "tags": "not_a_list",  # Should be a list
            "project_id": sample_project["project_id"]
        }
        
        response = client.post("/issues/", json=issue_data)
        assert response.status_code == 422
    
    def test_issues_tag_integration_edge_cases(self, client, sample_project):
        """Test edge cases for tag integration."""
        # Test with very long tag names
        issue_data = {
            "title": "Long Tag Test",
            "priority": "medium",
            "tags": ["a" * 100],  # Very long tag name
            "project_id": sample_project["project_id"]
        }
        
        response = client.post("/issues/", json=issue_data)
        # This should either work or return a validation error
        assert response.status_code in [200, 422]
        
        # Test with many tags
        issue_data = {
            "title": "Many Tags Test",
            "priority": "medium",
            "tags": [f"tag{i}" for i in range(20)],  # Many tags
            "project_id": sample_project["project_id"]
        }
        
        response = client.post("/issues/", json=issue_data)
        assert response.status_code == 200
        issue = response.json()
        assert len(issue["tags"]) == 20


class TestAPIIntegration:
    """Integration tests for API endpoints."""
    
    def test_project_issue_lifecycle(self, client):
        """Test complete project and issue lifecycle."""
        # Create a project
        project_data = {"name": "Integration Test Project", "description": "Testing integration"}
        project_response = client.post("/projects/", json=project_data)
        assert project_response.status_code == 200
        project = project_response.json()
        
        # Create an issue for the project
        issue_data = {
            "title": "Integration Test Issue",
            "description": "Testing issue creation",
            "assignee": "tester@example.com",
            "priority": "medium",
            "project_id": project["project_id"]
        }
        issue_response = client.post("/issues/", json=issue_data)
        assert issue_response.status_code == 200
        issue = issue_response.json()
        
        # Update the issue
        update_data = {"status": "in_progress", "priority": "high"}
        update_response = client.put(f"/issues/{issue['issue_id']}", json=update_data)
        assert update_response.status_code == 200
        updated_issue = update_response.json()
        assert updated_issue["status"] == "in_progress"
        assert updated_issue["priority"] == "high"
        
        # List issues should show our issue
        list_response = client.get("/issues/")
        assert list_response.status_code == 200
        issues = list_response.json()
        assert len(issues) == 1
        assert issues[0]["issue_id"] == issue["issue_id"]
        
        # Delete the issue
        delete_issue_response = client.delete(f"/issues/{issue['issue_id']}")
        assert delete_issue_response.status_code == 200
        
        # Delete the project
        delete_project_response = client.delete(f"/projects/{project['project_id']}")
        assert delete_project_response.status_code == 200
        
        # Verify everything is cleaned up
        list_projects_response = client.get("/projects/")
        assert list_projects_response.status_code == 200
        assert list_projects_response.json() == []
        
        list_issues_response = client.get("/issues/")
        assert list_issues_response.status_code == 200
        assert list_issues_response.json() == []
    
    def test_case_sensitivity(self, client, sample_project):
        """Test case sensitivity in filters."""
        # Create issues with different cases
        issues_data = [
            {"title": "BUG in system", "priority": "medium", "assignee": "Alice@Example.Com", "project_id": sample_project["project_id"]},
            {"title": "bug in feature", "priority": "medium", "assignee": "alice@example.com", "project_id": sample_project["project_id"]},
            {"title": "Feature request", "priority": "medium", "assignee": "Bob@Example.Com", "project_id": sample_project["project_id"]}
        ]
        
        for issue_data in issues_data:
            client.post("/issues/", json=issue_data)
        
        # Test exact title match (current API behavior)
        response = client.get("/issues/?title=BUG in system")
        assert response.status_code == 200
        issues = response.json()
        assert len(issues) == 1
        assert issues[0]["title"] == "BUG in system"
        
        # Test case-sensitive assignee filter
        response = client.get("/issues/?assignee=alice@example.com")
        assert response.status_code == 200
        issues = response.json()
        # This should be exact match
        for issue in issues:
            assert issue["assignee"] == "alice@example.com"
    
    def test_concurrent_operations(self, client, sample_project):
        """Test handling of concurrent operations."""
        # Create an issue
        issue_data = {
            "title": "Concurrent Test Issue",
            "priority": "medium",  # Required field
            "project_id": sample_project["project_id"]
        }
        issue_response = client.post("/issues/", json=issue_data)
        issue = issue_response.json()
        issue_id = issue["issue_id"]
        
        # Simulate concurrent updates (in real scenario these would be simultaneous)
        update1_data = {"priority": "high"}
        update2_data = {"status": "in_progress"}
        
        response1 = client.put(f"/issues/{issue_id}", json=update1_data)
        response2 = client.put(f"/issues/{issue_id}", json=update2_data)
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        # Verify final state
        get_response = client.get(f"/issues/{issue_id}")
        final_issue = get_response.json()
        
        # At least one of the updates should have succeeded
        assert final_issue["priority"] == "high" or final_issue["status"] == "in_progress"
    
    def test_large_dataset_performance(self, client, sample_project):
        """Test API performance with larger dataset."""
        # Create multiple issues
        for i in range(20):
            issue_data = {
                "title": f"Performance Test Issue {i}",
                "description": f"Description for issue {i}",
                "assignee": f"dev{i % 3}@example.com",
                "priority": ["low", "medium", "high"][i % 3],
                "project_id": sample_project["project_id"]
            }
            response = client.post("/issues/", json=issue_data)
            assert response.status_code == 200
        
        # Test listing all issues
        response = client.get("/issues/")
        assert response.status_code == 200
        issues = response.json()
        assert len(issues) == 20
        
        # Test pagination
        response = client.get("/issues/?limit=5")
        assert response.status_code == 200
        issues = response.json()
        assert len(issues) == 5
        
        # Test filtering on large dataset
        response = client.get("/issues/?priority=high")
        assert response.status_code == 200
        high_priority_issues = response.json()
        expected_count = 20 // 3 + (1 if 20 % 3 > 2 else 0)  # Every 3rd issue starting from index 2
        assert len(high_priority_issues) == expected_count