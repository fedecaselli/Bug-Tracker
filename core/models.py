"""
Database Models 

This module defines the SQLAlchemy ORM models for:
- Issues: Bug reports 
- Projects: Organizational containers for grouping related issues
- Tags: Labelig system for categorizing issues
- Association table for many-to-many relationship between issues and tags
"""

from sqlalchemy import Column, Integer, String, CheckConstraint, Text, DateTime, func, ForeignKey, Table, Index
from sqlalchemy.orm import relationship
from .db import Base 

# ASSOCIATION TABLES

# Many-to-many association table between Issues and Tags
# Uses simple Table instead of full ORM model since no additional relationship data is needed 
issue_tags = Table(
    "issue_tags", 
    Base.metadata,
    #CASCADE: If issue or tag is deleted, association records are also deleted automatically
    Column("issue_id", Integer, ForeignKey("issues.issue_id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.tag_id", ondelete="CASCADE"), primary_key=True),
)  

# CORE MODELS

class Issue(Base): 
    """
    Issue model representing bug reports.
    
    Central entity with comprehensive lifecycle tracking, priority management,
    and flexible categorization through tags. Every Issue must belong to an existing project
    
    Implements a validation strategy with database constraints and application-level validators for data integryty.
    """
    __tablename__ = 'issues' 
    
    # Primary key and relationships
    issue_id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.project_id", ondelete='CASCADE'), nullable=False, index=True) 
    
    title = Column(String(100), nullable=False)
    description = Column(Text)
    log = Column(Text)
    summary = Column(Text) 
    priority = Column(String(6), nullable=False, index=True) # low, medium, high
    status = Column(String(11), nullable=False, default="open", index=True) # open, in_progress, closed
    assignee = Column(String(100), index=True) # Person responsible for resolution
    
    # Automatic timestamps
    created_at = Column(DateTime, server_default=func.now(), index=True) # Set on creation
    updated_at = Column(DateTime, onupdate=func.now(), nullable=True) # NULL on creation, auto-updated on modifications
    
    
    # Database level constraints for data integrity
    __table_args__ = (
        # Data integrity Constraints
        CheckConstraint("priority IN ('low','medium','high')", name="check_issue_priority"),
        CheckConstraint("status IN ('open','in_progress','closed')", name="check_issue_status"),
        
        # Composite indexes for common query patterns
        Index('idx_issues_status_priority', 'status', 'priority'),           # AssigneeSuggester queries
        Index('idx_issues_assignee_status', 'assignee', 'status'),          # Workload calculations

    )
    
    # SQLAlchemy relationships
    project = relationship("Project", back_populates="issues")
    tags = relationship("Tag", secondary=issue_tags, back_populates="issues")
    
    
    
class Project(Base): 
    """
    Project grouping related issues.
    
    It is the primary organizational unit for the bug tracking system. Each project acts as a container for related issues.
    Project names must be unique across the entire system
    """
    
    __tablename__ = 'projects' 
    project_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, unique=True)
    created_at = Column(DateTime, server_default=func.now())
    
    # One-to-many: one project has many issues
    # passive_deletes=True: let database handle CASCADE deletion for better performance
    issues = relationship("Issue", back_populates="project", passive_deletes=True) 
    

class Tag(Base):
    """
    Tag model for flexible categorizing and labeling of issues.
    
    Enables many-to-many relationships where issues can have multiple tags and tags can be applied to multiple issues.
    """
    __tablename__ = 'tags'
    tag_id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True, index=True) 
    
    # Many-to-many: tags can be on multiple issues, issues can have multiple tags
    issues = relationship("Issue", secondary=issue_tags, back_populates="tags")