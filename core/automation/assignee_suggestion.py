"""
Assignee Suggestion Logic 

This module provides functionality to suggest the best assignee for an issue based on their expertise, workload, and success rate with specific tags.

The suggestion logic applies only to issues with:
- Status = "open": Only unresolved issues need assignees.
- Priority = "high": High-priority requires immediate attention from the most experienced.

Key Features:
- Suggest the best assignee based on tag expertise and workload.
- Automatically assign an issue to the best assignee.
- Calculate success rates, workload, and tag associations for assignees.
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_
from core.models import Issue, Tag

class AssigneeSuggester:
    """
    Class to handle assignee suggestion logic.
    """
    
    def __init__(self):
        """
        Initialize the AssigneeSuggester class.
        """
        pass
    
    def suggest_assignee(self,db:Session, issue_tags:List[str],status:str, priority:str) -> Optional[str]:
        """
        Suggest the best assignee for an issue based on tag expertise and workload.

        Args:
            db (Session): Database session.
            issue_tags (List[str]): List of tags associated with the issue.
            status (str): Status of the issue (must be "open").
            priority (str): Priority of the issue (must be "high").

        Returns:
            Optional[str]: The best assignee's name, or None if no suitable assignee is found.
        """
        # Only suggest assignees for open, high-priority issues
        if status != "open" or priority != "high":
            return None
        
        if not issue_tags:
            return None
        
        # Retrieve all assignees associated with the issue's tags
        assignees = self._get_assignees_with_tags(db, issue_tags)
        
        best_assignee = None
        best_score = float('-inf')
        
        # Evaluate each assignee
        for assignee in assignees:
            tag_scores = []

            # Calculate success rate for each tag
            for tag in issue_tags:
                resolved_tag_count = self._count_tags(db,tag,assignee)
                total_tag_count = self._total_tag_count(db,tag,assignee)
                
    
                if total_tag_count > 0:
                    success_rate = (resolved_tag_count / total_tag_count) * 100
                    tag_scores.append(success_rate)
                    
            # Skip assignees with no relevant tag associations
            if not tag_scores:
                continue 
            
            # Calculate the average success rate and apply a workload penalty
            avg_success_rate = sum(tag_scores) / len(tag_scores)
            current_workload = self._count_workload(db, assignee)
            score = avg_success_rate - current_workload * 10 # Penalize for high workload

            # Update the best assignee if the current one has a higher score
            if score > best_score:
                best_score = score
                best_assignee = assignee
                    
        return best_assignee 
            
            
            
    def auto_assign(self, db:Session,issue_id:int) -> bool:
        """
        Automatically assign an issue to the best assignee.

        Args:
            db (Session): Database session.
            issue_id (int): ID of the issue to assign.

        Returns:
            bool: True if an assignee was successfully assigned, False otherwise.
        """
        issue = db.query(Issue).filter(Issue.issue_id == issue_id).first()
        
        if not issue:
            return False
        
        # Extract tag names associated with the issue
        if issue.tags:
            issue_tag_names = []
            for tag in issue.tags:
                issue_tag_names.append(tag.name)
        else:
            issue_tag_names = []

        # Suggest the best assignee
        suggested_assignee = self.suggest_assignee(db, issue_tag_names, issue.status, issue.priority)
        

        # Assign the issue if a suitable assignee is found
        if suggested_assignee:
            issue.assignee = suggested_assignee
            db.commit()
            return True
        return False

         
    
    def _count_tags(self, db:Session, tag_name:str, assignee: str) -> int:
        """
        Count the number of closed issues with a specific tag resolved by an assignee.

        Args:
            db (Session): Database session.
            tag_name (str): Name of the tag.
            assignee (str): Name of the assignee.

        Returns:
            int: Number of closed issues with the specified tag resolved by the assignee.
        """
        return db.query(Issue).join(Issue.tags).filter(and_(Issue.assignee==assignee, Tag.name==tag_name, Issue.status=='closed')).count()
    
    def _total_tag_count(self, db:Session, tag_name: str, assignee: str) -> int:
        """
        Count the total number of issues with a specific tag assigned to an assignee.

        Args:
            db (Session): Database session.
            tag_name (str): Name of the tag.
            assignee (str): Name of the assignee.

        Returns:
            int: Total number of issues with the specified tag assigned to the assignee.
        """
        return db.query(Issue).join(Issue.tags).filter(and_(Issue.assignee == assignee, Tag.name==tag_name)).count()

    #Count current workload not to overwhelm assignee 
    def _count_workload(self,db:Session,assignee:str) -> int:
        """
        Count the number of open or in-progress issues assigned to an assignee.

        Args:
            db (Session): Database session.
            assignee (str): Name of the assignee.

        Returns:
            int: Number of open or in-progress issues assigned to the assignee.
        """
        return db.query(Issue).filter(and_(Issue.assignee==assignee,Issue.status!='closed')).count()

    def _get_assignees_with_tags(self, db:Session, issue_tags: List[str]) -> List[str]:
        """
        Retrieve a list of assignees associated with specific tags.

        Args:
            db (Session): Database session.
            issue_tags (List[str]): List of tag names.

        Returns:
            List[str]: List of assignee names associated with the specified tags.
        """
        #SQLAlchemy returns a list of tuples, not a list of strings
        result = db.query(Issue.assignee).join(Issue.tags).filter(and_(Issue.assignee.isnot(None),Tag.name.in_(issue_tags))).distinct().all()
        return [assignee[0] for assignee in result]
        
    