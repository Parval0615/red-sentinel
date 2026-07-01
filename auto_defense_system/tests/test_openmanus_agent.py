from __future__ import annotations

from auto_defense_system.openmanus_agent import build_default_adapter
from auto_defense_system.openmanus_agent.runner import run_normal_business_demo


def test_openmanus_adapter_registers_and_invokes_business_tools() -> None:
    adapter = build_default_adapter()

    result = adapter.call_tool(
        "send_email",
        {"to": "ops@company.com", "subject": "Hello", "body": "Internal update."},
    )

    assert "SIMULATED" in result
    assert adapter.call_history[-1].name == "send_email"
    assert {"db_query", "file_operation", "api_call", "send_email"} == set(adapter.tools)


def test_openmanus_runner_executes_no_defense_demo() -> None:
    result = run_normal_business_demo()

    assert result["agent"] == "openmanus"
    assert result["mode"] == "no_defense_demo"
    assert result["tool_call"]["name"] == "send_email"
    assert "send_email" in result["registered_tools"]
