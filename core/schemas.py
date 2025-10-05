"""
Pydantic Schemas 

This module defines Pydantic models used for validating and formatting data in the bug tracking API. These schemas ensure that the data 
sent between the client and server is well-structured, accurate, and adheres to the expected format.

Schema Pattern:
- Base: Common fields shared across operations.
- Create: Fields required for creating new records.
- Update: Optional fields for partial updates.
- Out: Response format with computed fields and relationships.
"""

from typing import Optional, List
from pydantic import BaseModel, Field, constr, field_validator
from datetime import datetime    
from core.validation import (validate_priority, validate_status, validate_title, validate_project_name, validate_tag_name, validate_tag_names)
from pydantic import ValidationError


# TAG SCHEMAS

class TagBase(BaseModel):
    """
    Base tag schema with common fields.

    Attributes:
        name (str): The tag name (min 1, max 100 characters).

    Validators:
        validate_name_field: Validates and normalizes the tag name.

    Raises:
        ValueError: If the tag name is invalid.
    """
    name: constr(min_length=1, max_length=100)
    
    @field_validator('name', mode='before')
    @classmethod
    def validate_name_field(cls, name):
        """
        Validates and normalizes the tag name.

        Args:
            name (str): The tag name to validate.

        Returns:
            str: Validated and normalized tag name.

        Raises:
            ValueError: If the tag name is invalid.
        """
        return validate_tag_name(name)


class TagOut(BaseModel):
    """
    Schema for tag API responses.

    Attributes:
        name (str): The tag name.
        tag_id (int): Unique identifier for the tag.

    Config:
        model_config: Enables conversion from ORM objects.
    """
    name: str
    tag_id: int
    
    # Enables automatic conversion of SQLAlchemy ORM objects to Pydantic models
    model_config = {"from_attributes": True}   

    
# PROJECT SCHEMAS 

class ProjectBase(BaseModel):
    """
    Base project schema with common fields.

    Attributes:
        name (str): The project name (min 1, max 200 characters).

    Validators:
        validate_name_field: Validates and normalizes the project name.

    Raises:
        ValueError: If the project name is invalid.
    """
    name: constr(min_length=1, max_length=200)
    @field_validator('name', mode='before')
    @classmethod
    def validate_name_field(cls, name):
        """
        Validates and normalizes the project name.

        Args:
            name (str): The project name to validate.

        Returns:
            str: Validated and normalized project name.

        Raises:
            ValueError: If the project name is invalid.
        """
        return validate_project_name(name)

class ProjectCreate(ProjectBase):
    """
    Schema for creating new projects.

    Inherits:
        name from ProjectBase.
    """
    pass  # Inheris name from ProjectBase

class ProjectUpdate(BaseModel):
    """
    Schema for project updates.

    Attributes:
        name (Optional[str]): The new project name (min 1, max 200 characters).

    Validators:
        validate_name_field: Validates and normalizes the project name if provided.

    Raises:
        ValueError: If the project name is invalid.
    """
    name: Optional[constr(min_length=1, max_length=200)] = None
    @field_validator('name', mode='before')
    @classmethod
    def validate_name_field(cls, name):
        """
        Validates and normalizes the project name if provided.

        Args:
            name (Optional[str]): The project name to validate.

        Returns:
            Optional[str]: Validated and normalized project name or None.

        Raises:
            ValueError: If the project name is invalid.
        """
        if name is None:
            return name
        return validate_project_name(name)
    
class ProjectOut(BaseModel):
    """
    Schema for project API responses.

    Attributes:
        name (str): The project name.
        project_id (int): Unique identifier for the project.
        created_at (datetime): Timestamp of project creation.

    Config:
        model_config: Enables conversion from ORM objects.
    """
    name: str
    project_id: int
    created_at: datetime
    model_config = {"from_attributes": True}

    
# ISSUE SCHEMAS

class IssueBase(BaseModel):
    """
    Base issue schema with common fields and validation.

    Attributes:
        title (str): Issue title (min 1, max 100 characters).
        description (Optional[str]): Detailed description.
        log (Optional[str]): Error log or debug info.
        summary (Optional[str]): Brief summary.
        priority (str): Priority level ("low", "medium", "high").
        status (str): Status ("open", "in_progress", "closed").
        assignee (Optional[str]): Assigned person.

    Validators:
        validate_title_field: Validates the issue title.
        validate_priority_field: Validates the priority.
        validate_status_field: Validates the status.

    Raises:
        ValueError: If any field is invalid.
    """
    title: constr(min_length=1, max_length=100)
    description: Optional[str] = None
    log: Optional[str] = None
    summary: Optional[str] = None
    priority: str
    status: str = "open"
    assignee: Optional[str] = None

    @field_validator('title', mode='before')
    @classmethod
    def validate_title_field(cls, title):
        """
        Validates the issue title.

        Args:
            title (str): The issue title.

        Returns:
            str: Validated title.

        Raises:
            ValueError: If the title is invalid.
        """
        return validate_title(title)

    @field_validator('priority', mode='before')
    @classmethod
    def validate_priority_field(cls, priority):
        """
        Validates the priority.

        Args:
            priority (str): Priority value.

        Returns:
            str: Validated priority.

        Raises:
            ValidationError: If priority is missing.
            ValueError: If priority is invalid.
        """
        if priority is None:
            raise ValidationError("Priority is required")
        return validate_priority(priority)
    
    @field_validator('status', mode='before')
    @classmethod
    def validate_status_field(cls, status):
        """
        Validates the status.

        Args:
            status (str): Status value.

        Returns:
            str: Validated status.

        Raises:
            ValueError: If status is invalid.
        """
        if status is None:
            return "open"  
        return validate_status(status)
    
class IssueCreate(IssueBase):
    """
    Schema for creating new issues with automation options.

    Attributes:
        project_id (int): Project ID for the issue.
        tag_names (Optional[List[str]]): List of tag names.
        auto_generate_tags (bool): Enable automatic tag generation.
        auto_generate_assignee (bool): Enable automatic assignee assignment.

    Validators:
        validate_tag_names_field: Validates and normalizes tag names.

    Raises:
        ValueError: If any tag name is invalid.
    """
    project_id: int
    tag_names: Optional[List[str]] = Field(default_factory=list)  # Manual tag assignment
    auto_generate_tags: bool = Field(default=False) # Enable automatic tag generation
    auto_generate_assignee: bool = Field(default=False) # Enable automatic assignee assignment

    @field_validator('tag_names', mode='before')
    @classmethod
    def validate_tag_names_field(cls, tag_names):
        """
        Validates and normalizes tag names.

        Args:
            tag_names (Optional[List[str]]): List of tag names.

        Returns:
            List[str]: Validated and normalized tag names.

        Raises:
            ValueError: If any tag name is invalid.
        """
        return validate_tag_names(tag_names or [])
    
class IssueUpdate(BaseModel):
    """
    Schema for partial issue updates - all fields optional.

    Attributes:
        title (Optional[str]): New issue title.
        description (Optional[str]): New description.
        log (Optional[str]): New log.
        summary (Optional[str]): New summary.
        priority (Optional[str]): New priority.
        status (Optional[str]): New status.
        assignee (Optional[str]): New assignee.
        tag_names (Optional[List[str]]): New tag names.

    Validators:
        validate_title_field: Validates the title if provided.
        validate_priority_field: Validates the priority if provided.
        validate_status_field: Validates the status if provided.
        validate_tag_names_field: Validates tag names if provided.

    Raises:
        ValueError: If any field is invalid.
    """
    title: Optional[constr(min_length=1, max_length=100)] = None
    description: Optional[str] = None
    log: Optional[str] = None
    summary: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    assignee: Optional[str] = None
    tag_names: Optional[List[str]] = None 

    @field_validator('title', mode='before')
    @classmethod
    def validate_title_field(cls, title):
        """
        Validates the title if provided.

        Args:
            title (Optional[str]): The issue title.

        Returns:
            Optional[str]: Validated title or None.

        Raises:
            ValueError: If the title is invalid.
        """
        if title is None:
            return title
        return validate_title(title)

    @field_validator('priority', mode='before')
    @classmethod
    def validate_priority_field(cls, priority):
        """
        Validates the priority if provided.

        Args:
            priority (Optional[str]): Priority value.

        Returns:
            Optional[str]: Validated priority or None.

        Raises:
            ValueError: If priority is invalid.
        """
        if priority is None:
            return priority
        return validate_priority(priority)
    
    @field_validator('status', mode='before')
    @classmethod
    def validate_status_field(cls, status):
        """
        Validates the status if provided.

        Args:
            status (Optional[str]): Status value.

        Returns:
            Optional[str]: Validated status or None.

        Raises:
            ValueError: If status is invalid.
        """
        if status is None:
            return status
        return validate_status(status)

    @field_validator('tag_names', mode='before')
    @classmethod
    def validate_tag_names_field(cls, tag_names):
        """
        Validates tag names if provided.

        Args:
            tag_names (Optional[List[str]]): List of tag names.

        Returns:
            Optional[List[str]]: Validated tag names or None.

        Raises:
            ValueError: If any tag name is invalid.
        """
        if tag_names is None:
            return tag_names
        return validate_tag_names(tag_names)

    
class IssueOut(BaseModel):
    """
    Schema for issue API responses.

    Attributes:
        issue_id (int): Unique identifier for the issue.
        project_id (int): Associated project ID.
        title (str): Issue title.
        description (Optional[str]): Issue description.
        log (Optional[str]): Issue log.
        summary (Optional[str]): Issue summary.
        priority (str): Issue priority.
        status (str): Issue status.
        assignee (Optional[str]): Issue assignee.
        created_at (datetime): Creation timestamp.
        updated_at (Optional[datetime]): Last update timestamp.
        tags (List[TagOut]): List of associated tags.

    Config:
        model_config: Enables conversion from ORM objects.
    """
    issue_id: int
    project_id: int
    title: str
    description: Optional[str] = None
    log: Optional[str] = None
    summary: Optional[str] = None
    priority: str
    status: str
    assignee: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    tags: List[TagOut] = Field(default_factory=list)

    model_config = {"from_attributes": True}


    
    
    
