from __future__ import annotations

import json
import re
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from agent_security_sdk.adapter import AgentAdapter
from agent_security_sdk.models import AgentTurnResult, ToolSpec
from agent_security_sdk.telemetry import TraceRecorder


OpenManusRunner = Callable[[str, str, dict[str, Any]], dict[str, Any]]


class OpenManusAdapter(AgentAdapter):
    def __init__(
        self,
        session_id: str = "openmanus-offline",
        *,
        runner: OpenManusRunner | None = None,
        fixture_path: str | Path | None = None,
    ) -> None:
        self.recorder = TraceRecorder(session_id=session_id)
        self._runner = runner
        self._fixture = _load_fixture(fixture_path)

    def send_message(self, user_id: str, message: str, context: dict[str, Any]) -> AgentTurnResult:
        payload = self._run(user_id, message, context)
        redacted_message = _redact(message)
        answer = _redact(str(payload.get("answer") or self._fixture.get("answer") or "OpenManus task completed."))
        answer = answer.replace("{message}", redacted_message)
        tool_calls = [
            _normalise_tool_call(item, index)
            for index, item in enumerate(payload.get("tool_calls") or self._fixture.get("tool_calls") or [])
        ]
        audit_events = _audit_events(tool_calls, user_id=user_id, session_id=self.recorder.session_id)
        audit_events.extend(_normalise_audit_event(item) for item in payload.get("audit_events") or [])
        result = AgentTurnResult(
            user_id=user_id,
            message=redacted_message,
            answer=answer,
            blocked=bool(payload.get("blocked", False)),
            risk_level=str(payload.get("risk_level") or self._fixture.get("risk_level") or "low"),
            tool_calls=tool_calls,
            business_events=list(payload.get("business_events") or []),
            audit_events=audit_events,
        )
        self.recorder.record_turn(result)
        return result

    def list_tools(self) -> list[ToolSpec]:
        source = getattr(self._runner, "list_tools", None)
        tools = source() if callable(source) else self._fixture.get("tools", [])
        return [_normalise_tool_spec(item) for item in tools]

    def export_trajectory(self) -> dict[str, Any]:
        trajectory = self.recorder.export()
        turns = trajectory["turns"]
        trajectory["agent_framework"] = "OpenManus"
        trajectory["tool_calls"] = [call for turn in turns for call in turn.get("tool_calls", [])]
        trajectory["audit_events"] = [event for turn in turns for event in turn.get("audit_events", [])]
        return trajectory

    def reset_session(self, session_id: str) -> None:
        self.recorder.reset(session_id)

    def _run(self, user_id: str, message: str, context: dict[str, Any]) -> dict[str, Any]:
        if self._runner is None:
            return {}
        payload = self._runner(user_id, message, context)
        if not isinstance(payload, dict):
            raise TypeError("OpenManus runner must return a dict payload.")
        return payload


def _load_fixture(fixture_path: str | Path | None) -> dict[str, Any]:
    path = Path(fixture_path) if fixture_path is not None else _default_fixture_path()
    return json.loads(path.read_text(encoding="utf-8"))


def _default_fixture_path() -> Path:
    for parent in Path(__file__).resolve().parents:
        candidate = parent / "third_party" / "OpenManus" / "fixtures" / "offline_turn.json"
        if candidate.exists():
            return candidate
    raise FileNotFoundError("OpenManus offline fixture not found.")


def _normalise_tool_spec(item: Any) -> ToolSpec:
    if isinstance(item, ToolSpec):
        return item
    if hasattr(item, "to_dict"):
        item = item.to_dict()
    if not isinstance(item, dict):
        raise TypeError("OpenManus tool spec must be a dict or ToolSpec.")
    return ToolSpec(
        name=str(item.get("name") or "openmanus_tool"),
        risk_level=str(item.get("risk_level") or "medium"),
        description=str(item.get("description") or "OpenManus tool."),
    )


def _normalise_tool_call(item: Any, index: int) -> dict[str, Any]:
    if not isinstance(item, dict):
        item = {"name": str(item)}
    name = str(item.get("name") or "openmanus_tool")
    arguments = item.get("arguments", item.get("args", {}))
    result = item.get("result", item.get("result_summary", ""))
    return {
        "tool_call_id": str(item.get("tool_call_id") or f"openmanus_tool_{index}"),
        "name": name,
        "args_summary": _summary(arguments),
        "result_summary": _summary(result),
        "timestamp": str(item.get("timestamp") or _utc_now_iso()),
    }


def _normalise_audit_event(item: Any) -> dict[str, Any]:
    if not isinstance(item, dict):
        return {"event_type": "openmanus_audit", "summary": _summary(item), "timestamp": _utc_now_iso()}
    payload = {str(key): _redact(value) if isinstance(value, str) else value for key, value in item.items()}
    payload.setdefault("timestamp", _utc_now_iso())
    return payload


def _audit_events(tool_calls: list[dict[str, Any]], *, user_id: str, session_id: str) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for call in tool_calls:
        common = {
            "user_id": user_id,
            "session_id": session_id,
            "tool_name": call["name"],
            "source": "openmanus_adapter",
            "decision": "allow",
        }
        events.append(
            {
                **common,
                "event_type": "tool_call",
                "call_type": "tool_call",
                "args_summary": call["args_summary"],
                "timestamp": call["timestamp"],
            }
        )
        events.append(
            {
                **common,
                "event_type": "tool_result",
                "call_type": "tool_result",
                "result_summary": call["result_summary"],
                "timestamp": _utc_now_iso(),
            }
        )
    return events


def _summary(value: Any, *, limit: int = 240) -> str:
    if isinstance(value, str):
        text = value
    else:
        text = json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
    text = _redact(text)
    return text if len(text) <= limit else f"{text[: limit - 3]}..."


def _redact(text: str) -> str:
    return re.sub(r"\b(1[3-9]\d)(\d{4})(\d{4})\b", r"\1****\3", text)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
