"""
Tests for project repository functions: create, get, update, delete, and list.
"""

import pytest
from core.models import Project
from core.schemas import ProjectCreate, ProjectUpdate
from core.repos.projects import (
    create_project,
    get_project,
    get_project_by_name,
    update_project,
    delete_project,
    list_projects,
)
from core.repos.exceptions import AlreadyExists, NotFound

def test_create_and_get_project(db):
    project = create_project(db, ProjectCreate(name="Alpha"))
    assert project.name == "Alpha"
    fetched = get_project(db, project.project_id)
    assert fetched.project_id == project.project_id

def test_create_duplicate_project(db):
    create_project(db, ProjectCreate(name="Beta"))
    with pytest.raises(AlreadyExists):
        create_project(db, ProjectCreate(name="Beta"))

def test_get_project_by_name(db):
    project = create_project(db, ProjectCreate(name="Gamma"))
    fetched = get_project_by_name(db, "Gamma")
    assert fetched.project_id == project.project_id
    with pytest.raises(NotFound):
        get_project_by_name(db, "Nonexistent")

def test_update_project(db):
    project = create_project(db, ProjectCreate(name="Delta"))
    updated = update_project(db, project.project_id, ProjectUpdate(name="Delta2"))
    assert updated.name == "Delta2"
    with pytest.raises(AlreadyExists):
        create_project(db, ProjectCreate(name="Epsilon"))
        update_project(db, updated.project_id, ProjectUpdate(name="Epsilon"))

def test_delete_project(db):
    project = create_project(db, ProjectCreate(name="Zeta"))
    assert delete_project(db, project.project_id) is True
    with pytest.raises(NotFound):
        get_project(db, project.project_id)

def test_list_projects(db):
    create_project(db, ProjectCreate(name="A"))
    create_project(db, ProjectCreate(name="B"))
    projects = list_projects(db)
    assert len(projects) >= 2
    
def test_create_project_case_insensitive_uniqueness(db):
    from core.schemas import ProjectCreate
    from core.repos.projects import create_project, AlreadyExists

    create_project(db, ProjectCreate(name="CaseTest"))
    with pytest.raises(AlreadyExists):
        create_project(db, ProjectCreate(name="casetest"))