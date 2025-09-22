# Pydantic schema = a class that defines the structure of request/response data for your API.
# Validate data before saved to database

'''
Create = what user sends to create.
Update = optional fields.
Out = what API returns.
'''
from typing import Optional, List
from pydantic import BaseModel, Field, constr
from datetime import datetime

# TAG SCHEMAS
class TagBase(BaseModel):
    name: constr(min_length=1, max_length=100)
    
class TagCreate(TagBase):
    pass  # name inherited from Base

class TagUpdate(BaseModel):
    name: Optional[constr(min_length=1, max_length=200)] = None
    
class TagOut(BaseModel):
    tag_id: int
    model_config = {"from_attributes": True}  # version 2.11
    
    
    
# PROJECT SCHEMAS 
class ProjectBase(BaseModel):
    name: constr(min_length=1, max_length=200)

class ProjectCreate(ProjectBase):
    pass  # name inherited from Base

class ProjectUpdate(BaseModel):
    name: Optional[constr(min_length=1, max_length=200)] = None
    
class ProjectOut(BaseModel):
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

# Inherit base fields automatically
class IssueCreate(IssueBase):
    project_id: int
    tag_ids: Optional[List[str]] = Field(default_factory=list) 
    
# OPTIONALS > MODIFY 1 OR MORE 
class IssueUpdate(BaseModel):
    title: Optional[constr(min_length=1, max_length=100)] = None
    description: Optional[str] = None
    log: Optional[str] = None
    summary: Optional[str] = None
    priority: Optional[constr(pattern=r"^(low|medium|high)$")] = None
    status: Optional[constr(pattern=r"^(open|in_progress|closed)$")] = None
    assignee: Optional[str] = None
    tags: Optional[List[str]] = None
    
    
class IssueOut(IssueBase):
    issue_id: int
    project_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    tags: List[TagOut] = Field(default_factory=list)

    model_config = {"from_attributes": True}

    
    #may receive data not just from dicts, but also from ORM objects
    #(like your SQLAlchemy models).


