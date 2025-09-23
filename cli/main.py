from core.db import SessionLocal
import typer
from core.models import Project, Issue
from typing import Optional
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
        
    
@project_app.command("delete")
def delete_project(project_id: int):
    db = SessionLocal()
    try:
        project = db.get(Project, project_id)
        if not project:
            typer.echo(f"Project not found")
            raise typer.Exit(code=1)
        db.delete(project)
        db.commit()
        typer.echo(f"Project {project_id} successfully deleted")
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
                 log: Optional[str] = typer.Option(None, "--log"),
                 summary: Optional[str] = typer.Option(None, "--summary"),
                 priority: str = typer.Option(...,"--priority", help="Insert low, medium or high"),
                 status: str = typer.Option(..., "--status", help="Insert open, in_progress or closed"),
                 assignee: Optional[str] = typer.Option(None,"--assignee", help="Person responsible for resolving the issue")):
    db = SessionLocal()
    try:
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
def list_issue():
    db = SessionLocal()
    try:
        rows = db.query(Issue).all()
        if not rows:
            typer.echo("No registered issues")
            return 
        for issue in rows:
            typer.echo(f"Issue id: {issue.issue_id:} \ttitle: {issue.title} \tdescription: {issue.description} \tlog: {issue.log} \tsummary: {issue.summary} \tpriority: {issue.priority}\tstatus: {issue.status} \tassignee: {issue.assignee}")
    finally: #ADD TAGS LATER
        db.close()
        

#LIST WITH FILTERS
#FUTURE DEVELOPMENT


if __name__ == "__main__":
    cli_app()