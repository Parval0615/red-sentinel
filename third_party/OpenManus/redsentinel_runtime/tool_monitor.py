from __future__ import annotations

import json
from typing import Any


def parse_tool_arguments(raw: str | None) -> dict[str, Any]:
    if not raw:
        return {}
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return {"raw_arguments": raw}
    return payload if isinstance(payload, dict) else {"value": payload}


def monitor_payload_for_tool(tool_name: str, arguments: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    name = str(tool_name or "")
    normalized = name.lower()

    if normalized == "python_execute":
        code = str(arguments.get("code") or "")
        return (
            "code_execution",
            {
                "tool_name": "python_execute",
                "arguments": {"code": code},
                "code": code,
                "source": "openmanus_real_runner",
            },
        )

    if normalized == "str_replace_editor":
        command = str(arguments.get("command") or "view").lower()
        path = str(arguments.get("path") or "")
        action = _file_action_for_editor_command(command)
        return (
            "file_access",
            {
                "tool_name": "file_operation",
                "arguments": {"action": action, "path": path, "command": command},
                "action": action,
                "path": path,
                "source": "openmanus_real_runner",
            },
        )

    if "browser" in normalized:
        target = _browser_target(arguments)
        return (
            "tool_call",
            {
                "tool_name": "browser_search",
                "arguments": {"query": target},
                "source": "openmanus_real_runner",
            },
        )

    if normalized in {"api_call", "http_request", "requests"}:
        endpoint = str(arguments.get("endpoint") or arguments.get("url") or arguments.get("uri") or arguments)
        method = str(arguments.get("method") or "GET")
        return (
            "tool_call",
            {
                "tool_name": "api_call",
                "arguments": {"method": method, "endpoint": endpoint},
                "source": "openmanus_real_runner",
            },
        )

    return (
        "tool_call",
        {
            "tool_name": name,
            "arguments": dict(arguments),
            "source": "openmanus_real_runner",
        },
    )


def evaluate_tool(tool_name: str, arguments: dict[str, Any], *, defense_mode: str) -> dict[str, Any]:
    call_type, payload = monitor_payload_for_tool(tool_name, arguments)
    if str(tool_name or "").lower() in {"terminate", "ask_human"}:
        return {
            "decision": "allow",
            "reason": f"{tool_name} allowed.",
            "risk_score": 0.0,
            "confidence": 1.0,
            "rules": [f"{tool_name}.allowed"],
            "call_type": call_type,
            "payload": payload,
        }
    if defense_mode == "baseline":
        return {
            "decision": "allow",
            "reason": "baseline_no_defense",
            "risk_score": 0.0,
            "confidence": 1.0,
            "rules": ["baseline.no_defense"],
            "call_type": call_type,
            "payload": payload,
        }

    from auto_defense_system.monitor_plugin import intercept

    decision = intercept(call_type, payload)
    data = decision.to_dict() if hasattr(decision, "to_dict") else dict(decision)
    data["call_type"] = call_type
    data["payload"] = payload
    return data


def evaluate_llm_input(messages: list[dict[str, Any]], *, defense_mode: str) -> dict[str, Any]:
    text = _primary_user_request(messages)
    payload = {
        "content": text,
        "messages": messages,
        "source": "openmanus_real_runner",
    }
    return _evaluate_boundary("llm_input", payload, defense_mode=defense_mode)


def evaluate_llm_output(content: str, *, defense_mode: str) -> dict[str, Any]:
    payload = {
        "content": content,
        "source": "openmanus_real_runner",
    }
    return _evaluate_boundary("llm_output", payload, defense_mode=defense_mode)


def _evaluate_boundary(call_type: str, payload: dict[str, Any], *, defense_mode: str) -> dict[str, Any]:
    if defense_mode == "baseline":
        return {
            "decision": "allow",
            "reason": "baseline_no_defense",
            "risk_score": 0.0,
            "confidence": 1.0,
            "rules": ["baseline.no_defense"],
            "call_type": call_type,
            "payload": payload,
        }

    from auto_defense_system.monitor_plugin import intercept

    decision = intercept(call_type, payload)
    data = decision.to_dict() if hasattr(decision, "to_dict") else dict(decision)
    data["call_type"] = call_type
    data["payload"] = payload
    return data


def _primary_user_request(messages: list[dict[str, Any]]) -> str:
    for message in messages:
        if str(message.get("role") or "").lower() == "user":
            content = str(message.get("content") or "")
            if content.strip():
                return content
    return "\n".join(str(message.get("content") or "") for message in messages)


def _file_action_for_editor_command(command: str) -> str:
    if command == "view":
        return "read"
    if command in {"create", "str_replace", "insert", "undo_edit"}:
        return "write"
    return command or "read"


def _browser_target(arguments: dict[str, Any]) -> str:
    for key in ("url", "query", "text", "goal", "instruction"):
        value = arguments.get(key)
        if value:
            return str(value)
    return json.dumps(arguments, ensure_ascii=False, sort_keys=True, default=str)


__all__ = [
    "evaluate_llm_input",
    "evaluate_llm_output",
    "evaluate_tool",
    "monitor_payload_for_tool",
    "parse_tool_arguments",
]
