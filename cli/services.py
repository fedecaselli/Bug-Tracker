"""
Shared helpers for CLI commands to avoid duplicated parsing and lookup logic.
"""

from typing import Optional, List

from core.repos.projects import get_project as repo_get_project, get_project_by_name as repo_get_project_by_name
from core.repos.exceptions import NotFound


def resolve_project_id(db, name: Optional[str] = None, project_id: Optional[int] = None) -> int:
    """
    Resolve a project ID from either name, id, or both (must match).
    """
    if project_id is not None and name is not None:
        project = repo_get_project_by_name(db, name)
        if project.project_id != project_id:
            raise ValueError("Project name and ID do not match. Provide either name or id.")
        return project.project_id

    if project_id is not None:
        project = repo_get_project(db, project_id)
        return project.project_id

    if name is not None:
        project = repo_get_project_by_name(db, name)
        return project.project_id

    raise ValueError("Provide either --id or --name to delete a project")


def parse_tags_input(tags_string: Optional[str]) -> List[str]:
    """
    Parse a comma-separated tags string into a list of normalized tag names.
    """
    if not tags_string:
        return []
    return [tag.strip() for tag in tags_string.split(",") if tag.strip()]
