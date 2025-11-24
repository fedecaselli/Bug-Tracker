"""
Validation utilities for Bug Tracker application.

This module provides functions to validate and normalize input data for tags, projects, issues, and related fields.
Each function raises ValueError on invalid input.
"""

import re
from core.enums import IssuePriority, IssueStatus

def normalize_name(name: str) -> str:
    """
    Normalize a tag name by trimming whitespace, collapsing multiple spaces, and converting to lowercase.

    Args:
        name (str): The tag name to normalize.

    Returns:
        str: Normalized tag name.

    Example:
        "  Front End  " -> "front end"
    """
    return re.sub(r'\s+', ' ', name.strip()).lower()

def validate_priority(priority: str) -> str:
    """
    Validate and normalize an issue priority.

    Args:
        priority (str): Priority value to validate ("low", "medium", "high").

    Returns:
        str: Normalized priority value.

    Raises:
        ValueError: If priority is not one of the allowed values.
    """
    allowed_priorities = {p.value for p in IssuePriority}
    normalized = priority.lower().strip()
    if normalized not in allowed_priorities:
        raise ValueError(f"Priority must be one of: {', '.join(allowed_priorities)}")
    return normalized

def validate_status(status: str) -> str:
    """
    Validate and normalize an issue status.

    Args:
        status (str): Status value to validate ("open", "in_progress", "closed").

    Returns:
        str: Normalized status value.

    Raises:
        ValueError: If status is not one of the allowed values.
    """
    allowed_statuses = {s.value for s in IssueStatus}
    normalized = status.lower().strip()
    if normalized not in allowed_statuses:
        raise ValueError(f"Status must be one of: {', '.join(allowed_statuses)}")
    return normalized

def validate_title(title: str) -> str:
    """
    Validate an issue title for non-empty and length constraints.

    Args:
        title (str): Title to validate.

    Returns:
        str: Validated and trimmed title.

    Raises:
        ValueError: If title is empty or exceeds 100 characters.
    """
    if not title or len(title.strip()) == 0:
        raise ValueError("Title cannot be empty")
    if len(title.strip()) > 100:
        raise ValueError("Title cannot exceed 100 characters")
    return title.strip()

def validate_project_name(name: str) -> str:
    """
    Validate a project name for non-empty and length constraints.

    Args:
        name (str): Project name to validate.

    Returns:
        str: Validated and trimmed project name.

    Raises:
        ValueError: If name is empty or exceeds 200 characters.
    """
    if not name or len(name.strip()) == 0:
        raise ValueError("Project name cannot be empty")
    if len(name.strip()) > 200:
        raise ValueError("Project name cannot exceed 200 characters")
    return name.strip()

def validate_tag_name(name: str) -> str:
    """
    Validate and normalize a tag name.

    Args:
        name (str): Tag name to validate.

    Returns:
        str: Normalized and validated tag name.

    Raises:
        ValueError: If tag name is empty or exceeds 100 characters.
    """
    normalized = normalize_name(name)
    if not normalized or len(normalized) == 0:
        raise ValueError("Tag name cannot be empty")
    if len(normalized) > 100:
        raise ValueError("Tag name cannot exceed 100 characters")
    return normalized

def validate_tag_names(tag_names: list) -> list:
    """
    Validate and normalize a list of tag names, removing duplicates.

    Args:
        tag_names (list): List of tag names (strings) to validate.

    Returns:
        list: List of unique, validated, normalized tag names.

    Raises:
        ValueError: If any tag name is invalid.
    """
    if not tag_names:
        return []
    validated_tags = []
    for tag in tag_names:
        if isinstance(tag, str):
            validated_tag = validate_tag_name(tag)  
            if validated_tag and validated_tag not in validated_tags:
                validated_tags.append(validated_tag)
    return validated_tags


# Reusable helpers for Pydantic models and repository layer

def require_title(title: str | None) -> str:
    """
    Ensure a title is present and valid.

    Args:
        title (str | None): Title to validate.

    Returns:
        str: Validated title.

    Raises:
        ValueError: If title is missing or invalid.
    """
    if title is None:
        raise ValueError("Title is required")
    return validate_title(title)


def optional_title(title: str | None) -> str | None:
    """
    Validate a title when provided.

    Args:
        title (str | None): Title to validate.

    Returns:
        str | None: Validated title or None.

    Raises:
        ValueError: If title is invalid.
    """
    if title is None:
        return None
    return validate_title(title)


def require_priority(priority: str | None) -> str:
    """
    Ensure a priority is present and valid.

    Args:
        priority (str | None): Priority to validate.

    Returns:
        str: Validated priority.

    Raises:
        ValueError: If priority is missing or invalid.
    """
    if priority is None:
        raise ValueError("Priority is required")
    return validate_priority(priority)


def optional_priority(priority: str | None) -> str | None:
    """
    Validate a priority when provided.

    Args:
        priority (str | None): Priority to validate.

    Returns:
        str | None: Validated priority or None.

    Raises:
        ValueError: If priority is invalid.
    """
    if priority is None:
        return None
    return validate_priority(priority)


def normalize_status(status: str | None, default: str | None = None) -> str | None:
    """
    Validate a status and optionally fall back to a default when missing.

    Args:
        status (str | None): Status to validate.
        default (str | None): Default value when status is None.

    Returns:
        str | None: Validated status or the default value.

    Raises:
        ValueError: If status is invalid.
    """
    if status is None:
        return default
    return validate_status(status)


def optional_project_name(name: str | None) -> str | None:
    """
    Validate a project name when provided.

    Args:
        name (str | None): Project name.

    Returns:
        str | None: Validated project name or None.

    Raises:
        ValueError: If name is invalid.
    """
    if name is None:
        return None
    return validate_project_name(name)


def normalize_tag_names(tag_names: list | None, keep_none: bool = False) -> list | None:
    """
    Validate a list of tag names with control over how None values are treated.

    Args:
        tag_names (list | None): List of tag names.
        keep_none (bool): If True, returns None when tag_names is None; otherwise returns [].

    Returns:
        list | None: Validated tag names, [] when empty, or None when keep_none=True and input is None.

    Raises:
        ValueError: If any tag name is invalid.
    """
    if tag_names is None:
        return None if keep_none else []
    return validate_tag_names(tag_names)
