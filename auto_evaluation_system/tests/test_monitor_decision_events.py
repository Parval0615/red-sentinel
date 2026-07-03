from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from auto_evaluation_system.events import MonitorDecisionPayload, StepEvent, StepType


def test_monitor_decision_event_accepts_ask_payload() -> None:
    event = StepEvent(
        step_type=StepType.MONITOR_DECISION,
        timestamp=datetime.now(timezone.utc),
        monitor_decision=MonitorDecisionPayload(
            call_type="file_access",
            decision="ask",
            risk_level="medium",
            reason="file write requires approval",
            audit_object="file",
            ask_id="ask-123",
            approval_state="pending",
        ),
    )

    assert event.monitor_decision is not None
    assert event.monitor_decision.ask_id == "ask-123"


def test_monitor_decision_event_requires_ask_id_for_ask() -> None:
    with pytest.raises(ValidationError):
        StepEvent(
            step_type=StepType.MONITOR_DECISION,
            timestamp=datetime.now(timezone.utc),
            monitor_decision=MonitorDecisionPayload(
                call_type="code_execution",
                decision="ask",
                risk_level="high",
                reason="code execution requires approval",
                audit_object="code",
            ),
        )
