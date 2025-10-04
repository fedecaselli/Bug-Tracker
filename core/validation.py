from pydantic import ValidationError

def validate_priority(priority: str) -> str:
    allowed_priorities = {"low", "medium", "high"}
    normalized = priority.lower().strip()
    if normalized not in allowed_priorities:
        raise ValidationError(f"Priority must be one of: {', '.join(allowed_priorities)}")
    return normalized

def validate_status(status: str) -> str:
    allowed_statuses = {"open", "in_progress", "closed"}
    normalized = status.lower().strip()
    if normalized not in allowed_statuses:
        raise ValidationError(f"Status must be one of: {', '.join(allowed_statuses)}")
    return normalized

def validate_title(title: str) -> str:
    if not title or len(title.strip()) == 0:
        raise ValidationError("Title cannot be empty")
    if len(title.strip()) > 100:
        raise ValidationError("Title cannot exceed 100 characters")
    return title.strip()

def validate_project_name(name: str) -> str:
    if not name or len(name.strip()) == 0:
        raise ValidationError("Project name cannot be empty")
    if len(name.strip()) > 200:
        raise ValidationError("Project name cannot exceed 200 characters")
    return name.strip()

def validate_tag_name(name: str) -> str:
    if not name or len(name.strip()) == 0:
        raise ValidationError("Tag name cannot be empty")
    if len(name.strip()) > 100:
        raise ValidationError("Tag name cannot exceed 100 characters")
    return name.lower().strip()

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
