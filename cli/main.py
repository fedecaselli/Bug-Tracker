from core.db import SessionLocal
import typer
from typing import Optional
import sys


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

cli_app.add_typer(issue_app, name ="issues")
cli_app.add_typer(project_app, name="projects")

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
            typer.echo(f"Project id:{project.project_id} \tname: {project.name} \tcreated at:{project.created_at}")

        
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
    
#ISSUE

@issue_app.command("create")
def create_issue(project_id: int = typer.Option(..., "--project", help="Project id"), 
                 title: str = typer.Option(..., "--title"),
                 description: Optional[str] = typer.Option(None, "--description"),
                 log: Optional[str] = typer.Option(None, "--log", help="Log text, or '-' to read from stdin"),
                 summary: Optional[str] = typer.Option(None, "--summary"),
                 priority: str = typer.Option(...,"--priority", help="low | medium | high"),
                 status: str = typer.Option(..., "--status", help="open | in_progress | closed"),
                 assignee: Optional[str] = typer.Option(None,"--assignee", help="Person responsible for resolving the issue")):
    with session_scope() as db: 
        if log == "-":
            log = sys.stdin.read()
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
                                ), )  
            #ADD TAGS
            typer.echo(f"Issue {issue.issue_id} successfully created with title {issue.title}")
        except NotFound as e:
            typer.echo(str(e))
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
):
    with session_scope() as db: 
        rows = repo_list_issues(db, 
                                skip=skip, 
                                limit=limit, 
                                assignee=assignee, 
                                priority=priority, 
                                status=status,
                                title=title)
        if not rows:
            typer.echo("No registered issues")
            return 
        for issue in rows:
            typer.echo(f"Issue id: {issue.issue_id:} \ttitle: {issue.title} \tdescription: {issue.description} \tlog: {issue.log} \tsummary: {issue.summary} \tpriority: {issue.priority}\tstatus: {issue.status} \tassignee: {issue.assignee}")
#ADD TAGS LATER

        


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
):
    #Update provided changes 
    with session_scope() as db: 
        # stdin for logs
        if log == "-":
            import sys
            log = sys.stdin.read()
        try:
            data = IssueUpdate(title=title,
                description=description,
                log=log,
                summary=summary,
                priority=priority,
                status=status,
                assignee=assignee)
            if not any([title, description, log, summary, priority, status, assignee]):
                typer.echo("No fields provided to update")
                raise typer.Exit(code=1)
            issue = repo_update_issue(db, issue_id, data)
            typer.echo(f"Issue {issue.issue_id} updated")
        except NotFound as e:
            typer.echo(str(e))
            raise typer.Exit(code=1)


    





