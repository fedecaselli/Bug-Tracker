"""
Helpers to build request payloads from CLI options.
"""

from typing import Any, Dict, Optional

from core.enums import IssuePriority, IssueStatus


def build_project_payload(name: str) -> Dict[str, Any]:
    return {"name": name}


def build_issue_payload(
    project_id: int,
    title: str,
    description: Optional[str],
    log: Optional[str],
    summary: Optional[str],
    priority: IssuePriority,
    status: IssueStatus,
    assignee: Optional[str],
    tag_names: list[str],
    auto_tags: bool,
    auto_assignee: bool,
) -> Dict[str, Any]:
    return {
        "project_id": project_id,
        "title": title,
        "description": description,
        "log": log,
        "summary": summary,
        "priority": priority.value,
        "status": status.value,
        "assignee": assignee,
        "tag_names": tag_names,
        "auto_generate_tags": auto_tags,
        "auto_generate_assignee": auto_assignee,
    }


def build_issue_update_payload(
    title: Optional[str],
    description: Optional[str],
    log: Optional[str],
    summary: Optional[str],
    priority: Optional[IssuePriority],
    status: Optional[IssueStatus],
    assignee: Optional[str],
    tags: Optional[str],
    parse_tags,
) -> Dict[str, Any]:
    update_data: Dict[str, Any] = {}
    if title is not None:
        update_data["title"] = title
    if description is not None:
        update_data["description"] = description
    if log is not None:
        update_data["log"] = log
    if summary is not None:
        update_data["summary"] = summary
    if priority is not None:
        update_data["priority"] = priority.value
    if status is not None:
        update_data["status"] = status.value
    if assignee is not None:
        update_data["assignee"] = assignee
    if tags is not None:
        update_data["tag_names"] = parse_tags(tags)
    return update_data
