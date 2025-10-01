from core.db import SessionLocal
import typer
from typing import Optional
import sys
from pydantic import ValidationError

from core.schemas import ProjectCreate, ProjectUpdate, IssueCreate, IssueUpdate
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
    get_issue as repo_get_issue,
    list_issues as repo_list_issues,
)

from core.repos.tags import (
    list_tags as repo_list_tags,
    delete_tag as repo_delete_tag,
    remove_tags_with_no_issue as repo_remove_tags_with_no_issue,
    rename_tags_everywhere as repo_rename_tags_everywhere,
    get_tag_usage_stats as repo_get_tag_usage_stats,
)


from core.repos.exceptions import AlreadyExists, NotFound

# cli/session.py
from contextlib import contextmanager


@contextmanager
def session_scope():
    db = SessionLocal()
    try:
        yield db    # repos handle commit
    finally:
        db.close()

    
cli_app = typer.Typer()
issue_app = typer.Typer(help="Issues")
project_app = typer.Typer(help="Projects")
tag_app = typer.Typer(help="Tags")

cli_app.add_typer(issue_app, name ="issues")
cli_app.add_typer(project_app, name="projects")
cli_app.add_typer(tag_app,name="tags")

#PROJECT 
#Add project
@project_app.command("add")
def create_project(name: str = typer.Option(..., "--name", help="Project name")):
    with session_scope() as db: 
        try:
            project = repo_create_project(db, ProjectCreate(name=name))
            typer.echo(f"Project {project.name} successfully created with id: {project.project_id}")
        except AlreadyExists as e:
            typer.echo(str(e))
            raise typer.Exit(code=1)

        
#Remove project
@project_app.command("rm")
def delete_project(
    project_id: Optional[int] = typer.Option(None, "--id", help="Project ID"),
    name: Optional[str] = typer.Option(None, "--name", help="Project name")
):
    with session_scope() as db: 
        try:
            if project_id is not None:
                repo_delete_project(db, project_id)
                typer.echo(f"Project {project_id} successfully deleted")
            elif name is not None:
                project = repo_get_project_by_name(db, name)  
                repo_delete_project(db, project.project_id)
                typer.echo(f"Project '{name}' successfully deleted")
            else:
                typer.echo("Provide either --id or --name to delete a project")
                raise typer.Exit(code=1)
        except NotFound as e:
            typer.echo(str(e))
            raise typer.Exit(code=1)
        
#List projects   
@project_app.command("list")
def list_project():
    with session_scope() as db: 
        rows = repo_list_projects(db)
        if not rows:
            typer.echo("No projects")
            return
        for project in rows:
            typer.echo(f"Project id: {project.project_id} \tname: {project.name} \tcreated at: {project.created_at}")

        
#Update projects
@project_app.command("update")
def update_project(#Update with old name (name is unique)
    old_name: str = typer.Option(..., "--old-name", help="Current project name"),
    new_name: str = typer.Option(..., "--new-name", help="New project name"),
):
    with session_scope() as db: 
        project = repo_get_project_by_name(db, old_name)
        try:
            data = ProjectUpdate(name=new_name)
            updated_project = repo_update_project(db, project.project_id, data)
            typer.echo(f"Updated project '{old_name}' with ID {updated_project.project_id}, to new name '{updated_project.name}'")
        except AlreadyExists as e:
            typer.echo(str(e))
            raise typer.Exit(code=1)
        except NotFound as e:
            typer.echo(str(e))
            raise typer.Exit(code=1)
        except ValidationError as e:
            typer.echo(f"Error: {e}")
            raise typer.Exit(code=1)
    
#ISSUE

@issue_app.command("create")
def create_issue(project_id: int = typer.Option(..., "--project", help="Project id"), 
                title: str = typer.Option(..., "--title"),
                description: Optional[str] = typer.Option(None, "--description"),
                log: Optional[str] = typer.Option(None, "--log", help="Log text, or '-' to read from stdin"),
                summary: Optional[str] = typer.Option(None, "--summary"),
                priority: str = typer.Option(...,"--priority", help="low | medium | high"),
                status: str = typer.Option(..., "--status", help="open | in_progress | closed"),
                assignee: Optional[str] = typer.Option(None,"--assignee", help="Person responsible for resolving the issue"),
                tags: Optional[str] = typer.Option(None, "--tags", help="Comma-separated list of tags")):
    with session_scope() as db: 
        if log == "-":
            log = sys.stdin.read()
        tag_names = []
        if tags:
            tag_names = [tag.strip() for tag in tags.split(",") if tag.strip()]
        try:  
            issue = repo_create_issue(db, IssueCreate(      
                                project_id=project_id,
                                title=title,
                                description=description,
                                log=log,
                                summary=summary,
                                priority=priority,
                                status=status,
                                assignee=assignee,
                                tag_names=tag_names,
                                ), )  
            typer.echo(f"Issue {issue.issue_id} successfully created with title {issue.title}")
        except NotFound as e:
            typer.echo(str(e))
            raise typer.Exit(code=1)
        except ValidationError as e:
            typer.echo(f"Error: {e}")
            raise typer.Exit(code=1)

        

    
@issue_app.command("rm")
def delete_issue(issue_id: int):
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
    tags: Optional[str] = typer.Option(None, "--tags", help="Enter comma-separated tags to match (eg. frontend,backend)"),
    tags_match_all: bool = typer.Option(True, "--tags-match-all/--tags-match-any", help="Filter by match all (issue with ALL specified tags - default option) or match any(filter with any of the specified tags)")
):
    with session_scope() as db: 
        tag_filter = None
        if tags:
            tag_filter = [tag.strip() for tag in tags.split(",") if tag.strip()]
        rows = repo_list_issues(db, 
                                skip=skip, 
                                limit=limit, 
                                assignee=assignee, 
                                priority=priority, 
                                status=status,
                                title=title,
                                tags=tag_filter,
                                tags_match_all=tags_match_all)
        if not rows:
            typer.echo("No registered issues")
            return 
        for issue in rows:
            tag_names = [tag.name for tag in issue.tags] if issue.tags else []
            tags_str = f"{', '.join(tag_names)}" if tag_names else "none"
            typer.echo(f"Issue id: {issue.issue_id:} \ttitle: {issue.title} \tdescription: {issue.description} \tlog: {issue.log} \tsummary: {issue.summary} \tpriority: {issue.priority}\tstatus: {issue.status} \tassignee: {issue.assignee} \ttags: {tags_str}")


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
    tags: Optional[str] = typer.Option(None, "--tags", help="comma-separated list of new tags to replace old ones")
):
    #Update provided changes 
    with session_scope() as db: 
        # stdin for logs
        if log == "-":
            import sys
            log = sys.stdin.read()
        try:
            # Build update dict with only provided fields
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
                tag_names = [tag.strip() for tag in tags.split(",") if tag.strip()]
                update_data["tag_names"] = tag_names
            
            if not update_data:
                typer.echo("No fields provided to update")
                raise typer.Exit(code=1)
                
                
            data = IssueUpdate(**update_data)
            issue = repo_update_issue(db, issue_id, data)
                
            typer.echo(f"Issue {issue.issue_id} updated")
        except NotFound as e:
            typer.echo(str(e))
            raise typer.Exit(code=1)
        except ValidationError as e:
            typer.echo(f"Error: {e}")
            raise typer.Exit(code=1)





#Renaming globally
@tag_app.command("rename")
def rename_tag(
    old_name: str = typer.Option(..., "--old-name", help="Current tag name"),
    new_name: str = typer.Option(..., "--new-name", help="New tag name")
):
    """Rename a tag globally (affects ALL issues with this tag)."""
    with session_scope() as db:
        try:
            repo_rename_tags_everywhere(db, old_name, new_name)
            typer.echo(f"Tag '{old_name}' renamed to '{new_name}' across all issues")
        except NotFound as e:
            typer.echo(f"Error: {e}")
            raise typer.Exit(code=1)
        
#deleting globally
@tag_app.command("delete")
def delete_tag(tag_id: int = typer.Option(..., "--id", help="Tag ID")):
    """Delete a tag (removes it from ALL issues)."""
    with session_scope() as db:
        try:
            if repo_delete_tag(db, tag_id):
                typer.echo(f"Tag {tag_id} deleted from all issues")
        except NotFound as e:
            typer.echo(f"Error: {e}")
            raise typer.Exit(code=1)
        
#Deleting all tags with no issue ID associated to them 
@tag_app.command("cleanup")
def cleanup_tags():
    """Remove unused tags."""
    with session_scope() as db:
        count = repo_remove_tags_with_no_issue(db)
        typer.echo(f"Cleaned up {count} unused tags")

@tag_app.command("list")
def list_tags(
    limit: int = typer.Option(100, "--limit", help="Max tags to show", min=1, max=1000),
    skip: int = typer.Option(0, "--skip", help="Skip first N tags", min=0),
    stats: bool = typer.Option(False, "--stats", help="Show usage statistics")
):
    """List all tags with optional usage statistics."""
    with session_scope() as db:
        if stats:
            # Show tag usage statistics
            usage_stats = repo_get_tag_usage_stats(db)
            if not usage_stats:
                typer.echo("No tags found")
                return
            typer.echo("Tag Usage Statistics:")
            typer.echo("Tag Name\t\tUsage Count")
            typer.echo("-" * 30)
            for stat in usage_stats:
                typer.echo(f"{stat['name']}\t\t{stat['issue_count']}")
        else:
            tags = repo_list_tags(db, skip=skip, limit=limit)
            if not tags:
                typer.echo("No tags found")
                return
            typer.echo("Available Tags:")
            for tag in tags:
                typer.echo(f"ID: {tag.tag_id}\tName: {tag.name}")



