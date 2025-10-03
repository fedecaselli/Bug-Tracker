"""
CLI

This module provides a command-line interface (CLI) for managing projects, issues, and tags in the Bug Tracker application. 
It allows users to perform operations such as creating, updating, deleting, and listing projects, issues, and tags. 
The CLI also supports advanced features like automatic tag generation and assignee suggestion.
"""

from core.db import SessionLocal
import typer
from typing import Optional
import sys
from pydantic import ValidationError
from core.schemas import ProjectCreate, ProjectUpdate, IssueCreate, IssueUpdate
from core.repos.exceptions import AlreadyExists, NotFound
from contextlib import contextmanager

# Repository layer imports
from core.repos.projects import (
    create_project as repo_create_project,
    delete_project as repo_delete_project,
    update_project as repo_update_project,
    get_project as repo_get_project,
    get_project_by_name as repo_get_project_by_name,
    list_projects as repo_list_projects,
)
from core.repos.issues import (
    create_issue as repo_create_issue,
    delete_issue as repo_delete_issue,
    update_issue as repo_update_issue,
    list_issues as repo_list_issues,
)

from core.repos.tags import (
    list_tags as repo_list_tags,
    delete_tag as repo_delete_tag,
    remove_tags_with_no_issue as repo_remove_tags_with_no_issue,
    rename_tags_everywhere as repo_rename_tags_everywhere,
    get_tag_usage_stats as repo_get_tag_usage_stats,
)


@contextmanager
def session_scope():
    """
    Provide a SQLAlchemy session with automatic cleanup.

    Opens a session and yields it to the caller. The session is always closed when the context exits, regardless 
    of success or failure.

    Yields:
        Session: An active SQLAlchemy session bound to the current engine.
    """
    db = SessionLocal()
    try:
        yield db    
    finally:
        db.close()

# Initialize main CLI application and sub-aplications
cli_app = typer.Typer()
issue_app = typer.Typer(help="Issues")
project_app = typer.Typer(help="Projects")
tag_app = typer.Typer(help="Tags")

cli_app.add_typer(issue_app, name ="issues")
cli_app.add_typer(project_app, name="projects")
cli_app.add_typer(tag_app,name="tags")

# PROJECT  COMMANDS: Add, Remove, List, Update
@project_app.command("add")
def create_project(name: str = typer.Option(..., "--name", help="Project name")):
    """
    Create a new project.

    Creates a project with the given unique name. The project receives an auto-generated ID on success.

    Args:
        name (str): Unique name for the project.

    Raises:
        AlreadyExists: A project with the given name already exists.
        ValidationError: The provided name failed validation.
        typer.Exit: On any error (exit code 1).
        
    Example:
        $ python -m cli projects add --name "My New Project"
        Project My New Project successfully created with id: 5
    """
    with session_scope() as db: 
        try:
            # Create the project using repository layer
            project = repo_create_project(db, ProjectCreate(name=name))
            typer.echo(f"Project {project.name} successfully created with id: {project.project_id}")
        except AlreadyExists as e:
            # Handle case where project name already exists (names must be unique)
            typer.echo(str(e))
            raise typer.Exit(code=1)
        except ValidationError as e:
            # Handle validation error from schemas
            typer.echo(f"Validation error: {e}")
            raise typer.Exit(code=1)

        
@project_app.command("rm")
def delete_project(
    project_id: Optional[int] = typer.Option(None, "--id", help="Project ID"),
    name: Optional[str] = typer.Option(None, "--name", help="Project name")):
    """
    Delete a project by ID or name (cascade issues).

    Deletes the specified project and, via database CASCADE constraints, all associated issues. If both ID and name are provided, 
    they must refer to the same project.

    Args:
        project_id (Optional[int]): ID of the project to delete.
        name (Optional[str]): Name of the project to delete.

    Raises:
        NotFound: The specified project does not exist.
        typer.Exit: No identifier provided or ID/name mismatch (exit code 1).

    Example:
        $ python -m cli projects rm --name "Old Project"
        Project 'Old Project' successfully deleted
    """

    with session_scope() as db: 
        try:
            if project_id is not None and name is not None: 
                # Both provided - check they match
                project_name = repo_get_project_by_name(db, name)
                if project_name.project_id != project_id:
                    typer.echo("Project name and ID do not match. Please provide either name or ID")
                    raise typer.Exit(code=1)
                # Match - delete by ID
                repo_delete_project(db,project_id)
                typer.echo(f"Project '{name}' of ID {project_id} successfully deleted")
                
            elif project_id is not None:
                # Delete by ID only
                repo_delete_project(db, project_id)
                typer.echo(f"Project {project_id} successfully deleted")
            elif name is not None:
                # Delete by name only: get project by name and delete by ID
                project = repo_get_project_by_name(db, name)  
                repo_delete_project(db, project.project_id)
                typer.echo(f"Project '{name}' successfully deleted")
            else:
                # Handle if user does not provide neither ID nor name
                typer.echo("Provide either --id or --name to delete a project")
                raise typer.Exit(code=1)
        except NotFound as e:
            typer.echo(str(e))
            raise typer.Exit(code=1)
        

@project_app.command("list")
def list_project(
    limit: int = typer.Option(20, "--limit", help="Max projects to show", min=1, max=100),
    skip: int = typer.Option(0, "--skip", help="Skip first N projects", min=0)
):
    """
    List all projects with basic information and optional pagination.
    
    Displays all projects in the system with their ID, name, and creation timestamp.
    Supports pagination using the --limit and --skip options.
    
    Args:
        limit (int): Maximum number of projects to display (default: 20).
        skip (int): Number of projects to skip for pagination (default: 0).
        
    Example:
        $ python -m cli projects list --limit 10 --skip 20
        Project id: 21    name: MyApp    created at: 2023-10-03 14:30:00
    """

    with session_scope() as db: 
        # Get all projects
        rows = repo_list_projects(db, skip=skip, limit=limit)
        if not rows:
            typer.echo("No projects")
            return
        # Print each project's information 
        for project in rows:
            typer.echo(f"Project id: {project.project_id} \tname: {project.name} \tcreated at: {project.created_at}")

        
@project_app.command("update")
def update_project(
    old_name: str = typer.Option(..., "--old-name", help="Current project name"),
    new_name: str = typer.Option(..., "--new-name", help="New project name")):
    """
    Update a project's name with uniqueness validation.
    
    Changes the name of an existing project. The new name must be unique across all projects in the system.
    
    Args:
        old_name (str): Current project name to update.
        new_name (str): New unique name for the project.
        
    Raises:
        NotFound: If project with old_name doesn't exist.
        AlreadyExists: If new_name is already taken by another project.
        ValidationError: If new_name fails validation rules.
        typer.Exit: On any error, exits with code 1.
        
    Example:
        $ python -m cli projects update --old-name "OldName" --new-name "NewName"
        Updated project 'OldName' with ID 1, to new name 'NewName'
    """
    with session_scope() as db: 
        # Get project by name
        project = repo_get_project_by_name(db, old_name)
        try:
            # Create update data and update
            data = ProjectUpdate(name=new_name)
            updated_project = repo_update_project(db, project.project_id, data)
            typer.echo(f"Updated project '{old_name}' with ID {updated_project.project_id}, to new name '{updated_project.name}'")
        except AlreadyExists as e:
            # Handle if new name already exists
            typer.echo(str(e))
            raise typer.Exit(code=1)
        except NotFound as e:
            # Handle if project does not exist
            typer.echo(str(e))
            raise typer.Exit(code=1)
        except ValidationError as e:
            # Handle validation errors from schemas
            typer.echo(f"Error: {e}")
            raise typer.Exit(code=1)
    
    
    
# ISSUE COMMANDS: Add, Remove, List, Update
@issue_app.command("add")
def create_issue(project_id: Optional[int] = typer.Option(None, "--project-id", help="Project id - Note: either id or name required"), 
                project_name: Optional[str] = typer.Option(None, "--project-name", help="Project name - Note: either id or name required"),
                title: str = typer.Option(..., "--title"),
                description: Optional[str] = typer.Option(None, "--description"),
                log: Optional[str] = typer.Option(None, "--log", help="Log text, or '-' to read from stdin"),
                summary: Optional[str] = typer.Option(None, "--summary"),
                priority: str = typer.Option(...,"--priority", help="low | medium | high"),
                status: str = typer.Option(..., "--status", help="open | in_progress | closed"),
                assignee: Optional[str] = typer.Option(None,"--assignee", help="Person responsible for resolving the issue"),
                tags: Optional[str] = typer.Option(None, "--tags", help="Comma-separated list of tags"),
                auto_tags: bool = typer.Option(False, "--auto-tags", help="Automatic tag generation"),
                auto_assignee: bool = typer.Option(False, "--auto-assignee",help="Automatic assign to most suitable person")):
    """
    Create a new issue with optional automatic assignee and tag assignment.
    
    Creates an issue within a specified project. Either project_id or project_name must be provided, but not both unless they 
    refer to the same project. Supports automatic tag generation and assignee assignment based on issue content.
    
    Args:
        project_id (Optional[int]): ID of the project to create issue in.
        project_name (Optional[str]): Name of the project to create issue in. 
        title (str): Issue title (required).
        description (Optional[str]): Detailed description of the issue.
        log (Optional[str]): Error logs or debug information. Use '-' to read from stdin.
        summary (Optional[str]): Brief summary of the issue.
        priority (str): Issue priority level ('low', 'medium', 'high').
        status (str): Issue status ('open', 'in_progress', 'closed').
        assignee (Optional[str]): Person responsible for resolving the issue.
        tags (Optional[str]): Comma-separated list of tags to apply.
        auto_tags (bool): Enable automatic tag generation based on content.
        auto_assignee (bool): Enable automatic assignee assignment.
        
    Raises:
        NotFound: If specified project doesn't exist.
        ValidationError: If any field values fail validation.
        typer.Exit: On validation errors or missing required project info (code 1).
        
    Examples:
        $ python -m cli issues add --project-name "MyApp" --title "Login Bug" --priority high --status open
        $ python -m cli issues add --project-id 1 --title "Feature Request" --priority medium --status open --auto-tags --auto-assignee
        $ echo "Error stacktrace..." | python -m cli issues add --project-id 1 --title "Crash" --log - --priority high --status open
    """
    with session_scope() as db: 
        # Handle case: read log from stdin
        if log == "-":
            log = sys.stdin.read()
            
        # Parse comma-separated tags into list 
        tag_names = []
        if tags:
            tag_list = tags.split(",")
            for tag in tag_list:
                stripped_tag = tag.strip()
            if stripped_tag:
                tag_names.append(stripped_tag)
                
        final_project_id = None
        
        # Validate either project ID or name are provided (issues belong to projects)
        if not project_name and not project_id:
            typer.echo("Error: provide either --project-id or --project-name")
            raise typer.Exit(code=1)
        
        # Handle mismatch if both are provided 
        if project_name and project_id:
            try:
                # Verify name and ID belong to same project
                project_by_name = repo_get_project_by_name(db, project_name)
                if project_by_name.project_id != project_id:
                    typer.echo("Project name and ID do not match. Please provide either name or id.")
                    raise typer.Exit(code=1)
                final_project_id = project_id
            except NotFound as e:
                typer.echo(str(e))
                raise typer.Exit(code=1)
            
        # Handle case if only project name is provided 
        elif project_name:
            try:
                # Get project ID from name
                project_obj = repo_get_project_by_name(db, project_name)
                final_project_id = project_obj.project_id
            except NotFound as e:
                typer.echo(str(e))
                raise typer.Exit(code=1)
            
        # Handle case if only project ID is provided
        elif project_id:
            try:
                # Verify project exists
                repo_get_project(db,project_id)
                final_project_id = project_id
            except NotFound as e:
                typer.echo(str(e))
                raise typer.Exit(code=1)
        
        
        try:  
            # Create issue with provided data
            issue = repo_create_issue(db, IssueCreate(      
                                project_id=final_project_id,
                                title=title,
                                description=description,
                                log=log,
                                summary=summary,
                                priority=priority,
                                status=status,
                                assignee=assignee,
                                tag_names=tag_names,
                                auto_generate_tags=auto_tags,
                                auto_generate_assignee=auto_assignee
                                ), )  
            typer.echo(f"Issue {issue.issue_id} successfully created with title '{issue.title}' in project {final_project_id}")
            
            # Provide information on automatic assignee assignment if selected
            if auto_assignee and issue.assignee and not assignee:
                typer.echo(f"Auto-assigned to: {issue.assignee}")
            elif auto_assignee and not issue.assignee:
                typer.echo("Auto-assignment requested but no suitable assignee found")
        except NotFound as e:
            typer.echo(str(e))
            raise typer.Exit(code=1)
        except ValidationError as e:
            # Handle validation error from schemas
            typer.echo(f"Validation Error: {e}")
            raise typer.Exit(code=1)

        

    
@issue_app.command("rm")
def delete_issue(issue_id: int):
    """
    Delete an issue by its unique ID.
    
    Permanently removes the specified issue and all its tag associations.
    The issue's project and tags remain unchanged.
    
    Args:
        issue_id (int): Unique identifier of the issue to delete.
        
    Raises:
        NotFound: If issue with specified ID doesn't exist.
        typer.Exit: On any error, exits with code 1.
        
    Example:
        $ python -m cli issues rm 42
        Successfully deleted issue
    """
    with session_scope() as db: 
        try:
            repo_delete_issue(db,issue_id)
            typer.echo("Successfully deleted issue")
        except NotFound as e:
            typer.echo(str(e))
            raise typer.Exit(code=1)


@issue_app.command("list")
def list_issue(
    limit: int = typer.Option(20, "--limit", help="Max issues to show"),
    skip: int = typer.Option(0, "--skip", help="Skip first N issues"),
    title: Optional[str] = typer.Option(None, "--title", help="Filter by issue name"),
    priority: Optional[str] = typer.Option(None, "--priority", help="Filter by priority (low | medium | high)"),
    status: Optional[str] = typer.Option(None, "--status", help="Filter by status (open | in_progress | closed)"),
    assignee: Optional[str] = typer.Option(None, "--assignee", help="Filter by assignee"),
    project_id: Optional[int] = typer.Option(None, "--project-id", help="Filter by project id"),
    project_name: Optional[str] = typer.Option(None, "--project-name", help="Filter by project name"),
    tags: Optional[str] = typer.Option(None, "--tags", help="Enter comma-separated tags to match (eg. frontend,backend)"),
    tags_match_all: bool = typer.Option(True, "--tags-match-all/--tags-match-any", help="Filter by match all (issue with ALL specified tags - default option) or match any(filter with any of the specified tags)")):
    """
    List issues with comprehensive filtering options and pagination.
    
    Displays issues with various filtering capabilities including project, status, priority, assignee, and tag-based filtering. 
    Supports pagination and flexible project identification via ID or name.
    
    Args:
        limit (int): Maximum number of issues to display (default: 20).
        skip (int): Number of issues to skip for pagination (default: 0).
        title (Optional[str]): Filter by issue title substring match.
        priority (Optional[str]): Filter by priority level ('low', 'medium', 'high').
        status (Optional[str]): Filter by status ('open', 'in_progress', 'closed').
        assignee (Optional[str]): Filter by assignee name.
        project_id (Optional[int]): Filter by project ID.
        project_name (Optional[str]): Filter by project name.
        tags (Optional[str]): Comma-separated tags for filtering.
        tags_match_all (bool): If True, match ALL tags; if False, match ANY tag.
        
    Raises:
        NotFound: If specified project doesn't exist.
        typer.Exit: If project name and ID don't match (code 1).
        
    Examples:
        $ python -m cli issues list --limit 10 --priority high
        $ python -m cli issues list --project-name "MyApp" --status open
        $ python -m cli issues list --tags "frontend,bug" --tags-match-all
    """
    
    with session_scope() as db: 
        tag_filter = None
        # Parse comma-separated tags into list 
        tag_names = []
        if tags:
            tag_list = tags.split(",")
            for tag in tag_list:
                stripped_tag = tag.strip()
            if stripped_tag:
                tag_names.append(stripped_tag)

        
        final_project_id = None
        
        # Handle mismatch if both are provided 
        if project_name and project_id:
            try:
                # Verify name and ID belong to same project
                project_by_name = repo_get_project_by_name(db, project_name)
                if project_by_name.project_id != project_id:
                    typer.echo("Project name and ID do not match. Please provide either name or id.")
                    raise typer.Exit(code=1)
                final_project_id = project_id
            except NotFound as e:
                typer.echo(str(e))
                raise typer.Exit(code=1)

        # Handle case if only project name is provided 
        elif project_name:
            try:
                # Get project ID from name
                project_obj = repo_get_project_by_name(db, project_name)
                final_project_id = project_obj.project_id
            except NotFound as e:
                typer.echo(str(e))
                raise typer.Exit(code=1)
        
        # Handle case if only project ID is provided
        elif project_id:
            try:
                # Verify project exists
                repo_get_project(db,project_id)
                final_project_id = project_id
            except NotFound as e:
                typer.echo(str(e))
                raise typer.Exit(code=1)
        
        
        # Fetch issues with applied filters
        rows = repo_list_issues(db, 
                                skip=skip, 
                                limit=limit, 
                                assignee=assignee, 
                                priority=priority, 
                                status=status,
                                title=title,
                                project_id=final_project_id,
                                tags=tag_filter,
                                tags_match_all=tags_match_all)
        # Handle empty results
        if not rows:
            typer.echo("No registered issues")
            return 
        # Display each issue with corresponding information
        for issue in rows:
            # Format tags
            tag_names = [tag.name for tag in issue.tags] if issue.tags else []
            tags_str = f"{', '.join(tag_names)}" if tag_names else "none" 
            typer.echo(f"Issue id: {issue.issue_id:} \ntitle: {issue.title} \ndescription: {issue.description} \nlog: {issue.log} \nsummary: {issue.summary} \npriority: {issue.priority}\nstatus: {issue.status} \nassignee: {issue.assignee} \ntags: {tags_str} \nproject_id{issue.project_id} \n{project_name}")


@issue_app.command("update")
def update_issue(
    issue_id: int = typer.Option(..., "--id", help="Issue ID"),
    title: Optional[str] = typer.Option(None, "--title"),
    description: Optional[str] = typer.Option(None, "--description"),
    log: Optional[str] = typer.Option(None, "--log", help="Log text, or '-' to read from stdin"),
    summary: Optional[str] = typer.Option(None, "--summary"),
    priority: Optional[str] = typer.Option(None, "--priority", help="low | medium | high"),
    status: Optional[str] = typer.Option(None, "--status", help="open | in_progress | closed"),
    assignee: Optional[str] = typer.Option(None, "--assignee"),
    tags: Optional[str] = typer.Option(None, "--tags", help="comma-separated list of new tags to replace old ones")):
    """
    Update one or more fields of an existing issue.
    
    Performs partial updates on an issue, modifying only the specified fields.
    Tag updates completely replace existing tags. Supports reading log data from stdin.
    
    Args:
        issue_id (int): Unique identifier of the issue to update.
        title (Optional[str]): New issue title.
        description (Optional[str]): New issue description.
        log (Optional[str]): New log content, use '-' to read from stdin.
        summary (Optional[str]): New issue summary.
        priority (Optional[str]): New priority level ('low', 'medium', 'high').
        status (Optional[str]): New status ('open', 'in_progress', 'closed').
        assignee (Optional[str]): New assignee name.
        tags (Optional[str]): Comma-separated tags to replace existing ones.
        
    Raises:
        NotFound: If issue with specified ID doesn't exist.
        ValidationError: If any field values fail validation.
        typer.Exit: If no fields provided or validation errors (code 1).
        
    Examples:
        $ python -m cli issues update --id 42 --status closed --assignee "john_doe"
        $ python -m cli issues update --id 42 --tags "bug,critical,backend"
        $ echo "New error log" | python -m cli issues update --id 42 --log -
    """
    with session_scope() as db: 
        # Handle case: read log from stdin
        if log == "-":
            import sys
            log = sys.stdin.read()
        try:
            # Build update dictionary with only provided fields for full or partial updates
            update_data = {}
            if title is not None:
                update_data["title"] = title
            if description is not None:
                update_data["description"] = description
            if log is not None:
                update_data["log"] = log
            if summary is not None:
                update_data["summary"] = summary
            if priority is not None:
                update_data["priority"] = priority
            if status is not None:
                update_data["status"] = status
            if assignee is not None:
                update_data["assignee"] = assignee
            if tags is not None: 
                tag_names = []
                tag_list = tags.split(",")
                for tag in tag_list:
                    stripped_tag = tag.strip()
                    if stripped_tag:
                        tag_names.append(stripped_tag)
                update_data["tag_names"] = tag_names
            
            # Handle if no updates are provided
            if not update_data:
                typer.echo("No fields provided to update")
                raise typer.Exit(code=1)
                
            # Update using repository layer  
            data = IssueUpdate(**update_data)
            issue = repo_update_issue(db, issue_id, data)
            typer.echo(f"Issue {issue.issue_id} updated")
            
        except NotFound as e:
            # Handle case where issue doesn't exist
            typer.echo(str(e))
            raise typer.Exit(code=1)
        except ValidationError as e:
            # Handle validation error from schemas
            typer.echo(f"Error: {e}")
            raise typer.Exit(code=1)




# TAG COMMANDS: Rename globally, Delete globally, Delete orphan tags, List
@tag_app.command("rename")
def rename_tag(
    old_name: str = typer.Option(..., "--old-name", help="Current tag name"),
    new_name: str = typer.Option(..., "--new-name", help="New tag name")):
    """
    Rename a tag globally across all issues that use it.
    
    Changes the name of a tag throughout the entire system, affecting all issues that currently have this tag assigned.
    
    Args:
        old_name (str): Current name of the tag to rename.
        new_name (str): New name for the tag.
        
    Raises:
        NotFound: If tag with old_name doesn't exist.
        typer.Exit: On any error, exits with code 1.
        
    Example:
        $ python -m cli tags rename --old-name "frontend" --new-name "ui"
        Tag 'frontend' renamed to 'ui' across all issues
    """
    with session_scope() as db:
        try:
            repo_rename_tags_everywhere(db, old_name, new_name)
            typer.echo(f"Tag '{old_name}' renamed to '{new_name}' across all issues")
        except NotFound as e:
            typer.echo(f"Error: {e}")
            raise typer.Exit(code=1)
        
@tag_app.command("delete")
def delete_tag(tag_id: int = typer.Option(..., "--id", help="Tag ID")):
    """
    Delete a tag and remove it from all associated issues.
    
    Permanently removes the specified tag from the system and removes all tag associations from issues that were using this tag.
    
    Args:
        tag_id (int): Unique identifier of the tag to delete
        
    Raises:
        NotFound: If tag with specified ID doesn't exist
        typer.Exit: On any error, exits with code 1
        
    Example:
        $ python -m cli tags delete --id 5
        Tag 5 deleted from all issues
    """
    with session_scope() as db:
        try:
            if repo_delete_tag(db, tag_id):
                typer.echo(f"Tag {tag_id} deleted from all issues")
        except NotFound as e:
            typer.echo(f"Error: {e}")
            raise typer.Exit(code=1)
        
@tag_app.command("cleanup")
def cleanup_tags():
    """
    Remove all unused tags that are not associated with any issues.
    
    Performs maintenance by identifying and deleting tags that have no issue associations, helping keep the tag system clean 
    and organized.
        
    Example:
        $ python -m cli tags cleanup
        Cleaned up 3 unused tags
    """
    with session_scope() as db:
        count = repo_remove_tags_with_no_issue(db)
        typer.echo(f"Cleaned up {count} unused tags")

@tag_app.command("list")
def list_tags(
    limit: int = typer.Option(100, "--limit", help="Max tags to show", min=1, max=1000),
    skip: int = typer.Option(0, "--skip", help="Skip first N tags", min=0),
    stats: bool = typer.Option(False, "--stats", help="Show usage statistics")):
    """
    List all tags with optional usage statistics and pagination.
        
    Displays available tags in the system with optional usage statistics showing how many issues use each tag. 
    Supports pagination for large tag sets.
        
    Args:
        limit (int): Maximum number of tags to display (1-1000, default: 100)
        skip (int): Number of tags to skip for pagination (default: 0)
        stats (bool): If True, show usage statistics for each tag
            
    Examples:
        $ python -m cli tags list --limit 50
        $ python -m cli tags list --stats
        Tag Usage Statistics:
        Tag Name             Usage Count
        frontend                      15
        backend                       12
    """

    with session_scope() as db:
        if stats:
            # Show tag usage statistics for each tag
            usage_stats = repo_get_tag_usage_stats(db)
            if not usage_stats:
                typer.echo("No tags found")
                return
            
            # Format statistics for display
            typer.echo("Tag Usage Statistics:")
            typer.echo(f"{'Tag Name':<20} {'Usage Count':>10}")
            typer.echo("-" * 30)
            for stat in usage_stats:
                typer.echo(f"{stat['name']:<20} {stat['issue_count']:>10}")
        else:
            # Show tag list 
            tags = repo_list_tags(db, skip=skip, limit=limit)
            if not tags:
                typer.echo("No tags found")
                return
            typer.echo("Available Tags:")
            for tag in tags:
                typer.echo(f"ID: {tag.tag_id}\tName: {tag.name}")



