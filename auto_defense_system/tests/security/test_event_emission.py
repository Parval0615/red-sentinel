from __future__ import annotations

import json
from pathlib import Path

from auto_defense_system.runtime import SecurityEventEmitter


EXPECTED_EVENT_FIELDS = {
    "event_id",
    "session_id",
    "agent_id",
    "call_type",
    "decision",
    "reason",
    "risk_score",
    "pending",
    "payload_summary",
    "timestamp",
}


def test_security_event_emitter_writes_jsonl_and_trims_to_max_events(tmp_path: Path) -> None:
    events_path = tmp_path / "security_events.jsonl"
    emitter = SecurityEventEmitter(events_path, max_events=3)

    emitter.emit(
        event_id="evt_seed",
        session_id="session-1",
        agent_id="agent-1",
        call_type="tool_call",
        decision="allow",
        reason="seed event",
        risk_score=1.0,
        payload_summary={"tool": "search"},
        timestamp="2026-07-01T00:00:00Z",
    )
    emitter.emit(
        event_id="evt_tool",
        session_id="session-1",
        agent_id="agent-1",
        call_type="tool_call",
        decision="allow",
        reason="tool call allowed",
        risk_score=10.0,
        payload_summary={"tool": "db_query", "api_token": "tok-raw-value"},
        timestamp="2026-07-01T00:00:01Z",
    )
    emitter.emit(
        event_id="evt_code",
        session_id="session-1",
        agent_id="agent-1",
        call_type="code_exec",
        decision="ask",
        reason="code execution needs review",
        risk_score=65.0,
        payload_summary={"command": "python app.py --token=tok-command-value"},
        timestamp="2026-07-01T00:00:02Z",
    )
    emitter.emit(
        event_id="evt_file",
        session_id="session-1",
        agent_id="agent-1",
        call_type="file_access",
        decision="block",
        reason="password=hunter2 was blocked",
        risk_score=90.0,
        payload_summary={"path": "/tmp/report.txt", "nested": {"password": "hunter2"}},
        timestamp="2026-07-01T00:00:03Z",
    )

    events = _read_jsonl(events_path)
    raw_jsonl = events_path.read_text(encoding="utf-8")

    assert [event["event_id"] for event in events] == ["evt_tool", "evt_code", "evt_file"]
    assert [event["call_type"] for event in events] == ["tool_call", "code_exec", "file_access"]
    assert [event["decision"] for event in events] == ["allow", "ask", "deny"]
    assert [event["pending"] for event in events] == [False, True, False]
    assert all(set(event) == EXPECTED_EVENT_FIELDS for event in events)
    assert events[0]["payload_summary"]["api_token"] == "[REDACTED]"
    assert events[1]["payload_summary"]["command"] == "python app.py --token=[REDACTED]"
    assert events[2]["payload_summary"]["nested"]["password"] == "[REDACTED]"
    assert events[2]["reason"] == "password=[REDACTED] was blocked"
    assert "tok-raw-value" not in raw_jsonl
    assert "tok-command-value" not in raw_jsonl
    assert "hunter2" not in raw_jsonl
    assert "evt_seed" not in raw_jsonl


def _read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
