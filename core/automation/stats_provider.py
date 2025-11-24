"""
Stats provider for assignee suggestion.

Separates DB aggregation from scoring logic so the suggester can remain focused
on picking the best assignee. This is easily swappable or mockable in tests.
"""

from typing import List, Dict
from sqlalchemy.orm import Session
from sqlalchemy import func
from core.models import Issue, Tag


class AssigneeStatsProvider:
    """
    Default stats provider that queries the database for tag performance and workload.
    """

    def get_tag_stats(self, db: Session, issue_tags: List[str]) -> Dict[str, Dict[str, Dict[str, int]]]:
        """
        Aggregate tag performance per assignee.

        Returns a mapping: assignee -> tag -> {"resolved": int, "total": int}
        """
        stats: Dict[str, Dict[str, Dict[str, int]]] = {}

        rows = (
            db.query(
                Issue.assignee,
                Tag.name,
                Issue.status,
                func.count().label("count"),
            )
            .join(Issue.tags)
            .filter(
                Issue.assignee.isnot(None),
                Tag.name.in_(issue_tags),
            )
            .group_by(Issue.assignee, Tag.name, Issue.status)
            .all()
        )

        for assignee, tag_name, status, count in rows:
            assignee_stats = stats.setdefault(assignee, {})
            tag_counts = assignee_stats.setdefault(tag_name, {"resolved": 0, "total": 0})
            tag_counts["total"] += count
            if status == "closed":
                tag_counts["resolved"] += count

        return stats

    def get_workloads(self, db: Session) -> Dict[str, int]:
        """
        Compute open/in-progress workload per assignee.
        """
        rows = (
            db.query(Issue.assignee, func.count().label("count"))
            .filter(Issue.assignee.isnot(None), Issue.status != "closed")
            .group_by(Issue.assignee)
            .all()
        )
        return {assignee: count for assignee, count in rows}

