"""
Tests for tag repository functions: get_or_create_tags, update_tags, 
rename_tags_everywhere, delete_tag, remove_tags_with_no_issue, etc.
"""

import pytest
from sqlalchemy.orm import Session
from core.models import Project, Issue, Tag
from core.schemas import IssueCreate
from core.repos.tags import (
    get_tag_by_name,
    get_or_create_tags,
    update_tags,
    rename_tags_everywhere,
    delete_tag,
    remove_tags_with_no_issue,
    list_tags,
    get_tag_usage_stats,
    get_tag
)
from core.repos.issues import create_issue
from core.repos.exceptions import NotFound
from core.validation import normalize_name
from core.automation import default_tag_suggester, default_assignee_strategy

def setup_project(db: Session, name: str = "TestProject") -> Project:
    """Helper to create a test project."""
    project = Project(name=name)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project

def create_test_issue(db: Session, project: Project, title: str = "Test Issue") -> Issue:
    """Helper to create a test issue."""
    issue_data = IssueCreate(
        project_id=project.project_id,
        title=title,
        description="Test description",
        priority="medium",
        status="open"
    )
    return create_issue(
        db,
        issue_data,
        tag_suggester=default_tag_suggester(),
        assignee_strategy=default_assignee_strategy(),
    )

class TestNormalizeName:
    """Test tag name normalization."""

    def test_normalize_basic(self):
        # Test basic normalization (lowercase conversion)
        assert normalize_name("Frontend") == "frontend"
        assert normalize_name("BACKEND") == "backend"
        assert normalize_name("api") == "api"

    def test_normalize_whitespace(self):
        # Test normalization removes extra whitespace
        assert normalize_name("  frontend  ") == "frontend"
        assert normalize_name("bug   fix") == "bug fix"
        assert normalize_name("  multiple   spaces  ") == "multiple spaces"

    def test_normalize_empty(self):
        # Test normalization of empty and whitespace-only strings
        assert normalize_name("") == ""
        assert normalize_name("   ") == ""
        assert normalize_name("\t\n ") == ""

class TestGetTagByName:
    """Test getting tag by name."""

    def test_get_existing_tag(self, db):
        # Test retrieving an existing tag by name (case insensitive)
        tag = Tag(name="frontend")
        db.add(tag)
        db.commit()
        found = get_tag_by_name(db, "frontend")
        assert found is not None
        assert found.name == "frontend"
        found = get_tag_by_name(db, "FRONTEND")
        assert found is not None
        assert found.name == "frontend"

    def test_get_nonexistent_tag(self, db):
        # Test retrieving a non-existent tag (should return None)
        found = get_tag_by_name(db, "nonexistent")
        assert found is None

class TestGetOrCreateTags:
    """Test get_or_create_tags function."""

    def test_empty_input(self, db):
        # Test empty input returns empty list
        tags = get_or_create_tags(db, [])
        assert tags == []

    def test_create_new_tags(self, db):
        # Test creating new tags
        tags = get_or_create_tags(db, ["frontend", "backend"])
        assert len(tags) == 2
        assert {tag.name for tag in tags} == {"frontend", "backend"}
        db_tags = db.query(Tag).all()
        assert len(db_tags) == 2

    def test_get_existing_tags(self, db):
        # Test getting existing tags
        existing1 = Tag(name="frontend")
        existing2 = Tag(name="backend")
        db.add_all([existing1, existing2])
        db.commit()
        tags = get_or_create_tags(db, ["frontend", "backend"])
        assert len(tags) == 2
        assert tags[0].tag_id == existing1.tag_id
        assert tags[1].tag_id == existing2.tag_id

    def test_mixed_existing_and_new(self, db):
        # Test mixing existing and new tags
        existing = Tag(name="frontend")
        db.add(existing)
        db.commit()
        tags = get_or_create_tags(db, ["frontend", "backend", "api"])
        assert len(tags) == 3
        assert tags[0].tag_id == existing.tag_id
        assert tags[1].name == "backend"
        assert tags[2].name == "api"

    def test_normalization_and_deduplication(self, db):
        # Test normalization and deduplication of tag names
        tags = get_or_create_tags(db, [
            "Frontend", 
            "  BACKEND  ", 
            "frontend",  # duplicate
            "back end",
            "BACK END"   # duplicate after normalization
        ])
        names = {tag.name for tag in tags}
        assert names == {"frontend", "backend", "back end"}
        assert len(tags) == 3

    def test_empty_strings_filtered(self, db):
        # Test that empty and whitespace-only tag names raise ValueError
        with pytest.raises(ValueError):
            get_or_create_tags(db, ["frontend", "", "  ", "backend"])

    def test_order_preservation(self, db):
        # Test that order of input tag names is preserved
        tags = get_or_create_tags(db, ["zulu", "alpha", "beta"])
        names = [tag.name for tag in tags]
        assert names == ["zulu", "alpha", "beta"]

class TestUpdateTags:
    """Test update_tags function."""

    def test_update_tags_new_issue(self, db):
        # Test updating tags for a new issue
        project = setup_project(db)
        issue = create_test_issue(db, project)
        update_tags(db, issue, ["frontend", "bug"])
        db.commit()
        db.refresh(issue)
        tag_names = {tag.name for tag in issue.tags}
        assert tag_names == {"frontend", "bug"}

    def test_update_tags_replace_existing(self, db):
        # Test replacing existing tags with new ones
        project = setup_project(db)
        issue = create_test_issue(db, project)
        update_tags(db, issue, ["frontend", "bug"])
        db.commit()
        db.refresh(issue)
        assert len(issue.tags) == 2
        update_tags(db, issue, ["backend", "enhancement"])
        db.commit()
        db.refresh(issue)
        tag_names = {tag.name for tag in issue.tags}
        assert tag_names == {"backend", "enhancement"}
        assert len(issue.tags) == 2

    def test_update_tags_empty_list(self, db):
        # Test removing all tags from an issue
        project = setup_project(db)
        issue = create_test_issue(db, project)
        update_tags(db, issue, ["frontend", "bug"])
        db.commit()
        db.refresh(issue)
        assert len(issue.tags) == 2
        update_tags(db, issue, [])
        db.commit()
        db.refresh(issue)
        assert len(issue.tags) == 0

    def test_update_tags_preserves_other_issues(self, db):
        # Test updating tags for one issue does not affect others
        project = setup_project(db)
        issue1 = create_test_issue(db, project, "Issue 1")
        issue2 = create_test_issue(db, project, "Issue 2")
        update_tags(db, issue1, ["frontend", "bug"])
        update_tags(db, issue2, ["frontend", "enhancement"])
        db.commit()
        update_tags(db, issue1, ["backend"])
        db.commit()
        db.refresh(issue1)
        db.refresh(issue2)
        assert {tag.name for tag in issue1.tags} == {"backend"}
        assert {tag.name for tag in issue2.tags} == {"frontend", "enhancement"}

class TestRenameTagsEverywhere:
    """Test rename_tags_everywhere function."""

    def test_rename_nonexistent_tag(self, db):
        # Test renaming a non-existent tag (should raise NotFound)
        with pytest.raises(NotFound):
            rename_tags_everywhere(db, "nonexistent", "newtag")

    def test_rename_simple(self, db):
        # Test renaming a tag and updating all issues
        project = setup_project(db)
        issue = create_test_issue(db, project)
        update_tags(db, issue, ["frontend"])
        db.commit()
        rename_tags_everywhere(db, "frontend", "ui")
        db.refresh(issue)
        assert len(issue.tags) == 1
        assert issue.tags[0].name == "ui"
        old_tag = get_tag_by_name(db, "frontend")
        assert old_tag is None

    def test_rename_to_existing_tag_merges(self, db):
        # Test renaming to an existing tag merges them
        project = setup_project(db)
        issue1 = create_test_issue(db, project, "Issue 1")
        issue2 = create_test_issue(db, project, "Issue 2")
        update_tags(db, issue1, ["frontend"])
        update_tags(db, issue2, ["ui"])
        db.commit()
        rename_tags_everywhere(db, "frontend", "ui")
        db.refresh(issue1)
        db.refresh(issue2)
        assert issue1.tags[0].name == "ui"
        assert issue2.tags[0].name == "ui"
        assert issue1.tags[0].tag_id == issue2.tags[0].tag_id
        ui_tags = db.query(Tag).filter(Tag.name == "ui").all()
        assert len(ui_tags) == 1

    def test_rename_same_name_noop(self, db):
        # Test renaming to the same name (should be no-op)
        project = setup_project(db)
        issue = create_test_issue(db, project)
        update_tags(db, issue, ["frontend"])
        db.commit()
        original_tag_id = issue.tags[0].tag_id
        rename_tags_everywhere(db, "frontend", "FRONTEND")
        db.refresh(issue)
        assert issue.tags[0].tag_id == original_tag_id
        assert issue.tags[0].name == "frontend"

    def test_rename_normalization(self, db):
        # Test renaming with normalization of names
        project = setup_project(db)
        issue = create_test_issue(db, project)
        update_tags(db, issue, ["frontend"])
        db.commit()
        rename_tags_everywhere(db, "FRONTEND", "  User Interface  ")
        db.refresh(issue)
        assert issue.tags[0].name == "user interface"

    def test_rename_empty_names_error(self, db):
        # Test renaming with empty names raises ValueError
        with pytest.raises(ValueError):
            rename_tags_everywhere(db, "", "newtag")
        with pytest.raises(ValueError):
            rename_tags_everywhere(db, "oldtag", "")

class TestDeleteTag:
    """Test delete_tag function."""

    def test_delete_existing_tag(self, db):
        # Test deleting an existing tag and removing it from issues
        project = setup_project(db)
        issue = create_test_issue(db, project)
        update_tags(db, issue, ["frontend", "backend"])
        db.commit()
        frontend_tag = get_tag_by_name(db, "frontend")
        tag_id = frontend_tag.tag_id
        result = delete_tag(db, tag_id)
        assert result is True
        db.refresh(issue)
        assert len(issue.tags) == 1
        assert issue.tags[0].name == "backend"
        deleted_tag = db.query(Tag).filter(Tag.tag_id == tag_id).first()
        assert deleted_tag is None

    def test_delete_nonexistent_tag(self, db):
        # Test deleting a non-existent tag (should raise NotFound)
        with pytest.raises(NotFound):
            delete_tag(db, 999)

    def test_delete_tag_from_multiple_issues(self, db):
        # Test deleting a tag from multiple issues
        project = setup_project(db)
        issue1 = create_test_issue(db, project, "Issue 1")
        issue2 = create_test_issue(db, project, "Issue 2")
        update_tags(db, issue1, ["frontend", "bug"])
        update_tags(db, issue2, ["frontend", "enhancement"])
        db.commit()
        frontend_tag = get_tag_by_name(db, "frontend")
        delete_tag(db, frontend_tag.tag_id)
        db.refresh(issue1)
        db.refresh(issue2)
        assert {tag.name for tag in issue1.tags} == {"bug"}
        assert {tag.name for tag in issue2.tags} == {"enhancement"}

class TestRemoveTagsWithNoIssue:
    """Test remove_tags_with_no_issue function."""

    def test_remove_orphaned_tags(self, db):
        # Test removing orphaned tags (not linked to any issue)
        orphan1 = Tag(name="orphan1")
        orphan2 = Tag(name="orphan2")
        db.add_all([orphan1, orphan2])
        project = setup_project(db)
        issue = create_test_issue(db, project)
        update_tags(db, issue, ["used_tag"])
        db.commit()
        assert db.query(Tag).count() == 3
        count = remove_tags_with_no_issue(db)
        assert count == 2
        assert db.query(Tag).count() == 1
        remaining_tag = db.query(Tag).first()
        assert remaining_tag.name == "used_tag"

    def test_remove_no_orphaned_tags(self, db):
        # Test removing when there are no orphaned tags
        project = setup_project(db)
        issue = create_test_issue(db, project)
        update_tags(db, issue, ["tag1", "tag2"])
        db.commit()
        count = remove_tags_with_no_issue(db)
        assert count == 0
        assert db.query(Tag).count() == 2

    def test_remove_tags_after_issue_deletion(self, db):
        # Test removing tags after deleting the issue they were linked to
        project = setup_project(db)
        issue = create_test_issue(db, project)
        update_tags(db, issue, ["temp_tag"])
        db.commit()
        db.delete(issue)
        db.commit()
        count = remove_tags_with_no_issue(db)
        assert count == 1
        assert db.query(Tag).count() == 0

class TestListTags:
    """Test list_tags function."""

    def test_list_empty(self, db):
        # Test listing tags when none exist
        tags = list_tags(db)
        assert tags == []

    def test_list_all_tags(self, db):
        # Test listing all tags
        project = setup_project(db)
        issue = create_test_issue(db, project)
        update_tags(db, issue, ["alpha", "beta", "gamma"])
        db.commit()
        tags = list_tags(db)
        assert len(tags) == 3
        names = {tag.name for tag in tags}
        assert names == {"alpha", "beta", "gamma"}

    def test_list_with_pagination(self, db):
        # Test listing tags with pagination
        project = setup_project(db)
        issue = create_test_issue(db, project)
        tag_names = [f"tag{i:02d}" for i in range(10)]
        update_tags(db, issue, tag_names)
        db.commit()
        page1 = list_tags(db, skip=0, limit=3)
        assert len(page1) == 3
        page2 = list_tags(db, skip=3, limit=3)
        assert len(page2) == 3
        page1_ids = {tag.tag_id for tag in page1}
        page2_ids = {tag.tag_id for tag in page2}
        assert len(page1_ids.intersection(page2_ids)) == 0

class TestGetTagUsageStats:
    """Test get_tag_usage_stats function."""

    def test_usage_stats_empty(self, db):
        # Test usage stats when no tags exist
        stats = get_tag_usage_stats(db)
        assert stats == []

    def test_usage_stats_single_tag(self, db):
        # Test usage stats for a single tag
        project = setup_project(db)
        issue = create_test_issue(db, project)
        update_tags(db, issue, ["frontend"])
        db.commit()
        stats = get_tag_usage_stats(db)
        assert len(stats) == 1
        assert stats[0]["name"] == "frontend"
        assert stats[0]["issue_count"] == 1

    def test_usage_stats_multiple_issues(self, db):
        # Test usage stats for multiple issues and tags
        project = setup_project(db)
        issue1 = create_test_issue(db, project, "Issue 1")
        issue2 = create_test_issue(db, project, "Issue 2")
        issue3 = create_test_issue(db, project, "Issue 3")
        update_tags(db, issue1, ["frontend", "bug"])
        update_tags(db, issue2, ["frontend", "enhancement"])
        update_tags(db, issue3, ["backend"])
        db.commit()
        stats = get_tag_usage_stats(db)
        assert len(stats) == 4
        stats_dict = {stat["name"]: stat["issue_count"] for stat in stats}
        assert stats_dict["frontend"] == 2
        assert stats_dict["bug"] == 1
        assert stats_dict["enhancement"] == 1
        assert stats_dict["backend"] == 1

    def test_usage_stats_orphaned_tags(self, db):
        # Test usage stats includes orphaned tags with zero count
        orphan = Tag(name="orphan")
        db.add(orphan)
        project = setup_project(db)
        issue = create_test_issue(db, project)
        update_tags(db, issue, ["used"])
        db.commit()
        stats = get_tag_usage_stats(db)
        assert len(stats) == 2
        stats_dict = {stat["name"]: stat["issue_count"] for stat in stats}
        assert stats_dict["orphan"] == 0
        assert stats_dict["used"] == 1

class TestGetTag:
    """Test get_tag function."""

    def test_get_existing_tag_by_id(self, db):
        # Test getting a tag by its ID
        tag = Tag(name="test_tag")
        db.add(tag)
        db.commit()
        db.refresh(tag)
        fetched = get_tag(db, tag.tag_id)
        assert fetched.tag_id == tag.tag_id
        assert fetched.name == "test_tag"

    def test_get_nonexistent_tag_by_id(self, db):
        # Test getting a non-existent tag by ID (should raise NotFound)
        with pytest.raises(NotFound):
            get_tag(db, 999)

class TestIntegrationScenarios:
    """Integration tests with realistic tag usage scenarios."""

    def test_complete_tag_lifecycle(self, db):
        # Test a complete tag management workflow
        project = setup_project(db)
        issue = create_test_issue(db, project, "Main Issue")
        update_tags(db, issue, ["frontend", "bug", "high-priority"])
        db.commit()
        assert len(issue.tags) == 3
        rename_tags_everywhere(db, "high-priority", "urgent")
        db.refresh(issue)
        tag_names = {tag.name for tag in issue.tags}
        assert "urgent" in tag_names
        assert "high-priority" not in tag_names
        issue2 = create_test_issue(db, project, "Second Issue")
        update_tags(db, issue2, ["backend", "urgent"])
        db.commit()
        stats = get_tag_usage_stats(db)
        stats_dict = {stat["name"]: stat["issue_count"] for stat in stats}
        assert stats_dict["urgent"] == 2
        assert stats_dict["frontend"] == 1
        assert stats_dict["backend"] == 1
        frontend_tag = get_tag_by_name(db, "frontend")
        delete_tag(db, frontend_tag.tag_id)
        orphan_count = remove_tags_with_no_issue(db)
        assert orphan_count == 0

    def test_tag_merge_scenario(self, db):
        # Test merging tags through rename operation
        project = setup_project(db)
        issue1 = create_test_issue(db, project, "Issue 1")
        issue2 = create_test_issue(db, project, "Issue 2")
        issue3 = create_test_issue(db, project, "Issue 3")
        update_tags(db, issue1, ["ui", "bug"])
        update_tags(db, issue2, ["frontend", "enhancement"])
        update_tags(db, issue3, ["ui", "frontend", "critical"])
        db.commit()
        initial_tag_count = db.query(Tag).count()
        rename_tags_everywhere(db, "frontend", "ui")
        final_tag_count = db.query(Tag).count()
        assert final_tag_count == initial_tag_count - 1
        db.refresh(issue1)
        db.refresh(issue2)
        db.refresh(issue3)
        for issue in [issue1, issue2, issue3]:
            tag_names = {tag.name for tag in issue.tags}
            assert "ui" in tag_names
            assert "frontend" not in tag_names

    def test_normalization_edge_cases(self, db):
        # Test edge cases in tag name normalization
        project = setup_project(db)
        issue = create_test_issue(db, project)
        update_tags(db, issue, [
            "  Normal  ",
            "UPPER CASE",
            "  multi    word   tag  ",
            "Tab\tSeparated",
            "Mixed   CASE   text"
        ])
        db.commit()
        expected_names = {
            "normal",
            "upper case",
            "multi word tag",
            "tab separated",
            "mixed case text"
        }
        db.refresh(issue)
        actual_names = {tag.name for tag in issue.tags}
        assert actual_names == expected_names
        
