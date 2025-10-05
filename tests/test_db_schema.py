'''
Test to ensure all tables exist in the database
'''

from sqlalchemy import inspect

def test_tables_exist(engine):
    # Test that all required tables are present in the database schema
    insp = inspect(engine)
    names = set(insp.get_table_names())
    # Assert that the expected tables are a subset of the actual tables
    assert {"projects", "issues", "tags", "issue_tags"} <= names
