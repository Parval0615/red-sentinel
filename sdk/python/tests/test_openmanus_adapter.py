from agent_security_sdk.openmanus import OpenManusAdapter


def test_openmanus_adapter_runs_offline_fixture_and_exports_events() -> None:
    adapter = OpenManusAdapter(session_id="openmanus-test")

    tools = adapter.list_tools()
    result = adapter.send_message("user_001", "查手机号 13812345678 的公开信息", {"role": "analyst"})
    trajectory = adapter.export_trajectory()

    assert {tool.name for tool in tools} >= {
        "browser_search",
        "python_execute",
        "send_email",
        "file_operation",
        "api_call",
        "db_query",
    }
    assert result.blocked is False
    assert result.risk_level == "low"
    assert result.tool_calls
    assert {event["event_type"] for event in result.audit_events} >= {"tool_call", "tool_result"}
    assert trajectory["session_id"] == "openmanus-test"
    assert trajectory["agent_framework"] == "OpenManus"
    assert trajectory["tool_calls"] == result.tool_calls
    assert trajectory["audit_events"] == result.audit_events
    assert "13812345678" not in str(trajectory)
    assert "138****5678" in str(trajectory)


def test_openmanus_adapter_accepts_runner_payload_and_resets_session() -> None:
    class Runner:
        def __call__(self, user_id: str, message: str, context: dict) -> dict:
            return {
                "answer": f"runner answered {message}",
                "blocked": True,
                "risk_level": "high",
                "tool_calls": [
                    {
                        "tool_call_id": "call_001",
                        "name": "python_execute",
                        "args": {"code": "print('ok')"},
                        "result_summary": "ok",
                    }
                ],
                "audit_events": [{"event_type": "runner_audit", "summary": "checked 13900001111"}],
            }

        def list_tools(self) -> list[dict]:
            return [{"name": "python_execute", "risk_level": "high", "description": "Run Python code."}]

    adapter = OpenManusAdapter(session_id="openmanus-runner", runner=Runner())

    assert adapter.list_tools()[0].name == "python_execute"
    result = adapter.send_message("user_002", "hello 13900001111", {})
    assert result.blocked is True
    assert result.risk_level == "high"
    assert any(event["event_type"] == "runner_audit" for event in result.audit_events)
    assert "13900001111" not in str(adapter.export_trajectory())

    adapter.reset_session("openmanus-reset")
    trajectory = adapter.export_trajectory()
    assert trajectory["session_id"] == "openmanus-reset"
    assert trajectory["turns"] == []
    assert trajectory["tool_calls"] == []
    assert trajectory["audit_events"] == []
