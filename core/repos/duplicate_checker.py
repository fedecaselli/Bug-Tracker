"""
Helpers for detecting duplicate issues.

The logic is kept here to keep repository methods slimmer and easier to test.
"""

from typing import List
from sqlalchemy.orm import Session
from core.models import Issue


def check_duplicate_issue(
    db: Session,
    project_id: int,
    title: str,
    description: str = None,
    log: str = None,
    summary: str = None,
    priority: str = None,
    status: str = None,
    assignee: str = None,
    tag_names: List[str] | None = None,
    exclude_issue_id: int | None = None,
) -> bool:
    """
    Check if an issue with identical fields already exists.

    Args mirror the Issue model fields plus optional tag names and an issue ID to exclude.
    """
    query = db.query(Issue).filter(
        Issue.project_id == project_id,
        Issue.title == title,
        Issue.description == description,
        Issue.log == log,
        Issue.summary == summary,
        Issue.priority == priority,
        Issue.status == status,
        Issue.assignee == assignee,
    )

    if exclude_issue_id:
        query = query.filter(Issue.issue_id != exclude_issue_id)

    for issue in query.all():
        issue_tag_names = {tag.name for tag in issue.tags}
        if set(tag_names or []) == issue_tag_names:
            return True

    return False

