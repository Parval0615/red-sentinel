from __future__ import annotations

import pytest

from auto_evaluation_system.product_api.app import create_app


def _raw_client(tmp_path, *, raise_server_exceptions: bool = True):
    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient

    return TestClient(create_app(storage_root=tmp_path), raise_server_exceptions=raise_server_exceptions)


def _client(tmp_path, *, username: str = "private_tenant", raise_server_exceptions: bool = True):
    client = _raw_client(tmp_path, raise_server_exceptions=raise_server_exceptions)
    response = client.post(
        "/v1/auth/register",
        json={
            "username": username,
            "email": f"{username}@example.test",
            "password": "correct-horse-battery-staple",
        },
    )
    assert response.status_code == 200
    client.headers.update({"Authorization": f"Bearer {response.json()['access_token']}"})
    return client


def test_supervision_api_requires_authentication(tmp_path) -> None:
    client = _raw_client(tmp_path, raise_server_exceptions=False)

    response = client.get("/v1/supervision/latest")

    assert response.status_code == 401
    assert response.json()["detail"]["error_code"] == "auth_required"


def test_supervision_latest_is_empty_before_events(tmp_path) -> None:
    client = _client(tmp_path)

    response = client.get("/v1/supervision/latest")

    assert response.status_code == 200
    body = response.json()
    assert body["events"] == []
    assert body["summary"]["total_events"] == 0
    assert body["summary"]["decision_counts"] == {"allow": 0, "deny": 0, "ask": 0}


def test_supervision_demo_seed_events_and_ask_response_flow(tmp_path) -> None:
    client = _client(tmp_path)

    seed_response = client.post("/v1/supervision/demo-seed")

    assert seed_response.status_code == 200
    seeded = seed_response.json()
    assert seeded["summary"]["decision_counts"] == {"allow": 1, "deny": 1, "ask": 1}
    pending_event_id = seeded["pending_decisions"][0]["event_id"]

    events_response = client.get("/v1/supervision/events?limit=2")
    assert events_response.status_code == 200
    assert [item["event_id"] for item in events_response.json()] == [
        "evt_demo_deny_file_access",
        "evt_demo_ask_code_execution",
    ]

    approve_response = client.post(
        f"/v1/supervision/ask/{pending_event_id}/respond",
        json={"action": "approve", "operator": "reviewer", "reason": "Approved for controlled demo."},
    )

    assert approve_response.status_code == 200
    assert approve_response.json()["status"] == "approved"

    latest_response = client.get("/v1/supervision/latest")
    assert latest_response.status_code == 200
    latest = latest_response.json()
    ask_event = next(item for item in latest["events"] if item["event_id"] == pending_event_id)
    assert ask_event["status"] == "approved"
    assert latest["pending_decisions"][0]["supervisor_action"] == "approve"

    duplicate_response = client.post(
        f"/v1/supervision/ask/{pending_event_id}/respond",
        json={"action": "reject", "operator": "reviewer", "reason": "Second response should fail."},
    )
    assert duplicate_response.status_code == 409
    assert duplicate_response.json()["detail"]["error_code"] == "supervision_event_resolved"


def test_supervision_api_isolates_events_by_tenant(tmp_path) -> None:
    tenant_a = _client(tmp_path, username="tenant_a")
    tenant_b = _client(tmp_path, username="tenant_b")

    seed_b = tenant_b.post("/v1/supervision/demo-seed")
    assert seed_b.status_code == 200
    tenant_b_pending_event_id = seed_b.json()["pending_decisions"][0]["event_id"]

    latest_a_before_seed = tenant_a.get("/v1/supervision/latest")
    events_a_before_seed = tenant_a.get("/v1/supervision/events")

    assert latest_a_before_seed.status_code == 200
    assert latest_a_before_seed.json()["events"] == []
    assert events_a_before_seed.status_code == 200
    assert events_a_before_seed.json() == []

    cross_tenant_response = tenant_a.post(
        f"/v1/supervision/ask/{tenant_b_pending_event_id}/respond",
        json={"action": "approve", "operator": "tenant_a", "reason": "Should not see tenant B event."},
    )
    assert cross_tenant_response.status_code == 404
    assert cross_tenant_response.json()["detail"]["error_code"] == "supervision_event_not_found"

    seed_a = tenant_a.post("/v1/supervision/demo-seed")
    assert seed_a.status_code == 200

    latest_a = tenant_a.get("/v1/supervision/latest").json()
    latest_b = tenant_b.get("/v1/supervision/latest").json()

    assert {event["tenant_id"] for event in latest_a["events"]} == {"tenant_a"}
    assert {event["tenant_id"] for event in latest_b["events"]} == {"tenant_b"}
    assert {record["tenant_id"] for record in latest_a["pending_decisions"]} == {"tenant_a"}
    assert {record["tenant_id"] for record in latest_b["pending_decisions"]} == {"tenant_b"}


def test_supervision_ask_response_handles_unknown_event(tmp_path) -> None:
    client = _client(tmp_path)

    response = client.post(
        "/v1/supervision/ask/missing/respond",
        json={"action": "reject", "operator": "reviewer", "reason": "Unknown event."},
    )

    assert response.status_code == 404
    assert response.json()["detail"]["error_code"] == "supervision_event_not_found"
