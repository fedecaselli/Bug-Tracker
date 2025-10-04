#from pydantic import ValidationError

import re

def normalize_name(name: str) -> str:
    """Normalize tag name: trim, collapse spaces, lowercase."""
    return re.sub(r'\s+', ' ', name.strip()).lower()

def validate_priority(priority: str) -> str:
    allowed_priorities = {"low", "medium", "high"}
    normalized = priority.lower().strip()
    if normalized not in allowed_priorities:
        raise ValueError(f"Priority must be one of: {', '.join(allowed_priorities)}")
    return normalized

def validate_status(status: str) -> str:
    allowed_statuses = {"open", "in_progress", "closed"}
    normalized = status.lower().strip()
    if normalized not in allowed_statuses:
        raise ValueError(f"Status must be one of: {', '.join(allowed_statuses)}")
    return normalized

def validate_title(title: str) -> str:
    if not title or len(title.strip()) == 0:
        raise ValueError("Title cannot be empty")
    if len(title.strip()) > 100:
        raise ValueError("Title cannot exceed 100 characters")
    return title.strip()

def validate_project_name(name: str) -> str:
    if not name or len(name.strip()) == 0:
        raise ValueError("Project name cannot be empty")
    if len(name.strip()) > 200:
        raise ValueError("Project name cannot exceed 200 characters")
    return name.strip()

def validate_tag_name(name: str) -> str:
    normalized = normalize_name(name)
    if not normalized or len(normalized) == 0:
        raise ValueError("Tag name cannot be empty")
    if len(normalized) > 100:
        raise ValueError("Tag name cannot exceed 100 characters")
    return normalized

def validate_tag_names(tag_names: list) -> list:
    if not tag_names:
        return []
    validated_tags = []
    for tag in tag_names:
        if isinstance(tag, str):
            validated_tag = validate_tag_name(tag)  
            if validated_tag and validated_tag not in validated_tags:
                validated_tags.append(validated_tag)
    return validated_tags



