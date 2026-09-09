import pytest
from fastapi.testclient import TestClient

import server


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(server, "DEFAULT_DB_PATH", str(tmp_path / "route_test.db"))
    monkeypatch.setattr(server, "ADMIN_TOKEN", "test-admin-token")
    monkeypatch.setenv("ONRECORD_PROTECT_READS", "true")
    monkeypatch.setenv("ONRECORD_JUDGE_MODE", "false")
    with TestClient(server.app) as test_client:
        yield test_client


def test_operator_reads_require_bearer_token(client):
    assert client.get("/api/status").status_code == 200
    assert client.get("/api/scene").status_code == 401
    assert client.get(
        "/api/scene",
        headers={"Authorization": "Bearer test-admin-token"},
    ).status_code == 200


def test_operator_mutations_require_bearer_token(client):
    payload = {"name": "Private desk", "sources": []}
    assert client.post("/api/scene", json=payload).status_code == 401
    assert client.post(
        "/api/scene",
        json=payload,
        headers={"Authorization": "Bearer test-admin-token"},
    ).status_code == 200


def test_judge_mode_allows_safe_demo_mutations_but_not_operator_actions(client, monkeypatch):
    monkeypatch.setenv("ONRECORD_JUDGE_MODE", "true")
    monkeypatch.setenv("ONRECORD_PROTECT_READS", "false")

    scene_response = client.post(
        "/api/scene",
        json={"name": "Public demo", "sources": []},
    )
    assert scene_response.status_code == 200
    assert client.post("/api/scout/run").status_code == 200
    assert client.post("/api/desk/delete_test").status_code == 200
    assert client.post("/api/desk/restore_memory").status_code == 200

    # Task actions remain operator-only; judge mode cannot perform arbitrary Clerk actions.
    assert client.post(
        "/api/clerk/open",
        json={"task_id": "missing"},
    ).status_code == 401


def test_security_headers_are_present(client):
    response = client.get("/api/status")
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "SAMEORIGIN"
    assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
    assert response.headers["Permissions-Policy"] == "camera=(), microphone=(), geolocation=()"
