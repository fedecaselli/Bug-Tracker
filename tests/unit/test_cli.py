import pytest
import requests
from typer.testing import CliRunner

from cli.main import cli_app


runner = CliRunner()


@pytest.fixture
def api_stub(monkeypatch):
    """
    Stub cli.main._api_request with a simple dispatcher and capture calls.
    """
    calls = []
    responses = {}

    def register(method, path, response):
        responses[(method, path)] = response

    def _fake_api(method, path, params=None, json=None):
        calls.append({"method": method, "path": path, "params": params, "json": json})
        key = (method, path)
        if key not in responses:
            raise AssertionError(f"Unexpected API call: {method} {path}")
        resp = responses[key]
        # Allow callable for dynamic responses
        return resp(json, params) if callable(resp) else resp

    monkeypatch.setattr("cli.main._api_request", _fake_api)
    return register, calls


def test_api_request_network_error(monkeypatch):
    import cli.main as cm
    class DummyExc(requests.RequestException):
        pass
    def boom(*args, **kwargs):
        raise DummyExc("boom")
    monkeypatch.setattr("cli.main.requests.request", boom)
    result = runner.invoke(cli_app, ["projects", "list"])
    assert result.exit_code != 0
    assert "Network error" in result.output


def test_api_request_http_error_json(monkeypatch):
    import cli.main as cm
    class Resp:
        status_code = 404
        text = "not found"
        headers = {"content-type": "application/json"}
        def json(self):
            return {"detail": "missing"}
    monkeypatch.setattr("cli.main.requests.request", lambda *a, **k: Resp())
    result = runner.invoke(cli_app, ["projects", "list"])
    assert result.exit_code != 0
    assert "API error 404" in result.output


def test_api_request_http_error_text(monkeypatch):
    class Resp:
        status_code = 500
        text = "fail"
        headers = {"content-type": "text/plain"}
        def json(self):
            raise ValueError
    monkeypatch.setattr("cli.main.requests.request", lambda *a, **k: Resp())
    result = runner.invoke(cli_app, ["projects", "list"])
    assert result.exit_code != 0
    assert "API error 500" in result.output


def test_api_request_text_response(monkeypatch):
    class Resp:
        status_code = 200
        text = "ok"
        headers = {"content-type": "text/plain"}
        def json(self):
            return {}
    monkeypatch.setattr("cli.main.requests.request", lambda *a, **k: Resp())
    from cli.main import _api_request
    assert _api_request("get", "/whatever") == "ok"


def test_projects_add_list_delete(api_stub):
    register, calls = api_stub

    # Responses for list/create/delete
    register("get", "/projects", [])
    register("get", "/projects/", [])
    register("get", "/projects/1", {"project_id": 1, "name": "Hello", "created_at": "now"})
    register("post", "/projects/", {"project_id": 1, "name": "Hello"})
    register("delete", "/projects/1", {})
    register("get", "/projects", [{"project_id": 1, "name": "Hello", "created_at": "now"}])
    register("get", "/projects/", [{"project_id": 1, "name": "Hello", "created_at": "now"}])

    # add
    result = runner.invoke(cli_app, ["projects", "add", "--name", "Hello"])
    assert result.exit_code == 0
    assert "successfully created" in result.output

    # list
    result = runner.invoke(cli_app, ["projects", "list"])
    assert result.exit_code == 0
    assert "Hello" in result.output

    # delete
    result = runner.invoke(cli_app, ["projects", "rm", "--id", "1"])
    assert result.exit_code == 0
    assert "successfully deleted" in result.output

    # Ensure calls were made
    assert any(c["method"] == "post" and c["path"] == "/projects/" for c in calls)
    assert any(c["method"] == "delete" and c["path"] == "/projects/1" for c in calls)


def test_issues_add_list_update_delete(api_stub):
    register, calls = api_stub

    # For resolve_project_id we need list_projects/get_project
    register("get", "/projects", [{"project_id": 1, "name": "Hello"}])
    register("get", "/projects/1", {"project_id": 1, "name": "Hello"})

    # Create issue response
    register(
        "post",
        "/issues/",
        {"issue_id": 5, "title": "Bug", "project_id": 1, "assignee": None},
    )

    # List issues response
    register(
        "get",
        "/issues/",
        [
            {
                "issue_id": 5,
                "title": "Bug",
                "description": None,
                "log": None,
                "summary": None,
                "priority": "high",
                "status": "open",
                "assignee": None,
                "tags": [{"name": "bug"}],
                "project_id": 1,
            }
        ],
    )

    # Update issue response
    register("put", "/issues/5", {})
    # Delete issue response
    register("delete", "/issues/5", {})

    # add
    result = runner.invoke(
        cli_app,
        [
            "issues",
            "add",
            "--project-name",
            "Hello",
            "--title",
            "Bug",
            "--priority",
            "high",
            "--status",
            "open",
        ],
    )
    assert result.exit_code == 0
    assert "successfully created" in result.output

    # list
    result = runner.invoke(cli_app, ["issues", "list", "--project-name", "Hello"])
    assert result.exit_code == 0
    assert "Bug" in result.output

    # update
    result = runner.invoke(
        cli_app,
        ["issues", "update", "--id", "5", "--status", "closed"],
    )
    assert result.exit_code == 0
    assert "updated" in result.output

    # delete
    result = runner.invoke(cli_app, ["issues", "rm", "5"])
    assert result.exit_code == 0
    assert "Successfully deleted" in result.output

    assert any(c["method"] == "post" and c["path"] == "/issues/" for c in calls)
    assert any(c["method"] == "put" and c["path"] == "/issues/5" for c in calls)
    assert any(c["method"] == "delete" and c["path"] == "/issues/5" for c in calls)


def test_tags_list_stats_rename_cleanup_delete(api_stub):
    register, calls = api_stub

    register(
        "get",
        "/tags",
        [{"tag_id": 1, "name": "bug"}, {"tag_id": 2, "name": "frontend"}],
    )
    register(
        "get",
        "/tags/stats/usage",
        [{"name": "bug", "issue_count": 3}],
    )
    register("patch", "/tags/rename", {})
    register("delete", "/tags/cleanup", {"count": 2})
    register("delete", "/tags/1", {})

    # list
    result = runner.invoke(cli_app, ["tags", "list"])
    assert result.exit_code == 0
    assert "bug" in result.output

    # stats
    result = runner.invoke(cli_app, ["tags", "list", "--stats"])
    assert result.exit_code == 0
    assert "Tag Usage Statistics" in result.output

    # rename
    result = runner.invoke(cli_app, ["tags", "rename", "--old-name", "bug", "--new-name", "ui"])
    assert result.exit_code == 0

    # cleanup
    result = runner.invoke(cli_app, ["tags", "cleanup"])
    assert result.exit_code == 0
    assert "Cleaned up" in result.output

    # delete
    result = runner.invoke(cli_app, ["tags", "delete", "--id", "1"])
    assert result.exit_code == 0

    assert any(c["method"] == "get" and c["path"] == "/tags" for c in calls)
    assert any(c["method"] == "delete" and c["path"] == "/tags/1" for c in calls)


def test_issue_update_no_fields():
    result = runner.invoke(cli_app, ["issues", "update", "--id", "5"])
    assert result.exit_code != 0
    assert "No fields provided to update" in result.output


def test_services_missing_args():
    from cli import services
    with pytest.raises(ValueError):
        services.resolve_project_id(lambda: [], lambda _id: None)


def test_services_not_found_name():
    from cli import services
    def list_fn():
        return [{"project_id": 1, "name": "A"}]
    with pytest.raises(ValueError):
        services.resolve_project_id(list_fn, lambda _id: None, name="B")


def test_projects_rm_by_name(api_stub):
    register, calls = api_stub
    register("get", "/projects", [{"project_id": 2, "name": "Bye", "created_at": "now"}])
    register("get", "/projects/", [{"project_id": 2, "name": "Bye", "created_at": "now"}])
    register("get", "/projects/2", {"project_id": 2, "name": "Bye", "created_at": "now"})
    register("delete", "/projects/2", {})

    result = runner.invoke(cli_app, ["projects", "rm", "--name", "Bye"])
    assert result.exit_code == 0
    assert "successfully deleted" in result.output
    assert any(c["method"] == "delete" and c["path"] == "/projects/2" for c in calls)


def test_projects_rm_missing_args():
    result = runner.invoke(cli_app, ["projects", "rm"])
    assert result.exit_code != 0
    assert "Provide either --id or --name" in result.output


def test_projects_rm_mismatch(api_stub):
    register, _calls = api_stub
    register("get", "/projects", [{"project_id": 3, "name": "Foo"}])
    register("get", "/projects/", [{"project_id": 3, "name": "Foo"}])
    # mismatch: id 3 vs name Bar should trigger ValueError in resolver
    result = runner.invoke(cli_app, ["projects", "rm", "--id", "3", "--name", "Bar"])
    assert result.exit_code != 0
    assert "not found" in result.output or "do not match" in result.output


def test_issue_list_no_results(api_stub):
    register, _calls = api_stub
    register("get", "/issues/", [])

    result = runner.invoke(cli_app, ["issues", "list"])
    assert result.exit_code == 0
    assert "No registered issues" in result.output


def test_tags_list_no_results(api_stub):
    register, _calls = api_stub
    register("get", "/tags", [])

    result = runner.invoke(cli_app, ["tags", "list"])
    assert result.exit_code == 0
    assert "No tags found" in result.output


def test_projects_list_empty(api_stub):
    register, _calls = api_stub
    register("get", "/projects/", [])
    result = runner.invoke(cli_app, ["projects", "list"])
    assert result.exit_code == 0
    assert "No projects" in result.output


def test_issue_add_with_tags_and_project_id(api_stub):
    register, calls = api_stub
    register("get", "/projects/10", {"project_id": 10, "name": "X"})
    register(
        "post",
        "/issues/",
        {"issue_id": 11, "title": "Crash", "project_id": 10, "assignee": None},
    )

    result = runner.invoke(
        cli_app,
        [
            "issues",
            "add",
            "--project-id",
            "10",
            "--title",
            "Crash",
            "--priority",
            "high",
            "--status",
            "open",
            "--tags",
            "bug,frontend",
        ],
    )
    assert result.exit_code == 0
    assert "successfully created" in result.output
    assert any(c["method"] == "post" and c["path"] == "/issues/" for c in calls)


def test_issue_list_cache_hits(api_stub):
    register, calls = api_stub
    register(
        "get",
        "/issues/",
        [
            {
                "issue_id": 1,
                "title": "One",
                "priority": "low",
                "status": "open",
                "assignee": None,
                "tags": [],
                "project_id": 123,
            },
            {
                "issue_id": 2,
                "title": "Two",
                "priority": "medium",
                "status": "open",
                "assignee": None,
                "tags": [],
                "project_id": 123,
            },
        ],
    )
    register("get", "/projects/123", {"project_id": 123, "name": "Proj"})

    result = runner.invoke(cli_app, ["issues", "list"])
    assert result.exit_code == 0
    assert "Proj" in result.output


def test_issue_update_log_stdin(monkeypatch, api_stub):
    register, _calls = api_stub
    register("put", "/issues/9", {})
    monkeypatch.setattr("sys.stdin.read", lambda: "from stdin")
    result = runner.invoke(
        cli_app,
        ["issues", "update", "--id", "9", "--log", "-", "--status", "closed"],
    )
    assert result.exit_code == 0
    assert "updated" in result.output
