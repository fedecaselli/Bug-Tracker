import pytest
from core.automation.tag_generator import TagGenerator

tg = TagGenerator()

def test_single_bug_keyword_in_title():
    # Title contains "error" -> should suggest "bug"
    tags = tg.generate_tags("Critical error on page")
    assert "bug" in tags

def test_single_frontend_keyword_in_title():
    # Title contains "UI" -> should suggest "frontend"
    tags = tg.generate_tags("UI not responsive")
    assert "frontend" in tags

def test_single_backend_keyword_in_title():
    # Title contains "API" -> should suggest "backend"
    tags = tg.generate_tags("API returns 500 error")
    assert "backend" in tags

def test_single_performance_keyword_in_title():
    # Title contains "slow" -> should suggest "performance"
    tags = tg.generate_tags("App is slow to load")
    assert "performance" in tags

def test_keyword_in_description():
    # Description contains "database" -> should suggest "backend"
    tags = tg.generate_tags("Login fails", description="Database unreachable")
    assert "backend" in tags

def test_keyword_in_log():
    # Log contains "timeout" -> should suggest "performance"
    tags = tg.generate_tags("Request failed", log="timeout after 30s")
    assert "performance" in tags

def test_multiple_keywords_multiple_tags():
    # Title and description contain keywords for multiple tags
    tags = tg.generate_tags(
        "Crash on login page",
        description="UI button broken, database error",
        log="slow response"
    )
    assert set(tags) == {"bug", "frontend", "backend", "performance"}

def test_multiple_keywords_same_tag():
    # Title contains "fail" and "error" -> should only suggest "bug" once
    tags = tg.generate_tags("Fail error bug crash")
    assert tags.count("bug") == 1

def test_no_keyword_match():
    # No keywords present -> should return empty list
    tags = tg.generate_tags("All good", description="Nothing wrong", log="OK")
    assert tags == []

def test_case_insensitivity():
    # Keywords in different cases -> should still match
    tags = tg.generate_tags("ERROR in UI", description="DATABASE is slow")
    assert set(tags) == {"bug", "frontend", "backend", "performance"}

def test_partial_keyword_should_not_match():
    # "errorsome" should not match "error"
    tags = tg.generate_tags("errorsome situation")
    assert tags == []

def test_empty_input():
    # All fields empty -> should return empty list
    tags = tg.generate_tags("", "", "")
    assert tags == []

def test_keyword_in_multiple_fields():
    # "bug" in both title and description -> should only suggest "bug" once
    tags = tg.generate_tags("bug found", description="another bug here")
    assert tags.count("bug") == 1

def test_duplicate_keywords_for_different_tags():
    # "fail" for bug, "ui" for frontend, "database" for backend
    tags = tg.generate_tags("fail", description="ui issue", log="database error")
    assert set(tags) == {"bug", "frontend", "backend"}