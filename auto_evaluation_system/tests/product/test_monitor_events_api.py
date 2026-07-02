from __future__ import annotations

import json
from pathlib import Path

import pytest

from auto_evaluation_system.product_api.app import create_app
from auto_evaluation_system.product_api.auth_password import hash_password
from auto_evaluation_system.product_api.auth_service import ProductAuthService


def _client(tmp_path: Path):
    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient

    return TestClient(create_app(storage_root=tmp_path), raise_server_exceptions=False)


def _auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _token(tmp_path: Path, *, username: str, role: str) -> str:
    auth_service = ProductAuthService(storage_root=tmp_path)
    password_hash, password_salt = hash_password("correct-horse-battery-staple")
    user = auth_service.storage.write_user(
        f"usr_{username}",
        {
            "username": username,
            "email": f"{username}@example.test",
            "password_hash": password_hash,
            "password_salt": password_salt,
            "role": role,
        },
    )
    return auth_service.issue_access_token(user, expires_in_seconds=3600)


def _write_security_events(storage_root: Path) -> None:
    events = [
        {
            "event_id": "evt_allow_checkout",
            "timestamp": "2026-07-01T10:00:00Z",
            "session_id": "session-alpha",
            "agent_id": "checkout-agent",
            "call_type": "llm_inference",
            "decision": "allow",
            "reason": "Clean request.",
            "risk_score": 10.0,
        },
        {
            "event_id": "evt_deny_refund",
            "timestamp": "2026-07-01T10:01:00Z",
            "session_id": "session-alpha",
            "agent_id": "checkout-agent",
            "call_type": "tool_call",
            "decision": "deny",
            "reason": "Refund amount exceeds policy.",
            "risk_score": 85.0,
        },
        {
            "event_id": "evt_ask_code",
            "timestamp": "2026-07-01T10:02:00Z",
            "session_id": "session-beta",
            "agent_id": "ops-agent",
            "call_type": "code_execution",
            "decision": "ask",
            "reason": "Human confirmation required.",
            "risk_score": 91.0,
        },
        {
            "event_id": "evt_deny_refund_retry",
            "timestamp": "2026-07-01T10:03:00Z",
            "session_id": "session-gamma",
            "agent_id": "checkout-agent",
            "call_type": "tool_call",
            "decision": "deny",
            "reason": "Repeated refund manipulation.",
            "risk_score": 65.0,
        },
    ]
    (storage_root / "security_events.jsonl").write_text(
        "\n".join(json.dumps(event) for event in events) + "\n",
        encoding="utf-8",
    )


def test_monitor_events_admin_can_read_events_and_summary_counts(tmp_path: Path) -> None:
    _write_security_events(tmp_path)
    client = _client(tmp_path)
    headers = _auth_header(_token(tmp_path, username="security-admin", role="admin"))

    response = client.get("/v1/monitor/events", headers=headers)

    assert response.status_code == 200
    events = response.json()
    assert [event["event_id"] for event in events] == [
        "evt_allow_checkout",
        "evt_deny_refund",
        "evt_ask_code",
        "evt_deny_refund_retry",
    ]
    assert events[2]["status"] == "pending"

    summary_response = client.get("/v1/monitor/events/summary", headers=headers)
    assert summary_response.status_code == 200
    summary = summary_response.json()
    assert summary["total_events"] == 4
    assert summary["decision_counts"] == {"allow": 1, "deny": 2, "ask": 1}
    assert summary["high_risk_count"] == 2
    assert summary["latest_event_id"] == "evt_deny_refund_retry"


def test_monitor_events_rejects_non_admin_users(tmp_path: Path) -> None:
    _write_security_events(tmp_path)
    client = _client(tmp_path)
    headers = _auth_header(_token(tmp_path, username="regular-user", role="user"))

    for path in ["/v1/monitor/events", "/v1/monitor/events/summary"]:
        response = client.get(path, headers=headers)

        assert response.status_code == 403
        assert response.json()["detail"]["error_code"] == "admin_required"


def test_monitor_events_filters_by_agent_decision_session_and_limit(tmp_path: Path) -> None:
    _write_security_events(tmp_path)
    client = _client(tmp_path)
    headers = _auth_header(_token(tmp_path, username="security-admin", role="admin"))

    by_agent = client.get("/v1/monitor/events?agent_id=checkout-agent", headers=headers)
    assert by_agent.status_code == 200
    assert [event["event_id"] for event in by_agent.json()] == [
        "evt_allow_checkout",
        "evt_deny_refund",
        "evt_deny_refund_retry",
    ]

    by_decision = client.get("/v1/monitor/events?decision=deny", headers=headers)
    assert by_decision.status_code == 200
    assert [event["event_id"] for event in by_decision.json()] == [
        "evt_deny_refund",
        "evt_deny_refund_retry",
    ]

    by_session = client.get("/v1/monitor/events?session_id=session-alpha", headers=headers)
    assert by_session.status_code == 200
    assert [event["event_id"] for event in by_session.json()] == [
        "evt_allow_checkout",
        "evt_deny_refund",
    ]

    limited = client.get("/v1/monitor/events?limit=2", headers=headers)
    assert limited.status_code == 200
    assert [event["event_id"] for event in limited.json()] == [
        "evt_ask_code",
        "evt_deny_refund_retry",
    ]

    combined = client.get(
        "/v1/monitor/events?agent_id=checkout-agent&decision=deny&session_id=session-alpha",
        headers=headers,
    )
    assert combined.status_code == 200
    assert [event["event_id"] for event in combined.json()] == ["evt_deny_refund"]
