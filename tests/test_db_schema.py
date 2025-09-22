from sqlalchemy import inspect
#check that tables exist in database 
def test_tables_exist(engine):
    insp = inspect(engine)
    names = set(insp.get_table_names())
    assert {"projects", "issues", "tags", "issue_tags"} <= names
