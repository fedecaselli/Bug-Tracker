"""
Automation package for the bug tracker.

Exposes default implementations and injectable interfaces/factories so core
logic can depend on abstractions instead of concrete classes.
"""

from .tag_generator import TagGenerator
from .assignee_suggestion import AssigneeSuggester
from .interfaces import TagSuggester, AssigneeStrategy


def default_tag_suggester() -> TagSuggester:
    """Factory for the default tag suggester implementation."""
    return TagGenerator()


def default_assignee_strategy() -> AssigneeStrategy:
    """Factory for the default assignee strategy implementation."""
    return AssigneeSuggester()


__all__ = [
    "TagGenerator",
    "AssigneeSuggester",
    "TagSuggester",
    "AssigneeStrategy",
    "default_tag_suggester",
    "default_assignee_strategy",
]
