"""
Helpers to format API responses for CLI output.
"""

from typing import Callable, Dict, List


def format_project_row(project: Dict) -> str:
    return f"Project id: {project['project_id']} \tname: {project['name']} \tcreated at: {project.get('created_at')}"


def format_issue(issue: Dict, project_name_lookup: Callable[[int], str]) -> str:
    tags_str = ", ".join([t["name"] for t in issue.get("tags", [])]) if issue.get("tags") else "none"
    project_display = project_name_lookup(issue["project_id"])
    return (
        f"Issue id: {issue['issue_id']} \n"
        f"title: {issue['title']} \n"
        f"description: {issue.get('description')} \n"
        f"log: {issue.get('log')} \n"
        f"summary: {issue.get('summary')} \n"
        f"priority: {issue['priority']}\n"
        f"status: {issue['status']} \n"
        f"assignee: {issue.get('assignee')} \n"
        f"tags: {tags_str} \n"
        f"project_id: {issue['project_id']} \n"
        f"project_name:{project_display}\n"
    )


def format_tag_stats(stats: List[Dict]) -> str:
    lines = ["Tag Usage Statistics:", f"{'Tag Name':<20} {'Usage Count':>10}", "-" * 30]
    for stat in stats:
        lines.append(f"{stat['name']:<20} {stat['issue_count']:>10}")
    return "\n".join(lines)
