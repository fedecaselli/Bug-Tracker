import pytest
from core.validation import (
    normalize_name,
    validate_priority,
    validate_status,
    validate_title,
    validate_project_name,
    validate_tag_name,
    validate_tag_names,
)

def test_normalize_name_basic():
    assert normalize_name("  Foo  Bar  ") == "foo bar"
    assert normalize_name("FOO\tBAR") == "foo bar"
    assert normalize_name("  ") == ""
    assert normalize_name("Test") == "test"
    assert normalize_name("Test\nTest") == "test test"
    assert normalize_name("Ünicode  Test") == "ünicode test"

def test_validate_priority_valid():
    for val in ["low", "Low", "  MEDIUM ", "high"]:
        assert validate_priority(val) in {"low", "medium", "high"}

def test_validate_priority_invalid():
    with pytest.raises(ValueError):
        validate_priority("urgent")
    with pytest.raises(ValueError):
        validate_priority("")
    with pytest.raises(ValueError):
        validate_priority("LOWEST")

def test_validate_status_valid():
    for val in ["open", "Open", "in_progress", "IN_PROGRESS", "closed", "  closed  "]:
        assert validate_status(val) in {"open", "in_progress", "closed"}

def test_validate_status_invalid():
    with pytest.raises(ValueError):
        validate_status("archived")
    with pytest.raises(ValueError):
        validate_status("")
    with pytest.raises(ValueError):
        validate_status("progress")

def test_validate_title_valid():
    assert validate_title("Bug report") == "Bug report"
    assert validate_title(" " * 10 + "Title" + " " * 10) == "Title"
    assert validate_title("A" * 100) == "A" * 100

def test_validate_title_empty_or_whitespace():
    with pytest.raises(ValueError):
        validate_title("")
    with pytest.raises(ValueError):
        validate_title("   ")

def test_validate_title_too_long():
    with pytest.raises(ValueError):
        validate_title("A" * 101)

def test_validate_project_name_valid():
    assert validate_project_name("Project X") == "Project X"
    assert validate_project_name(" " * 5 + "Proj" + " " * 5) == "Proj"
    assert validate_project_name("A" * 200) == "A" * 200

def test_validate_project_name_empty_or_whitespace():
    with pytest.raises(ValueError):
        validate_project_name("")
    with pytest.raises(ValueError):
        validate_project_name("   ")

def test_validate_project_name_too_long():
    with pytest.raises(ValueError):
        validate_project_name("A" * 201)

def test_validate_tag_name_valid():
    assert validate_tag_name("Tag") == "tag"
    assert validate_tag_name("  Tag  Name  ") == "tag name"
    assert validate_tag_name("A" * 100) == "a" * 100

def test_validate_tag_name_empty_or_whitespace():
    with pytest.raises(ValueError):
        validate_tag_name("")
    with pytest.raises(ValueError):
        validate_tag_name("   ")

def test_validate_tag_name_too_long():
    with pytest.raises(ValueError):
        validate_tag_name("A" * 101)

def test_validate_tag_names_basic():
    tags = ["foo", "Foo", "bar", "bar", "  baz  "]
    result = validate_tag_names(tags)
    assert set(result) == {"foo", "bar", "baz"}

def test_validate_tag_names_empty_list():
    assert validate_tag_names([]) == []

def test_validate_tag_names_invalid_entries():
    tags = ["", "   ", "valid", "VALID", "a" * 101]
    with pytest.raises(ValueError):
        validate_tag_names(tags)

def test_validate_tag_names_unicode_and_special():
    tags = ["тест", "ТЕСТ", "special!"]
    result = validate_tag_names(tags)
    assert set(result) == {"тест", "special!"}