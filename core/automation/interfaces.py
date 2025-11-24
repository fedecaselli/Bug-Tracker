"""
Interfaces for automation components used by the bug tracker.

These Protocols allow dependency injection in repositories and APIs, keeping
core logic decoupled from specific implementations such as AI-based tag
suggesters or assignee strategies.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable
from sqlalchemy.orm import Session


@runtime_checkable
class TagSuggester(Protocol):
    def generate_tags(self, *, title: str, description: str, log: str) -> list[str]:
        ...


@runtime_checkable
class AssigneeStrategy(Protocol):
    def suggest_assignee(self, db: Session, tags: list[str], status: str, priority: str) -> str | None:
        ...

    def auto_assign(self, db: Session, issue_id: int) -> bool:
        ...

