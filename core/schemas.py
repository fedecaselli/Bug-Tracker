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

# TAG SCHEMAS

class TagBase(BaseModel):
    """Base tag schema with common fields."""
    name: constr(min_length=1, max_length=100)

'''
class TagCreate(TagBase):
    """Schema for creating new tags."""
    pass  # name inherited from Base

class TagUpdate(BaseModel):
    """Schema for tag updates."""
    name: Optional[constr(min_length=1, max_length=100)] = None
'''

class TagOut(TagBase):
    """Schema for tag API responses."""
    tag_id: int
    
    # Enables automatic conversion of SQLAlchemy ORM objects to Pydantic models
    model_config = {"from_attributes": True}   

    
# PROJECT SCHEMAS 

class ProjectBase(BaseModel):
    """Base project schema with common fields."""
    name: constr(min_length=1, max_length=200)

class ProjectCreate(ProjectBase):
    """Schema for creating new projects."""
    pass  # Inheris name from ProjectBase

class ProjectUpdate(BaseModel):
    """Schema for project updates."""
    name: Optional[constr(min_length=1, max_length=200)] = None
    
class ProjectOut(ProjectBase):
    """Schema for project API responses."""
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

    @field_validator('priority', mode='before')
    @classmethod
    def normalize_priority(cls, v):
        """Normalize priority to lowercase."""
        if v is None:
            raise ValueError("Priority is required")
        normalized = str(v).lower().strip()
        # Validate against allowed values
        if normalized not in ("low", "medium", "high"):
            raise ValueError("Priority must be one of: low, medium, high")
        return normalized
    
    @field_validator('status', mode='before')
    @classmethod
    def normalize_status(cls, v):
        """Normalize status to lowercase."""
        if v is None:
            return "open"  # Default value
        normalized = str(v).lower().strip()
        # Validate against allowed values
        if normalized not in ("open", "in_progress", "closed"):
            raise ValueError("Status must be one of: open, in_progress, closed")
        return normalized

class IssueCreate(IssueBase):
    """Schema for creating new issues with automation options."""
    project_id: int
    tag_names: Optional[List[str]] = Field(default_factory=list)  # Manual tag assignment
    auto_generate_tags: bool = Field(default=False) # Enable automatic tag generation
    auto_generate_assignee: bool = Field(default=False) # Enable automatic assignee assignment
    
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

    @field_validator('priority', mode='before')
    @classmethod
    def normalize_priority(cls, v):
        """Normalize priority to lowercase."""
        if v is None:
            raise ValueError("Priority is required")
        normalized = str(v).lower().strip()
        # Validate against allowed values
        if normalized not in ("low", "medium", "high"):
            raise ValueError("Priority must be one of: low, medium, high")
        return normalized
    
    @field_validator('status', mode='before')
    @classmethod
    def normalize_status(cls, v):
        """Normalize status to lowercase."""
        if v is None:
            return "open"  # Default value
        normalized = str(v).lower().strip()
        # Validate against allowed values
        if normalized not in ("open", "in_progress", "closed"):
            raise ValueError("Status must be one of: open, in_progress, closed")
        return normalized
    
class IssueOut(IssueBase):
    issue_id: int
    project_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    tags: List[TagOut] = Field(default_factory=list)

    model_config = {"from_attributes": True}