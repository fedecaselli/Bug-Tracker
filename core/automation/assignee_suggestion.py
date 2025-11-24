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
from core.repos.exceptions import NotFound
from core.automation.stats_provider import AssigneeStatsProvider

class AssigneeSuggester:
    """
    Class to handle assignee suggestion logic.
    """
    
    def __init__(self, stats_provider: AssigneeStatsProvider | None = None):
        """
        Initialize the AssigneeSuggester class.
        """
        self.stats_provider = stats_provider or AssigneeStatsProvider()
    
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
        
        tag_stats = self.stats_provider.get_tag_stats(db, issue_tags)
        workloads = self.stats_provider.get_workloads(db)

        best_assignee = None
        best_score = float('-inf')
        
        # Evaluate each assignee
        for assignee, stats_per_tag in tag_stats.items():
            tag_scores = []

            # Calculate success rate for each tag
            for tag in issue_tags:
                counts = stats_per_tag.get(tag)
                if counts and counts["total"] > 0:
                    success_rate = (counts["resolved"] / counts["total"]) * 100
                    tag_scores.append(success_rate)
                    
            # Skip assignees with no relevant tag associations
            if not tag_scores:
                continue 
            
            # Calculate the average success rate and apply a workload penalty
            avg_success_rate = sum(tag_scores) / len(tag_scores)
            current_workload = workloads.get(assignee, 0)
            score = avg_success_rate - current_workload * 10 # Penalize for high workload

            # Update the best assignee if the current one has a higher score
            if score > best_score:
                best_score = score
                best_assignee = assignee
                    
        return best_assignee 
            
            
            


    def auto_assign(self, db: Session, issue_id: int) -> bool:
        """
        Automatically assign an issue to the best assignee.

        Args:
            db (Session): Database session.
            issue_id (int): ID of the issue to assign.

        Returns:
            bool: True if an assignee was successfully assigned.
            
        Raises:
            NotFound: If no suitable assignee is found for the issue.
        """
        issue = db.query(Issue).filter(Issue.issue_id == issue_id).first()
        
        if not issue:
            raise NotFound(f"Issue with ID {issue_id} not found")
        
        # Extract tag names associated with the issue
        if issue.tags:
            issue_tag_names = [tag.name for tag in issue.tags]
        else:
            issue_tag_names = []

        # Suggest the best assignee
        suggested_assignee = self.suggest_assignee(db, issue_tag_names, issue.status, issue.priority)
        
        # Assign the issue if a suitable assignee is found
        if suggested_assignee:
            issue.assignee = suggested_assignee
            db.commit()
            return True
        else:
            # Raise exception with detailed message
            raise NotFound(f"No suitable assignee found for issue {issue_id} with tags {issue_tag_names}, status '{issue.status}', and priority '{issue.priority}'")

         
    
