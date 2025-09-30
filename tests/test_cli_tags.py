"""
Comprehensive CLI tests for tag functionality.

This module tests all tag-related CLI commands and their integration with issues.
It ensures that CLI parameters are parsed correctly, error handling works properly,
and the tag system functions correctly from the user interface layer.
"""

import pytest
from unittest.mock import patch, Mock, MagicMock
from typer.testing import CliRunner
from cli.main import cli_app
from core.models import Project, Issue, Tag
from core.schemas import ProjectCreate, IssueCreate
from core.repos.exceptions import NotFound, AlreadyExists
import sys
from io import StringIO


runner = CliRunner()


class TestTagsCLI:
    """Test CLI tag commands: list, rename, delete, cleanup"""

    def test_tags_list_empty(self, db):
        """Test listing tags when no tags exist"""
        with patch('cli.main.session_scope') as mock_session:
            mock_session.return_value.__enter__.return_value = db
            mock_session.return_value.__exit__.return_value = None
            
            with patch('cli.main.repo_list_tags') as mock_list:
                mock_list.return_value = []
                
                result = runner.invoke(cli_app, ["tags", "list"])
                assert result.exit_code == 0
                assert "No tags found" in result.output
                mock_list.assert_called_once_with(db, skip=0, limit=100)

    def test_tags_list_with_tags(self, db):
        """Test listing tags when tags exist"""
        with patch('cli.main.session_scope') as mock_session:
            mock_session.return_value.__enter__.return_value = db
            mock_session.return_value.__exit__.return_value = None
            
            # Mock tag objects
            mock_tag1 = Mock()
            mock_tag1.tag_id = 1
            mock_tag1.name = "bug"
            mock_tag2 = Mock()
            mock_tag2.tag_id = 2
            mock_tag2.name = "feature"
            
            with patch('cli.main.repo_list_tags') as mock_list:
                mock_list.return_value = [mock_tag1, mock_tag2]
                
                result = runner.invoke(cli_app, ["tags", "list"])
                assert result.exit_code == 0
                assert "Available Tags:" in result.output
                assert "ID: 1\tName: bug" in result.output
                assert "ID: 2\tName: feature" in result.output
                mock_list.assert_called_once_with(db, skip=0, limit=100)

    def test_tags_list_with_pagination(self, db):
        """Test tag listing with skip and limit parameters"""
        with patch('cli.main.session_scope') as mock_session:
            mock_session.return_value.__enter__.return_value = db
            mock_session.return_value.__exit__.return_value = None
            
            with patch('cli.main.repo_list_tags') as mock_list:
                mock_list.return_value = []
                
                result = runner.invoke(cli_app, ["tags", "list", "--skip", "10", "--limit", "50"])
                assert result.exit_code == 0
                mock_list.assert_called_once_with(db, skip=10, limit=50)

    def test_tags_list_with_stats_empty(self, db):
        """Test listing tag statistics when no tags exist"""
        with patch('cli.main.session_scope') as mock_session:
            mock_session.return_value.__enter__.return_value = db
            mock_session.return_value.__exit__.return_value = None
            
            with patch('cli.main.repo_get_tag_usage_stats') as mock_stats:
                mock_stats.return_value = []
                
                result = runner.invoke(cli_app, ["tags", "list", "--stats"])
                assert result.exit_code == 0
                assert "No tags found" in result.output
                mock_stats.assert_called_once_with(db)

    def test_tags_list_with_stats(self, db):
        """Test listing tag statistics when tags exist"""
        with patch('cli.main.session_scope') as mock_session:
            mock_session.return_value.__enter__.return_value = db
            mock_session.return_value.__exit__.return_value = None
            
            mock_stats = [
                {'tag_name': 'bug', 'usage_count': 5},
                {'tag_name': 'feature', 'usage_count': 3}
            ]
            
            with patch('cli.main.repo_get_tag_usage_stats') as mock_get_stats:
                mock_get_stats.return_value = mock_stats
                
                result = runner.invoke(cli_app, ["tags", "list", "--stats"])
                assert result.exit_code == 0
                assert "Tag Usage Statistics:" in result.output
                assert "bug\t\t5" in result.output
                assert "feature\t\t3" in result.output
                mock_get_stats.assert_called_once_with(db)

    def test_tags_rename_success(self, db):
        """Test successful tag renaming"""
        with patch('cli.main.session_scope') as mock_session:
            mock_session.return_value.__enter__.return_value = db
            mock_session.return_value.__exit__.return_value = None
            
            with patch('cli.main.repo_rename_tags_everywhere') as mock_rename:
                result = runner.invoke(cli_app, ["tags", "rename", "--old-name", "bug", "--new-name", "defect"])
                assert result.exit_code == 0
                assert "Tag 'bug' renamed to 'defect' across all issues" in result.output
                mock_rename.assert_called_once_with(db, "bug", "defect")

    def test_tags_rename_not_found(self, db):
        """Test tag renaming when tag doesn't exist"""
        with patch('cli.main.session_scope') as mock_session:
            mock_session.return_value.__enter__.return_value = db
            mock_session.return_value.__exit__.return_value = None
            
            with patch('cli.main.repo_rename_tags_everywhere') as mock_rename:
                mock_rename.side_effect = NotFound("Tag 'nonexistent' not found")
                
                result = runner.invoke(cli_app, ["tags", "rename", "--old-name", "nonexistent", "--new-name", "defect"])
                assert result.exit_code == 1
                assert "Error: Tag 'nonexistent' not found" in result.output
                mock_rename.assert_called_once_with(db, "nonexistent", "defect")

    def test_tags_delete_success(self, db):
        """Test successful tag deletion"""
        with patch('cli.main.session_scope') as mock_session:
            mock_session.return_value.__enter__.return_value = db
            mock_session.return_value.__exit__.return_value = None
            
            with patch('cli.main.repo_delete_tag') as mock_delete:
                mock_delete.return_value = True
                
                result = runner.invoke(cli_app, ["tags", "delete", "--id", "1"])
                assert result.exit_code == 0
                assert "Tag 1 deleted from all issues" in result.output
                mock_delete.assert_called_once_with(db, 1)

    def test_tags_delete_not_found(self, db):
        """Test tag deletion when tag doesn't exist"""
        with patch('cli.main.session_scope') as mock_session:
            mock_session.return_value.__enter__.return_value = db
            mock_session.return_value.__exit__.return_value = None
            
            with patch('cli.main.repo_delete_tag') as mock_delete:
                mock_delete.side_effect = NotFound("Tag with id 999 not found")
                
                result = runner.invoke(cli_app, ["tags", "delete", "--id", "999"])
                assert result.exit_code == 1
                assert "Error: Tag with id 999 not found" in result.output
                mock_delete.assert_called_once_with(db, 999)

    def test_tags_cleanup_success(self, db):
        """Test successful tag cleanup"""
        with patch('cli.main.session_scope') as mock_session:
            mock_session.return_value.__enter__.return_value = db
            mock_session.return_value.__exit__.return_value = None
            
            with patch('cli.main.repo_remove_tags_with_no_issue') as mock_cleanup:
                mock_cleanup.return_value = 3
                
                result = runner.invoke(cli_app, ["tags", "cleanup"])
                assert result.exit_code == 0
                assert "Cleaned up 3 unused tags" in result.output
                mock_cleanup.assert_called_once_with(db)

    def test_tags_cleanup_no_orphans(self, db):
        """Test tag cleanup when no orphaned tags exist"""
        with patch('cli.main.session_scope') as mock_session:
            mock_session.return_value.__enter__.return_value = db
            mock_session.return_value.__exit__.return_value = None
            
            with patch('cli.main.repo_remove_tags_with_no_issue') as mock_cleanup:
                mock_cleanup.return_value = 0
                
                result = runner.invoke(cli_app, ["tags", "cleanup"])
                assert result.exit_code == 0
                assert "Cleaned up 0 unused tags" in result.output
                mock_cleanup.assert_called_once_with(db)


class TestIssuesCLIWithTags:
    """Test issue CLI commands with tag integration"""

    def test_issues_create_with_tags(self, db):
        """Test creating issue with tags"""
        with patch('cli.main.session_scope') as mock_session:
            mock_session.return_value.__enter__.return_value = db
            mock_session.return_value.__exit__.return_value = None
            
            mock_issue = Mock()
            mock_issue.issue_id = 1
            mock_issue.title = "Test Issue"
            
            with patch('cli.main.repo_create_issue') as mock_create:
                mock_create.return_value = mock_issue
                
                result = runner.invoke(cli_app, [
                    "issues", "create",
                    "--project", "1",
                    "--title", "Test Issue",
                    "--priority", "high",
                    "--status", "open",
                    "--tags", "bug,urgent,frontend"
                ])
                
                assert result.exit_code == 0
                assert "Issue 1 successfully created with title Test Issue" in result.output
                
                # Verify the correct IssueCreate was called
                mock_create.assert_called_once()
                args, kwargs = mock_create.call_args
                issue_create = args[1]  # Second argument is IssueCreate
                assert issue_create.tag_names == ["bug", "urgent", "frontend"]

    def test_issues_create_with_empty_tags(self, db):
        """Test creating issue with empty tag string"""
        with patch('cli.main.session_scope') as mock_session:
            mock_session.return_value.__enter__.return_value = db
            mock_session.return_value.__exit__.return_value = None
            
            mock_issue = Mock()
            mock_issue.issue_id = 1
            mock_issue.title = "Test Issue"
            
            with patch('cli.main.repo_create_issue') as mock_create:
                mock_create.return_value = mock_issue
                
                result = runner.invoke(cli_app, [
                    "issues", "create",
                    "--project", "1",
                    "--title", "Test Issue",
                    "--priority", "high",
                    "--status", "open",
                    "--tags", ""
                ])
                
                assert result.exit_code == 0
                
                # Verify empty tags are handled correctly
                mock_create.assert_called_once()
                args, kwargs = mock_create.call_args
                issue_create = args[1]
                assert issue_create.tag_names == []

    def test_issues_create_with_whitespace_tags(self, db):
        """Test creating issue with tags containing whitespace"""
        with patch('cli.main.session_scope') as mock_session:
            mock_session.return_value.__enter__.return_value = db
            mock_session.return_value.__exit__.return_value = None
            
            mock_issue = Mock()
            mock_issue.issue_id = 1
            mock_issue.title = "Test Issue"
            
            with patch('cli.main.repo_create_issue') as mock_create:
                mock_create.return_value = mock_issue
                
                result = runner.invoke(cli_app, [
                    "issues", "create",
                    "--project", "1",
                    "--title", "Test Issue",
                    "--priority", "high",
                    "--status", "open",
                    "--tags", " bug , urgent,  frontend , "
                ])
                
                assert result.exit_code == 0
                
                # Verify whitespace is trimmed correctly
                mock_create.assert_called_once()
                args, kwargs = mock_create.call_args
                issue_create = args[1]
                assert issue_create.tag_names == ["bug", "urgent", "frontend"]

    def test_issues_create_without_tags(self, db):
        """Test creating issue without any tags"""
        with patch('cli.main.session_scope') as mock_session:
            mock_session.return_value.__enter__.return_value = db
            mock_session.return_value.__exit__.return_value = None
            
            mock_issue = Mock()
            mock_issue.issue_id = 1
            mock_issue.title = "Test Issue"
            
            with patch('cli.main.repo_create_issue') as mock_create:
                mock_create.return_value = mock_issue
                
                result = runner.invoke(cli_app, [
                    "issues", "create",
                    "--project", "1",
                    "--title", "Test Issue",
                    "--priority", "high",
                    "--status", "open"
                ])
                
                assert result.exit_code == 0
                
                # Verify no tags are passed
                mock_create.assert_called_once()
                args, kwargs = mock_create.call_args
                issue_create = args[1]
                assert issue_create.tag_names == []

    def test_issues_update_tags(self, db):
        """Test updating issue tags"""
        with patch('cli.main.session_scope') as mock_session:
            mock_session.return_value.__enter__.return_value = db
            mock_session.return_value.__exit__.return_value = None
            
            mock_issue = Mock()
            mock_issue.issue_id = 1
            
            with patch('cli.main.repo_update_issue') as mock_update:
                mock_update.return_value = mock_issue
                
                result = runner.invoke(cli_app, [
                    "issues", "update",
                    "--id", "1",
                    "--tags", "new-tag,updated"
                ])
                
                assert result.exit_code == 0
                assert "Issue 1 updated" in result.output
                
                # Verify the correct IssueUpdate was called
                mock_update.assert_called_once()
                args, kwargs = mock_update.call_args
                issue_update = args[2]  # Third argument is IssueUpdate (db, issue_id, data)
                assert issue_update.tag_names == ["new-tag", "updated"]

    def test_issues_update_clear_tags(self, db):
        """Test clearing all tags from an issue"""
        with patch('cli.main.session_scope') as mock_session:
            mock_session.return_value.__enter__.return_value = db
            mock_session.return_value.__exit__.return_value = None
            
            mock_issue = Mock()
            mock_issue.issue_id = 1
            
            with patch('cli.main.repo_update_issue') as mock_update:
                mock_update.return_value = mock_issue
                
                result = runner.invoke(cli_app, [
                    "issues", "update",
                    "--id", "1",
                    "--tags", ""
                ])
                
                assert result.exit_code == 0
                
                # Verify tags are cleared
                mock_update.assert_called_once()
                args, kwargs = mock_update.call_args
                issue_update = args[2]  # Third argument is IssueUpdate (db, issue_id, data)
                assert issue_update.tag_names == []

    def test_issues_list_filter_by_tags_any(self, db):
        """Test listing issues filtered by tags (has any of specified tags)"""
        with patch('cli.main.session_scope') as mock_session:
            mock_session.return_value.__enter__.return_value = db
            mock_session.return_value.__exit__.return_value = None
            
            # Mock issue with tags
            mock_tag1 = Mock()
            mock_tag1.name = "bug"
            mock_tag2 = Mock()
            mock_tag2.name = "urgent"
            
            mock_issue = Mock()
            mock_issue.issue_id = 1
            mock_issue.title = "Test Issue"
            mock_issue.description = "Test description"
            mock_issue.log = None
            mock_issue.summary = None
            mock_issue.priority = "high"
            mock_issue.status = "open"
            mock_issue.assignee = "user1"
            mock_issue.tags = [mock_tag1, mock_tag2]
            
            with patch('cli.main.repo_list_issues') as mock_list:
                mock_list.return_value = [mock_issue]
                
                result = runner.invoke(cli_app, [
                    "issues", "list",
                    "--tags", "bug,feature",
                    "--tags-match-any"  # Use --tags-match-any to set to False
                ])
                
                assert result.exit_code == 0
                assert "Test Issue" in result.output
                assert "bug, urgent" in result.output
                
                # Verify the correct filter was applied
                mock_list.assert_called_once()
                args, kwargs = mock_list.call_args
                assert kwargs['tags'] == ["bug", "feature"]
                assert kwargs['tags_match_all'] == False

    def test_issues_list_filter_by_tags_all(self, db):
        """Test listing issues filtered by tags (has all specified tags)"""
        with patch('cli.main.session_scope') as mock_session:
            mock_session.return_value.__enter__.return_value = db
            mock_session.return_value.__exit__.return_value = None
            
            with patch('cli.main.repo_list_issues') as mock_list:
                mock_list.return_value = []
                
                result = runner.invoke(cli_app, [
                    "issues", "list",
                    "--tags", "bug,urgent",
                    "--tags-match-all"  # Default is True, so this explicit flag should work
                ])
                
                assert result.exit_code == 0
                assert "No registered issues" in result.output
                
                # Verify the correct filter was applied
                mock_list.assert_called_once()
                args, kwargs = mock_list.call_args
                assert kwargs['tags'] == ["bug", "urgent"]
                assert kwargs['tags_match_all'] == True

    def test_issues_list_without_tag_filter(self, db):
        """Test listing issues without tag filter"""
        with patch('cli.main.session_scope') as mock_session:
            mock_session.return_value.__enter__.return_value = db
            mock_session.return_value.__exit__.return_value = None
            
            with patch('cli.main.repo_list_issues') as mock_list:
                mock_list.return_value = []
                
                result = runner.invoke(cli_app, ["issues", "list"])
                
                assert result.exit_code == 0
                
                # Verify no tag filter was applied
                mock_list.assert_called_once()
                args, kwargs = mock_list.call_args
                assert kwargs['tags'] is None

    def test_issues_list_display_tags(self, db):
        """Test that issue listing displays tags correctly"""
        with patch('cli.main.session_scope') as mock_session:
            mock_session.return_value.__enter__.return_value = db
            mock_session.return_value.__exit__.return_value = None
            
            # Mock issue without tags
            mock_issue1 = Mock()
            mock_issue1.issue_id = 1
            mock_issue1.title = "Issue without tags"
            mock_issue1.description = "Test"
            mock_issue1.log = None
            mock_issue1.summary = None
            mock_issue1.priority = "low"
            mock_issue1.status = "open"
            mock_issue1.assignee = None
            mock_issue1.tags = None
            
            # Mock issue with tags
            mock_tag = Mock()
            mock_tag.name = "bug"
            mock_issue2 = Mock()
            mock_issue2.issue_id = 2
            mock_issue2.title = "Issue with tags"
            mock_issue2.description = "Test"
            mock_issue2.log = None
            mock_issue2.summary = None
            mock_issue2.priority = "high"
            mock_issue2.status = "open"
            mock_issue2.assignee = "user1"
            mock_issue2.tags = [mock_tag]
            
            with patch('cli.main.repo_list_issues') as mock_list:
                mock_list.return_value = [mock_issue1, mock_issue2]
                
                result = runner.invoke(cli_app, ["issues", "list"])
                
                assert result.exit_code == 0
                assert "tags: none" in result.output  # Issue without tags
                assert "tags: bug" in result.output   # Issue with tags


class TestCLITagsIntegration:
    """Integration tests for CLI tag functionality"""

    def test_complete_tag_workflow(self, db):
        """Test complete tag workflow: create issue with tags, list, rename, delete, cleanup"""
        with patch('cli.main.session_scope') as mock_session:
            mock_session.return_value.__enter__.return_value = db
            mock_session.return_value.__exit__.return_value = None
            
            # Step 1: Create issue with tags
            mock_issue = Mock()
            mock_issue.issue_id = 1
            mock_issue.title = "Test Issue"
            
            with patch('cli.main.repo_create_issue') as mock_create:
                mock_create.return_value = mock_issue
                
                result = runner.invoke(cli_app, [
                    "issues", "create",
                    "--project", "1",
                    "--title", "Test Issue",
                    "--priority", "high",
                    "--status", "open",
                    "--tags", "bug,urgent"
                ])
                assert result.exit_code == 0
            
            # Step 2: List tags
            mock_tag1 = Mock()
            mock_tag1.tag_id = 1
            mock_tag1.name = "bug"
            mock_tag2 = Mock()
            mock_tag2.tag_id = 2
            mock_tag2.name = "urgent"
            
            with patch('cli.main.repo_list_tags') as mock_list_tags:
                mock_list_tags.return_value = [mock_tag1, mock_tag2]
                
                result = runner.invoke(cli_app, ["tags", "list"])
                assert result.exit_code == 0
                assert "bug" in result.output
                assert "urgent" in result.output
            
            # Step 3: Rename tag
            with patch('cli.main.repo_rename_tags_everywhere') as mock_rename:
                result = runner.invoke(cli_app, [
                    "tags", "rename",
                    "--old-name", "bug",
                    "--new-name", "defect"
                ])
                assert result.exit_code == 0
                assert "renamed to 'defect'" in result.output
            
            # Step 4: Delete tag
            with patch('cli.main.repo_delete_tag') as mock_delete:
                mock_delete.return_value = True
                
                result = runner.invoke(cli_app, ["tags", "delete", "--id", "2"])
                assert result.exit_code == 0
                assert "deleted from all issues" in result.output
            
            # Step 5: Cleanup orphaned tags
            with patch('cli.main.repo_remove_tags_with_no_issue') as mock_cleanup:
                mock_cleanup.return_value = 1
                
                result = runner.invoke(cli_app, ["tags", "cleanup"])
                assert result.exit_code == 0
                assert "Cleaned up 1 unused tags" in result.output

    def test_tag_filtering_edge_cases(self, db):
        """Test edge cases in tag filtering"""
        with patch('cli.main.session_scope') as mock_session:
            mock_session.return_value.__enter__.return_value = db
            mock_session.return_value.__exit__.return_value = None
            
            with patch('cli.main.repo_list_issues') as mock_list:
                mock_list.return_value = []
                
                # Test with commas and spaces
                result = runner.invoke(cli_app, [
                    "issues", "list",
                    "--tags", " , bug , ,urgent,  , "
                ])
                
                assert result.exit_code == 0
                
                # Verify empty strings are filtered out
                mock_list.assert_called_once()
                args, kwargs = mock_list.call_args
                assert kwargs['tags'] == ["bug", "urgent"]

    def test_error_handling_in_tag_commands(self, db):
        """Test error handling in various tag commands"""
        with patch('cli.main.session_scope') as mock_session:
            mock_session.return_value.__enter__.return_value = db
            mock_session.return_value.__exit__.return_value = None
            
            # Test NotFound errors
            test_cases = [
                (["tags", "rename", "--old-name", "nonexistent", "--new-name", "new"], 
                 "repo_rename_tags_everywhere"),
                (["tags", "delete", "--id", "999"], 
                 "repo_delete_tag")
            ]
            
            for cmd, mock_func_name in test_cases:
                with patch(f'cli.main.{mock_func_name}') as mock_func:
                    mock_func.side_effect = NotFound("Not found")
                    
                    result = runner.invoke(cli_app, cmd)
                    assert result.exit_code == 1
                    assert "Error:" in result.output

    def test_stdin_log_with_tags(self, db):
        """Test creating issue with stdin log and tags"""
        with patch('cli.main.session_scope') as mock_session:
            mock_session.return_value.__enter__.return_value = db
            mock_session.return_value.__exit__.return_value = None
            
            mock_issue = Mock()
            mock_issue.issue_id = 1
            mock_issue.title = "Test Issue"
            
            with patch('cli.main.repo_create_issue') as mock_create:
                mock_create.return_value = mock_issue
                
                # Use input parameter in runner.invoke instead of mocking sys.stdin
                test_log = "Error traceback from stdin"
                result = runner.invoke(cli_app, [
                    "issues", "create",
                    "--project", "1",
                    "--title", "Test Issue",
                    "--priority", "high",
                    "--status", "open",
                    "--log", "-",
                    "--tags", "error,stdin"
                ], input=test_log)
                
                assert result.exit_code == 0
                
                # Verify stdin was read and tags were processed
                mock_create.assert_called_once()
                args, kwargs = mock_create.call_args
                issue_create = args[1]
                assert issue_create.log == test_log
                assert issue_create.tag_names == ["error", "stdin"]


class TestCLITagsParameterValidation:
    """Test CLI parameter validation and edge cases for tag commands"""

    def test_tag_rename_missing_parameters(self):
        """Test tag rename command with missing parameters"""
        # Missing new-name
        result = runner.invoke(cli_app, ["tags", "rename", "--old-name", "bug"])
        assert result.exit_code == 2  # Typer CLI error for missing required option
        
        # Missing old-name
        result = runner.invoke(cli_app, ["tags", "rename", "--new-name", "defect"])
        assert result.exit_code == 2

    def test_tag_delete_missing_id(self):
        """Test tag delete command with missing ID"""
        result = runner.invoke(cli_app, ["tags", "delete"])
        assert result.exit_code == 2  # Missing required option

    def test_tag_list_invalid_parameters(self):
        """Test tag list command with invalid parameters"""
        # Negative limit should still work (handled by repo layer)
        with patch('cli.main.session_scope') as mock_session:
            mock_db = Mock()
            mock_session.return_value.__enter__.return_value = mock_db
            mock_session.return_value.__exit__.return_value = None
            
            with patch('cli.main.repo_list_tags') as mock_list:
                mock_list.return_value = []
                
                result = runner.invoke(cli_app, ["tags", "list", "--limit", "-1"])
                assert result.exit_code == 0
                mock_list.assert_called_once_with(mock_db, skip=0, limit=-1)

    def test_issues_update_no_fields_provided(self, db):
        """Test issue update with no fields provided"""
        with patch('cli.main.session_scope') as mock_session:
            mock_session.return_value.__enter__.return_value = db
            mock_session.return_value.__exit__.return_value = None
            
            result = runner.invoke(cli_app, ["issues", "update", "--id", "1"])
            assert result.exit_code == 1
            assert "No fields provided to update" in result.output

    def test_issues_create_validation_error(self, db):
        """Test issue creation with validation errors"""
        with patch('cli.main.session_scope') as mock_session:
            mock_session.return_value.__enter__.return_value = db
            mock_session.return_value.__exit__.return_value = None
            
            from pydantic import ValidationError
            
            with patch('cli.main.repo_create_issue') as mock_create:
                mock_create.side_effect = ValidationError.from_exception_data(
                    "ValidationError", 
                    [{"type": "missing", "loc": ("title",), "msg": "Field required"}]
                )
                
                result = runner.invoke(cli_app, [
                    "issues", "create",
                    "--project", "1",
                    "--title", "",
                    "--priority", "high",
                    "--status", "open",
                    "--tags", "test"
                ])
                
                assert result.exit_code == 1
                assert "Error:" in result.output
