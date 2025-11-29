"""
Shared helpers for CLI commands to avoid duplicated parsing and lookup logic.
"""

from typing import Optional, List, Callable


def resolve_project_id(
    list_projects_fn: Callable[[], list[dict]],
    get_project_fn: Callable[[int], dict],
    name: Optional[str] = None,
    project_id: Optional[int] = None,
) -> int:
    """
    Resolve a project ID using the API call helpers provided.

    Args:
        list_projects_fn: Callable that returns a list of project dicts.
        get_project_fn: Callable that retrieves a single project by id.
        name: Optional project name.
        project_id: Optional project id.
    """
    if project_id is not None and name is not None:
        project = _get_project_by_name(list_projects_fn, name)
        if project["project_id"] != project_id:
            raise ValueError("Project name and ID do not match. Provide either name or id.")
        return project["project_id"]

    if project_id is not None:
        project = get_project_fn(project_id)
        return project["project_id"]

    if name is not None:
        project = _get_project_by_name(list_projects_fn, name)
        return project["project_id"]

    raise ValueError("Provide either --id or --name to identify a project")


def _get_project_by_name(list_projects_fn: Callable[[], list[dict]], name: str) -> dict:
    projects = list_projects_fn()
    for project in projects:
        if project["name"] == name:
            return project
    raise ValueError(f"Project named '{name}' not found")


def parse_tags_input(tags_string: Optional[str]) -> List[str]:
    """
    Parse a comma-separated tags string into a list of normalized tag names.
    """
    if not tags_string:
        return []
    return [tag.strip() for tag in tags_string.split(",") if tag.strip()]
