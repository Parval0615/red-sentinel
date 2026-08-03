from __future__ import annotations

import json
from pathlib import Path

from redsentinel.application.contracts import SupervisionEvent
from redsentinel.application.engine.supervision import SupervisionEventStore


def _event_payload(
    event_id: str,
    *,
    decision: str = "allow",
    status: str = "observed",
    call_type: str = "tool_call",
    risk_score: float = 10.0,
    timestamp: str = "2026-07-01T00:00:00Z",
) -> dict:
    return {
        "event_id": event_id,
        "timestamp": timestamp,
        "tenant_id": "tenant_001",
        "agent_id": "agent_001",
        "call_type": call_type,
        "decision": decision,
        "reason": f"{decision} decision for {call_type}",
        "risk_score": risk_score,
        "confidence": 0.9,
        "payload_summary": {"target": call_type},
        "source": "pytest",
        "status": status,
    }


def _read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_supervision_events_serialize_allow_deny_and_ask(tmp_path: Path) -> None:
    store = SupervisionEventStore(storage_root=tmp_path)

    stored_events = [
        store.append_event(
            SupervisionEvent.model_validate(
                _event_payload("evt_allow", decision="allow", status="observed", call_type="tool_call")
            )
        ),
        store.append_event(_event_payload("evt_deny", decision="deny", status="blocked", call_type="file_access")),
        store.append_event(_event_payload("evt_ask", decision="ask", status="pending", call_type="code_execution")),
    ]
    serialized_events = _read_jsonl(store.events_path)

    assert [event.event_id for event in stored_events] == ["evt_allow", "evt_deny", "evt_ask"]
    assert [event["event_id"] for event in serialized_events] == ["evt_allow", "evt_deny", "evt_ask"]
    assert [event["decision"] for event in serialized_events] == ["allow", "deny", "ask"]
    assert [event["status"] for event in serialized_events] == ["observed", "blocked", "pending"]
    assert all(event["schema_version"] == "supervision-event-v0.1" for event in serialized_events)
    assert all(
        set(event)
        == {
            "agent_id",
            "call_type",
            "confidence",
            "decision",
            "event_id",
            "payload_summary",
            "reason",
            "risk_score",
            "schema_version",
            "source",
            "status",
            "tenant_id",
            "timestamp",
        }
        for event in serialized_events
    )


def test_supervision_store_reads_recent_events_in_append_order(tmp_path: Path) -> None:
    store = SupervisionEventStore(storage_root=tmp_path, recent_event_limit=2, max_events=10)

    for index in range(5):
        store.append_event(
            _event_payload(
                f"evt_{index}",
                call_type="tool_call",
                timestamp=f"2026-07-01T00:00:0{index}Z",
            )
        )

    default_recent = store.read_recent_events()
    explicit_recent = store.read_recent_events(limit=3)

    assert [event.event_id for event in default_recent] == ["evt_3", "evt_4"]
    assert [event.event_id for event in explicit_recent] == ["evt_2", "evt_3", "evt_4"]


def test_supervision_summary_and_latest_snapshot_are_written(tmp_path: Path) -> None:
    store = SupervisionEventStore(storage_root=tmp_path, recent_event_limit=3)

    store.append_event(
        _event_payload(
            "evt_allow",
            decision="allow",
            status="observed",
            call_type="tool_call",
            risk_score=12.0,
            timestamp="2026-07-01T00:00:01Z",
        )
    )
    store.append_event(
        _event_payload(
            "evt_deny",
            decision="deny",
            status="blocked",
            call_type="file_access",
            risk_score=91.0,
            timestamp="2026-07-01T00:00:02Z",
        )
    )
    store.append_event(
        _event_payload(
            "evt_ask",
            decision="ask",
            status="pending",
            call_type="code_execution",
            risk_score=80.0,
            timestamp="2026-07-01T00:00:03Z",
        )
    )

    summary = store.compute_summary()
    latest = json.loads(store.latest_path.read_text(encoding="utf-8"))

    assert summary["schema_version"] == "supervision-summary-v0.1"
    assert summary["total_events"] == 3
    assert summary["decision_counts"] == {"allow": 1, "deny": 1, "ask": 1}
    assert summary["status_counts"]["observed"] == 1
    assert summary["status_counts"]["blocked"] == 1
    assert summary["status_counts"]["pending"] == 1
    assert summary["call_type_counts"]["tool_call"] == 1
    assert summary["call_type_counts"]["file_access"] == 1
    assert summary["call_type_counts"]["code_execution"] == 1
    assert summary["high_risk_count"] == 2
    assert summary["pending_count"] == 1
    assert summary["latest_event_id"] == "evt_ask"
    assert summary["latest_timestamp"] == "2026-07-01T00:00:03Z"
    assert latest["schema_version"] == "supervision-latest-v0.1"
    assert [event["event_id"] for event in latest["events"]] == ["evt_allow", "evt_deny", "evt_ask"]
    assert latest["summary"]["decision_counts"] == {"allow": 1, "deny": 1, "ask": 1}
    assert latest["pending_decisions"][0]["event_id"] == "evt_ask"


def test_supervision_events_jsonl_is_trimmed_to_max_events(tmp_path: Path) -> None:
    store = SupervisionEventStore(storage_root=tmp_path, max_events=3, recent_event_limit=10)

    for index in range(5):
        store.append_event(_event_payload(f"evt_{index}", timestamp=f"2026-07-01T00:00:0{index}Z"))

    serialized_events = _read_jsonl(store.events_path)
    latest = json.loads(store.latest_path.read_text(encoding="utf-8"))

    assert [event["event_id"] for event in serialized_events] == ["evt_2", "evt_3", "evt_4"]
    assert [event["event_id"] for event in latest["events"]] == ["evt_2", "evt_3", "evt_4"]


def test_supervision_ask_event_initializes_pending_decision(tmp_path: Path) -> None:
    store = SupervisionEventStore(
        storage_root=tmp_path,
        default_action="allow",
        pending_ttl_seconds=120,
    )
    ask_event = _event_payload(
        "evt_pending",
        decision="ask",
        status="pending",
        call_type="code_execution",
        timestamp="2026-07-01T12:00:00Z",
    )

    store.append_event(ask_event)
    store.append_event(ask_event)
    pending_payload = json.loads(store.pending_decisions_path.read_text(encoding="utf-8"))
    records = store.read_pending_decisions()

    assert pending_payload["schema_version"] == "pending-decisions-v0.1"
    assert len(pending_payload["decisions"]) == 1
    assert len(records) == 1
    assert records[0].event_id == "evt_pending"
    assert records[0].requested_at == "2026-07-01T12:00:00Z"
    assert records[0].expires_at == "2026-07-01T12:02:00Z"
    assert records[0].default_action == "allow"
    assert records[0].supervisor_action is None
    assert records[0].resolved_at is None
