import pytest

import config


def test_database_url_validates_supported_schemes():
    assert config._validate_database_url("sqlite:///./db.sqlite") == "sqlite:///./db.sqlite"
    assert config._validate_database_url("postgresql://user:pass@host:5432/db") == "postgresql://user:pass@host:5432/db"


def test_database_url_rejects_missing():
    with pytest.raises(ValueError):
        config._validate_database_url("")


def test_database_url_rejects_bad_scheme():
    with pytest.raises(ValueError):
        config._validate_database_url("http://not-a-db")
