'''
Test to ensure a single issue can be mapped to multiple tags
'''
from core.models import Project, Issue, Tag

def test_issue_can_have_tags(db):
    proj = Project(name="Trial3")
    db.add(proj); db.commit(); db.refresh(proj)

    #add 2 different tags
    t1 = Tag(name="frontend")
    t2 = Tag(name="backend")
    db.add_all([t1, t2]); db.commit(); db.refresh(t1); db.refresh(t2)

    issue = Issue(
        project_id=proj.project_id,
        title="issue3",
        priority="low",
        status="open",
    )
    issue.tags.extend([t1, t2])
    db.add(issue); db.commit(); db.refresh(issue)

    # reload and check
    fetched = db.get(Issue, issue.issue_id)
    names = sorted(tag.name for tag in fetched.tags)
    assert names == ["backend", "frontend"]
