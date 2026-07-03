from __future__ import annotations

import json
from pathlib import Path

import pytest

from auto_evaluation_system.product_api.contracts import AgentRegistration, EvaluationRequest
from auto_evaluation_system.product_api.service import ProductEvaluationService
from auto_evaluation_system.product_api.supervision import SupervisionEventStore


def _write_runtime_security_events(storage_root: Path, *, evaluation_id: str, agent_id: str) -> None:
    events = [
        {
            "event_id": "evt_bridge_allow",
            "timestamp": "2026-07-01T10:00:00Z",
            "session_id": f"{evaluation_id}:clean",
            "agent_id": agent_id,
            "call_type": "tool_call",
            "decision": "allow",
            "reason": "Clean tool call stayed in policy.",
            "risk_score": 10.0,
            "payload_summary": {"tool": "search_orders"},
        },
        {
            "event_id": "evt_bridge_deny",
            "timestamp": "2026-07-01T10:01:00Z",
            "session_id": f"{evaluation_id}:attack",
            "agent_id": agent_id,
            "call_type": "file_access",
            "decision": "deny",
            "reason": "File access exceeded the workspace boundary.",
            "risk_score": 92.0,
            "payload_summary": {"path": "../secrets/customer_export.csv"},
        },
        {
            "event_id": "evt_bridge_ask",
            "timestamp": "2026-07-01T10:02:00Z",
            "session_id": f"{evaluation_id}:ask",
            "agent_id": agent_id,
            "call_type": "code_exec",
            "decision": "ask",
            "pending": True,
            "reason": "Code execution requires supervisor confirmation.",
            "risk_score": 76.0,
            "payload_summary": {"language": "python"},
        },
        {
            "event_id": "evt_unrelated",
            "timestamp": "2026-07-01T10:03:00Z",
            "session_id": "eval_other:attack",
            "agent_id": agent_id,
            "call_type": "tool_call",
            "decision": "deny",
            "reason": "Unrelated evaluation event.",
            "risk_score": 80.0,
        },
    ]
    (storage_root / "security_events.jsonl").write_text(
        "\n".join(json.dumps(event) for event in events) + "\n",
        encoding="utf-8",
    )


def test_run_evaluation_bridges_runtime_security_events_to_supervision_latest(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = ProductEvaluationService(storage_root=tmp_path)
    registration = service.register_agent(
        AgentRegistration(agent_id="ecommerce_customer_guide", name="E-commerce Guide")
    )
    real_run_evaluation = service._run_evaluation

    def run_and_emit_events(
        evaluation_id: str,
        registration: AgentRegistration,
        request: EvaluationRequest,
<<<<<<< HEAD
        **kwargs: object,
=======
>>>>>>> origin/main
    ) -> object:
        _write_runtime_security_events(
            tmp_path,
            evaluation_id=evaluation_id,
            agent_id=registration.agent_id,
        )
<<<<<<< HEAD
        return real_run_evaluation(evaluation_id, registration, request, **kwargs)
=======
        return real_run_evaluation(evaluation_id, registration, request)
>>>>>>> origin/main

    monkeypatch.setattr(service, "_run_evaluation", run_and_emit_events)

    status = service.run_evaluation(
        EvaluationRequest(
            tenant_id=registration.tenant_id,
            agent_id=registration.agent_id,
            scenarios=["support-pii-masking"],
        )
    )

    store = SupervisionEventStore(storage=service.storage)
    latest = store.write_latest_snapshot()
    bridged_events = [
        event for event in latest["events"] if event["event_id"].startswith("evt_bridge_")
    ]

    assert status.status == "completed"
    assert [event["event_id"] for event in bridged_events] == [
        "evt_bridge_allow",
        "evt_bridge_deny",
        "evt_bridge_ask",
    ]
    assert [event["decision"] for event in bridged_events] == ["allow", "deny", "ask"]
    assert [event["status"] for event in bridged_events] == ["observed", "blocked", "pending"]
    assert bridged_events[2]["call_type"] == "code_execution"
    assert latest["summary"]["decision_counts"] == {"allow": 1, "deny": 1, "ask": 1}
    assert latest["pending_decisions"][0]["event_id"] == "evt_bridge_ask"

    bridged_again = service._bridge_runtime_events_to_supervision(
        status.evaluation_id,
        tenant_id=registration.tenant_id,
        agent_id=registration.agent_id,
    )
    latest_after_repeat = store.write_latest_snapshot()

    assert bridged_again == 0
    assert [
        event["event_id"]
        for event in latest_after_repeat["events"]
        if event["event_id"].startswith("evt_bridge_")
    ] == ["evt_bridge_allow", "evt_bridge_deny", "evt_bridge_ask"]
