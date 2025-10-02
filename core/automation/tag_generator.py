from typing import List
import re

class TagGenerator:
    def __init__(self):
        self.keywords = {
            "bug": ["error", "bug", "fail", "crash", "broken", "issue"],
            "frontend": ["ui", "frontend", "interface", "button", "form", "page"],
            "backend": ["backend", "server", "api", "database", "db"],
            "performance": ["slow", "performance", "timeout", "lag"]
        }
    
    def generate_tags(self, title: str, description: str = "", log: str = "") -> List[str]:
        """Generate tags based on simple keyword matching"""
        text = f"{title} {description} {log}".lower()
        
        suggested_tags = []
        
        for tag, keywords in self.keywords.items():
            for keyword in keywords:
                if keyword in text:
                    suggested_tags.append(tag)
                    break  # Only add the tag once per category
          
        return suggested_tags