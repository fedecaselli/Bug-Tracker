from core.db import SessionLocal
import typer
from core.models import Project, Issue
from typing import Optional
import sys

'''
def get_db():
    db = SessionLocal() 
    try:
        yield db
    finally:
        db.close()
'''
    
cli_app = typer.Typer()
issue_app = typer.Typer(help="Issues")
project_app = typer.Typer(help="Projects")

cli_app.add_typer(issue_app, name ="issues")
cli_app.add_typer(project_app, name="projects")

#PROJECT 
@project_app.command("add")
def create_project(name: str = typer.Option(..., "--name", help="Project name")):
    db = SessionLocal()
    try:
        if db.query(Project).filter_by(name=name).first():
            typer.echo(f"Project {name} already exists")
            raise typer.Exit(code=1)
        project = Project(name=name)
        db.add(project)
        db.commit()
        db.refresh(project)
        typer.echo(f"Project {project.name} successfully created with id: {project.project_id}")
    finally:
        db.close()
        
    
@project_app.command("rm")
def delete_project(
    project_id: Optional[int] = typer.Option(None, "--id", help="Project ID"),
    name: Optional[str] = typer.Option(None, "--name", help="Project name")
):
    db = SessionLocal()
    try:
        project = None
        if project_id is not None:
            project = db.get(Project, project_id)
        elif name is not None:
            project = db.query(Project).filter_by(name=name).first()
        else:
            typer.echo("Provide either --id or --name to delete a project")
            raise typer.Exit(code=1)

        if not project:
            typer.echo("Project not found")
            raise typer.Exit(code=1)
        db.delete(project)
        db.commit()
        typer.echo(f"Project '{project.name}' (id: {project.project_id}) successfully deleted")
    finally:
        db.close()

@project_app.command("list")
def list_project():
    db = SessionLocal()
    try:
        rows = db.query(Project).order_by(Project.name).all()
        if not rows:
            typer.echo("No projects")
            return
        for project in rows:
            typer.echo(f"Project id:{project.project_id:} \tname: {project.name} \tcreated at:{project.created_at}")
    finally:
        db.close()
        
        
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
    db = SessionLocal()
    try:
        if log == "-":
            log = sys.stdin.read()
            
        if not db.get(Project, project_id):
            typer.echo(f"Project {project_id} not found")
            raise typer.Exit(code=1)
        issue = Issue(project_id = project_id, title=title, description=description, log=log, summary=summary, priority = priority.lower(), status=status.lower(), assignee=assignee)
        #ADD TAGS
        db.add(issue)
        db.commit()
        db.refresh(issue)
        typer.echo(f"Issue {issue.issue_id} successfully created with title {issue.title}")
    finally:
        db.close()
        

    
@issue_app.command("rm")
def delete_issue(issue_id: int):
    db = SessionLocal()
    try:
        issue = db.get(Issue, issue_id)
        if not issue:
            typer.echo(f"Issue {issue_id} not found")
            raise typer.Exit(code=1)
        db.delete(issue)
        db.commit()
        typer.echo(f"Successfuly deleted issue {issue.issue_id}")
    finally:
        db.close()

@issue_app.command("list")
def list_issue(
    limit: int = typer.Option(20, "--limit", help="Max issues to show"),
    offset: int = typer.Option(0, "--offset", help="Skip first N issues")
):
    db = SessionLocal()
    try:
        rows = db.query(Issue).offset(offset).limit(limit).all()
        if not rows:
            typer.echo("No registered issues")
            return 
        for issue in rows:
            typer.echo(f"Issue id: {issue.issue_id:} \ttitle: {issue.title} \tdescription: {issue.description} \tlog: {issue.log} \tsummary: {issue.summary} \tpriority: {issue.priority}\tstatus: {issue.status} \tassignee: {issue.assignee}")
    finally: #ADD TAGS LATER
        db.close()
        


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
    db = SessionLocal()
    try:
        issue = db.get(Issue, issue_id)
        if not issue:
            typer.echo(f"Issue {issue_id} not found")
            raise typer.Exit(code=1)

        # stdin for logs
        if log == "-":
            import sys
            log = sys.stdin.read()

        changed = False

        if title is not None:
            issue.title = title; changed = True
        if description is not None:
            issue.description = description; changed = True
        if log is not None:
            issue.log = log; changed = True
        if summary is not None:
            issue.summary = summary; changed = True
        if priority is not None:
            issue.priority = priority.lower(); changed = True
        if status is not None:
            issue.status = status.lower(); changed = True
        if assignee is not None:
            issue.assignee = assignee; changed = True

        if not changed:
            typer.echo("No fields provided to update.")
            raise typer.Exit(code=1)

        db.commit()
        db.refresh(issue)
        typer.echo(f"Issue {issue.issue_id} updated")
    finally:
        db.close()

        
@project_app.command("update")
def update_project(
    project_id: int = typer.Option(..., "--id", help="Project ID"),
    name: Optional[str] = typer.Option(None, "--name", help="New project name"),
):

    db = SessionLocal()
    try:
        project = db.get(Project, project_id)
        if not project:
            typer.echo(f"Project {project_id} not found")
            raise typer.Exit(code=1)

        changed = False
        if name is not None:
            #No projects with same name
            exists = db.query(Project).filter(Project.name == name, Project.project_id != project_id).first()
            if exists:
                typer.echo(f"Another project already uses the name '{name}'")
                raise typer.Exit(code=1)
            project.name = name
            changed = True

        if not changed:
            typer.echo("No fields provided to update.")
            raise typer.Exit(code=1)

        db.commit()
        db.refresh(project)
        typer.echo(f"Updated project {project.project_id}: {project.name}")
    finally:
        db.close()



#LIST WITH FILTERS



