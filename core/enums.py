"""Shared enums for core domain constants."""

from enum import Enum


class IssueStatus(str, Enum):
    open = "open"
    in_progress = "in_progress"
    closed = "closed"


class IssuePriority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


__all__ = ["IssueStatus", "IssuePriority"]
