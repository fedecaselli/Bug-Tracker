"""
Thin API client wrapper for CLI commands.
Encapsulates HTTP details so commands can focus on orchestration.
"""

from typing import Any, Dict, Optional

import requests
import typer

from core.logging import get_logger


logger = get_logger(__name__)


class ApiClient:
    def __init__(self, base_url: str, token: Optional[str] = None):
        self.base_url = base_url.rstrip("/")
        self.token = token

    def _request(self, method: str, path: str, *, params=None, json=None):
        url = f"{self.base_url}{path}"
        headers = {"Accept": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        try:
            resp = requests.request(method, url, params=params, json=json, headers=headers, timeout=15)
        except requests.RequestException as exc:
            logger.error("Network error calling %s: %s", url, exc)
            typer.echo(f"Network error calling {url}: {exc}")
            raise typer.Exit(code=1)

        if resp.status_code >= 400:
            detail = resp.text
            try:
                detail_json = resp.json()
                detail = detail_json.get("detail", detail)
            except ValueError:
                pass
            logger.error("API error %s for %s: %s", resp.status_code, url, detail)
            typer.echo(f"API error {resp.status_code}: {detail}")
            raise typer.Exit(code=1)

        if resp.headers.get("content-type", "").startswith("application/json"):
            return resp.json()
        return resp.text

    # Project endpoints
    def list_projects(self) -> list[dict]:
        return self._request("get", "/projects/")

    def get_project(self, project_id: int) -> dict:
        return self._request("get", f"/projects/{project_id}")

    def create_project(self, payload: Dict[str, Any]) -> dict:
        return self._request("post", "/projects/", json=payload)

    def update_project(self, project_id: int, payload: Dict[str, Any]) -> dict:
        return self._request("put", f"/projects/{project_id}", json=payload)

    def delete_project(self, project_id: int) -> None:
        self._request("delete", f"/projects/{project_id}")

    # Issue endpoints
    def list_issues(self, params: Dict[str, Any]) -> list[dict]:
        return self._request("get", "/issues/", params=params)

    def create_issue(self, payload: Dict[str, Any]) -> dict:
        return self._request("post", "/issues/", json=payload)

    def update_issue(self, issue_id: int, payload: Dict[str, Any]) -> dict:
        return self._request("put", f"/issues/{issue_id}", json=payload)

    def delete_issue(self, issue_id: int) -> None:
        self._request("delete", f"/issues/{issue_id}")

    # Tag endpoints
    def list_tags(self, params: Dict[str, Any]) -> list[dict]:
        return self._request("get", "/tags/", params=params)

    def list_tag_stats(self) -> list[dict]:
        return self._request("get", "/tags/stats/usage")

    def rename_tag(self, old_name: str, new_name: str) -> None:
        self._request("patch", "/tags/rename", params={"old_name": old_name, "new_name": new_name})

    def delete_tag(self, tag_id: int) -> None:
        self._request("delete", f"/tags/{tag_id}")

    def cleanup_tags(self) -> dict:
        return self._request("delete", "/tags/cleanup")
