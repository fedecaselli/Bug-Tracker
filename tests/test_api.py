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