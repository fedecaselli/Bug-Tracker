"""
Tag Generator 

This module provides functionality to automatically generate tags for issues based on their title, description, and logs. 
Tags are generated using simple keyword matching against predefined categories.

Key Features:
- Automatically generate tags based on issue content.
- Supports multiple categories such as "bug", "frontend", "backend", and "performance".
- Uses a keyword-based approach for tag generation.
"""

from typing import List
import re

class TagGenerator:
    """
    Class to handle automatic tag generation for issues.
    """
    def __init__(self):
        """
        Initialize the TagGenerator class with predefined keyword categories.
        """
        self._keywords = {
            "bug": ["error", "bug", "fail", "crash", "broken", "issue"],
            "frontend": ["ui", "frontend", "interface", "button", "form", "page"],
            "backend": ["backend", "server", "api", "database", "db"],
            "performance": ["slow", "performance", "timeout", "lag"]
        }
    
    def generate_tags(self, title: str, description: str = "", log: str = "") -> List[str]:
        """
        Generate tags based on simple keyword matching.

        Args:
            title (str): The title of the issue.
            description (str, optional): The description of the issue. Defaults to an empty string.
            log (str, optional): The log details of the issue. Defaults to an empty string.

        Returns:
            List[str]: A list of suggested tags based on the issue content.
        """
        
        # Combine the title, description, and log into a single text block
        text = f"{title} {description} {log}".lower()
        
        suggested_tags = []
        
        for tag, keywords in self._keywords.items():
            for keyword in keywords:
                if re.search(rf"\b{re.escape(keyword.lower())}\b", text):
                # If a keyword is found in the text, add the tag and stop checking further keywords
                    suggested_tags.append(tag)
                    break  
                
        return suggested_tags
    

