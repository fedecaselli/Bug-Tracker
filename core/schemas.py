# Pydantic schema = a class that defines the structure of request/response data for your API.
# Validate data before saved to database

'''
Create = what user sends to create.
Update = optional fields.
Out = what API returns.
'''
from typing import Optional, List
from pydantic import BaseModel, Field, constr, field_validator
from datetime import datetime


# TAG SCHEMAS
class TagBase(BaseModel):
    name: constr(min_length=1, max_length=100)
'''
class TagCreate(TagBase):
    pass  # name inherited from Base

class TagUpdate(BaseModel):
    name: Optional[constr(min_length=1, max_length=100)] = None
'''

class TagOut(BaseModel):
    tag_id: int
    model_config = {"from_attributes": True}   

    
# PROJECT SCHEMAS 
class ProjectBase(BaseModel):
    name: constr(min_length=1, max_length=200)

class ProjectCreate(ProjectBase):
    pass  # name inherited from Base

class ProjectUpdate(BaseModel):
    name: Optional[constr(min_length=1, max_length=200)] = None
    
class ProjectOut(ProjectBase):
    project_id: int
    created_at: datetime
    model_config = {"from_attributes": True}
    
# ISSUE SCHEMAS
class IssueBase(BaseModel):
    title: constr(min_length=1, max_length=100)
    description: Optional[str] = None
    log: Optional[str] = None
    summary: Optional[str] = None
    priority: constr(pattern=r"^(low|medium|high)$")
    status: constr(pattern=r"^(open|in_progress|closed)$") = "open"
    assignee: Optional[str] = None


    @field_validator("priority")
    @classmethod
    def normalize_priority(cls, priority):
        if priority is None: return priority
        priority = priority.lower()
        if priority not in {"low","medium","high"}:
            raise ValueError("priority must be low|medium|high")
        return priority

    @field_validator("status")
    @classmethod
    def normalize_status(cls, status):
        if status is None: 
            return status
        status = status.lower()
        if status not in {"open","in_progress","closed"}:
            raise ValueError("status must be open|in_progress|closed")
        return status
    
# Inherit base fields automatically
class IssueCreate(IssueBase):
    project_id: int
    tag_names: Optional[List[str]] = Field(default_factory=list)  #List of strings / empty list
    
# OPTIONALS > MODIFY 1 OR MORE 
class IssueUpdate(BaseModel): #cannot inherit from issuebase bc they are optional fields
    title: Optional[constr(min_length=1, max_length=100)] = None
    description: Optional[str] = None
    log: Optional[str] = None
    summary: Optional[str] = None
    priority: Optional[constr(pattern=r"^(low|medium|high)$")] = None
    status: Optional[constr(pattern=r"^(open|in_progress|closed)$")] = None
    assignee: Optional[str] = None
    tag_names: Optional[List[str]] = None #None = no change in the tags.

    @field_validator("priority")
    @classmethod
    def normalize_priority(cls, priority):
        if priority is None: 
            return priority
        priority = priority.lower()
        if priority not in {"low","medium","high"}:
            raise ValueError("priority must be low|medium|high")
        return priority

    @field_validator("status")
    @classmethod
    def normalize_status(cls, status):
        if status is None: 
            return status
        status = status.lower()
        if status not in {"open","in_progress","closed"}:
            raise ValueError("status must be open|in_progress|closed")
        return status
    
    
class IssueOut(IssueBase):
    issue_id: int
    project_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    tags: List[TagOut] = Field(default_factory=list)

    model_config = {"from_attributes": True}

    
    #may receive data not just from dicts, but also from ORM objects
    #(like your SQLAlchemy models).


