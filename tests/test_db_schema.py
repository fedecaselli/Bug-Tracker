'''
Test to ensure all tables exist in the database
'''

from sqlalchemy import inspect

def test_tables_exist(engine):
    insp = inspect(engine)
    names = set(insp.get_table_names())
    assert {"projects", "issues", "tags", "issue_tags"} <= names
