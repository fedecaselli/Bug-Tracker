import re

from fastapi.testclient import TestClient

from app import app


client = TestClient(app)


def test_health_endpoint():
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "database" in data


def test_metrics_endpoint_includes_http_requests():
    # Trigger a request so counters increment
    client.get("/health")
    resp = client.get("/metrics")
    assert resp.status_code == 200
    body = resp.text
    # Basic checks for our custom metrics
    assert "http_requests_total" in body
    assert re.search(r"http_requests_total\{.*path=\"/health\".*\}", body)
