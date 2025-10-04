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
    """Base tag schema with common fields."""
    name: constr(min_length=1, max_length=100)
    
    @field_validator('name', mode='before')
    @classmethod
    def validate_name_field(cls, name):
        return validate_tag_name(name)

'''
class TagCreate(TagBase):
    """Schema for creating new tags."""
    pass  # name inherited from Base

class TagUpdate(BaseModel):
    """Schema for tag updates."""
    name: Optional[constr(min_length=1, max_length=100)] = None
'''

class TagOut(BaseModel):
    """Schema for tag API responses."""
    name: str
    tag_id: int
    
    # Enables automatic conversion of SQLAlchemy ORM objects to Pydantic models
    model_config = {"from_attributes": True}   

    
# PROJECT SCHEMAS 

class ProjectBase(BaseModel):
    """Base project schema with common fields."""
    name: constr(min_length=1, max_length=200)
    @field_validator('name', mode='before')
    @classmethod
    def validate_name_field(cls, name):
        return validate_project_name(name)

class ProjectCreate(ProjectBase):
    """Schema for creating new projects."""
    pass  # Inheris name from ProjectBase

class ProjectUpdate(BaseModel):
    """Schema for project updates."""
    name: Optional[constr(min_length=1, max_length=200)] = None
    @field_validator('name', mode='before')
    @classmethod
    def validate_name_field(cls, name):
        if name is None:
            return name
        return validate_project_name(name)
    
class ProjectOut(BaseModel):
    """Schema for project API responses."""
    name: str
    project_id: int
    created_at: datetime
    model_config = {"from_attributes": True}

    
# ISSUE SCHEMAS

class IssueBase(BaseModel):
    """Base issue schema with common fields and validation."""
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
        return validate_title(title)

    @field_validator('priority', mode='before')
    @classmethod
    def validate_priority_field(cls, priority):
        if priority is None:
            raise ValidationError("Priority is required")
        return validate_priority(priority)
    
    @field_validator('status', mode='before')
    @classmethod
    def validate_status_field(cls, status):
        if status is None:
            return "open"  
        return validate_status(status)
    
class IssueCreate(IssueBase):
    """Schema for creating new issues with automation options."""
    project_id: int
    tag_names: Optional[List[str]] = Field(default_factory=list)  # Manual tag assignment
    auto_generate_tags: bool = Field(default=False) # Enable automatic tag generation
    auto_generate_assignee: bool = Field(default=False) # Enable automatic assignee assignment

    @field_validator('tag_names', mode='before')
    @classmethod
    def validate_tag_names_field(cls, tag_names):
        return validate_tag_names(tag_names or [])
    
class IssueUpdate(BaseModel):
    """Schema for partial issue updates - all fields optional."""
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
        if title is None:
            return title
        return validate_title(title)

    @field_validator('priority', mode='before')
    @classmethod
    def validate_priority_field(cls, priority):
        if priority is None:
            return priority
        return validate_priority(priority)
    
    @field_validator('status', mode='before')
    @classmethod
    def validate_status_field(cls, status):
        if status is None:
            return status
        return validate_status(status)

    @field_validator('tag_names', mode='before')
    @classmethod
    def validate_tag_names_field(cls, tag_names):
        if tag_names is None:
            return tag_names
        return validate_tag_names(tag_names)

    
class IssueOut(BaseModel):
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


    
    
    
