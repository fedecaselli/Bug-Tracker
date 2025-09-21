from sqlalchemy import Column, Integer, String, CheckConstraint, Text, DateTime, func, ForeignKey, Table
from sqlalchemy.orm import validates, relationship
from .db import Base 

'''
when finishing setting up the database, check that all enforcements on data work correctly
'''

class Issue(Base): 
    __tablename__ = 'issues' 
    
    issue_id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.project_id", ondelete='CASCADE'), nullable=False) #every issue_id must point to valid project_id
    #CASCADE: if I delete a project all the issues are deleted too
    title = Column(String(100), nullable=False)
    description = Column(Text)
    log = Column(Text)
    summary = Column(Text) #AI summary
    priority = Column(String(6), nullable=False) 
    status = Column(String(11), nullable=False, default="open") 
    assignee = Column(String(100))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now(), nullable=True) # NULL at insert, auto-update later
    
    
    #constraints
    __table_args__ = (
        #DB-level contraint: enforce low, medium, high
        CheckConstraint("priority IN ('low','medium','high')", name="check_issue_priority"),
        #DB-level contraint: enforce open, in_progress, closed
        CheckConstraint("status IN ('open','in_progress','closed')", name="check_issue_status"),
    )
    
    #relationships
    project = relationship("Project", back_populates="issues")
    tags = relationship("Tag", secondary="issues_tags", back_populates="issues")
    
    
    """
TAKE INTO CONSIDERATION:
onupdate=func.now():
UPDATE issues
the column only updates when an SQL UPDATE command happens (via SQLAlchemy).
    """
    
    #App-level validation
    @validates("priority") #column to validate
    def validate_priority(self, key, value):
        if value not in ("low", "medium", "high"):
            raise ValueError("Please choose either low, medium or high")
        return value
    
    @validates("status") #column to validate
    def validate_status(self, key, value):
        if value not in ("open", "in_progress", "closed"):
            raise ValueError("Please choose either open, in_progress or closed")
        return value
    
    
class Project(Base): 
    __tablename__ = 'projects' 
    project_id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False, unique=True)
    created_at = Column(DateTime, server_default=func.now())
    
    issues = relationship("Issue", back_populates="project")
    
      
#Filter by tags and asignee, status and priority

#ASSOCIATION, no extra data so no need to do full ORM model with class Issue_Tag 
issue_tags = Table(
    "issue_tags",
    Base.metadata,
    Column("issue_id", Integer, ForeignKey("issues.issue_id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.tag_id", ondelete="CASCADE"), primary_key=True),
)


class Tag(Base):
    __tablename__ = 'tags'
    tag_id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    

    issues = relationship("Issue", secondary=issue_tags, back_populates="tags")
    
   
   


    
    
#One-to-many: project and issues
#Many-to-many: tags and issues



#FILTERING IDEA
''' 
SELECT * FROM issues WHERE tags LIKE '%"frontend"%';
SELECT * FROM issues WHERE assignee = 'Alice'; !alice and Alice are considered different
'''


#INDEXES for speed up lookups when filtering 







