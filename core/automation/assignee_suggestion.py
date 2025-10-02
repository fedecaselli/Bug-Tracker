#ONLY IF status = open and priority=high
#Example: “If issue has tag frontend, suggest Alice because she resolved 70% of frontend issues.”
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_
from core.models import Issue, Tag

class AssigneeSuggester:
    def __init__(self):
        pass
    
    def suggest_assignee(self,db:Session, issue_tags:List[str],status:str, priority:str) -> Optional[str]:
        if status != "open" or priority != "high":
            return None
        
        if not issue_tags:
            return None
        
        assignees = self.get_assignees_with_tags(db, issue_tags)
        
        best_assignee = None
        best_score = -100000000 
        
        for assignee in assignees:
            tag_scores = []
            
            for tag in issue_tags:
                #resolved issues with tags
                resolved_tag_count = self.count_tags(db,tag,assignee)
                #total issue with tags
                total_tag_count = self.total_tag_count(db,tag,assignee)
                
    
                if total_tag_count > 0:
                    success_rate = (resolved_tag_count / total_tag_count) * 100
                    tag_scores.append(success_rate)
            
            if not tag_scores:
                continue #skip if the tag is not associated to that assignee
            
                #workload penalty
            avg_success_rate = sum(tag_scores) / len(tag_scores)
                
            current_workload = self.count_workload(db, assignee)
                
            score = avg_success_rate - current_workload * 10
                    
            if score > best_score:
                best_score = score
                best_assignee = assignee
                    
        return best_assignee 
            
            
            
    def auto_assign(self, db:Session,issue_id:int) -> bool:
        issue = db.query(Issue).filter(Issue.issue_id == issue_id).first()
        
        if not issue:
            return False
        
        if issue.tags:
            issue_tag_names = []
            for tag in issue.tags:
                issue_tag_names.append(tag.name)
        else:
            issue_tag_names = []
            
        suggested_assignee = self.suggest_assignee(db, issue_tag_names, issue.status, issue.priority)
        
        if suggested_assignee:
            issue.assignee = suggested_assignee
            db.commit()
            return True
        return False

         
    
    #Count closed issues with specific tags and closed status for each assignee (means they solved it) 
    def count_tags(self, db:Session, tag_name:str, assignee: str) -> int:
        return db.query(Issue).join(Issue.tags).filter(and_(Issue.assignee==assignee, Tag.name==tag_name, Issue.status=='closed')).count()
    
    def total_tag_count(self, db:Session, tag_name: str, assignee: str) -> int:
        return db.query(Issue).join(Issue.tags).filter(and_(Issue.assignee == assignee, Tag.name==tag_name)).count()

    #Count current workload not to overwhelm assignee 
    def count_workload(self,db:Session,assignee:str) -> int:
        return db.query(Issue).filter(and_(Issue.assignee==assignee,Issue.status!='closed')).count()

    def get_assignees_with_tags(self, db:Session, issue_tags: List[str]) -> List[str]:
        #SQLAlchemy returns a list of tuples, not a list of strings
        result = db.query(Issue.assignee).join(Issue.tags).filter(and_(Issue.assignee.isnot(None),Tag.name.in_(issue_tags))).distinct().all()
        return [assignee[0] for assignee in result]
        
    