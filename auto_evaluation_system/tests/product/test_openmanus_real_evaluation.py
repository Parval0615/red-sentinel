from __future__ import annotations

from typing import Any

from agent_security_sdk.adapter import AgentAdapter
from agent_security_sdk.models import AgentTurnResult, ToolSpec
from auto_evaluation_system.product_api.contracts import AgentRegistration, EvaluationRequest
from auto_evaluation_system.product_api.service import OPENMANUS_BENCHMARK_ID, ProductEvaluationService


class FakeOpenManusRealAdapter(AgentAdapter):
    def __init__(self) -> None:
        self.session_id = ""
        self.turns: list[dict[str, Any]] = []

    def send_message(self, user_id: str, message: str, context: dict[str, Any]) -> AgentTurnResult:
        blocked = context.get("defense_mode") == "guarded" and context.get("case_type") == "controlled"
        executed = context.get("defense_mode") == "baseline"
        decision = "deny" if blocked else "allow"
        result = AgentTurnResult(
            user_id=user_id,
            message=message,
            answer="fake real OpenManus result",
            blocked=blocked,
            risk_level="high" if blocked else "low",
            tool_calls=[
                {
                    "tool_call_id": "call_1",
                    "name": "python_execute",
                    "args_summary": "{}",
                    "result_summary": "ok" if executed else "",
                    "executed": executed,
                }
            ],
            audit_events=[
                {
                    "event_type": "monitor_decision",
                    "call_type": "code_execution",
                    "tool_name": "python_execute",
                    "decision": decision,
                    "risk_score": 80.0 if blocked else 0.0,
                    "reason": "fake decision",
                    "rules": ["fake.rule"],
                    "source": "openmanus_real_runner",
                }
            ],
        )
        self.turns.append(result.to_dict())
        return result

    def list_tools(self) -> list[ToolSpec]:
        return [ToolSpec(name="python_execute", risk_level="high", description="fake")]

    def export_trajectory(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "agent_framework": "OpenManus",
            "runtime_mode": "openmanus_real",
            "real_runtime": True,
            "simulated": False,
            "turns": list(self.turns),
        }

    def reset_session(self, session_id: str) -> None:
        self.session_id = session_id
        self.turns = []


def test_openmanus_real_mode_builds_real_runtime_report(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://api.example.test/v1")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-test")
    monkeypatch.setattr(
        "auto_evaluation_system.product_api.service._openmanus_real_adapter_for",
        lambda _registration, output_root: FakeOpenManusRealAdapter(),
    )
    service = ProductEvaluationService(storage_root=tmp_path)
    service.register_agent(
        AgentRegistration(
            tenant_id="tenant_1",
            username="tenant_1",
            agent_id="openmanus_official",
            name="OpenManus Official",
            domain="general",
            integration_type="source",
            framework="OpenManus",
            adapter_type="openmanus",
            status="ready",
        )
    )

    status = service.run_evaluation(
        EvaluationRequest(
            tenant_id="tenant_1",
            agent_id="openmanus_official",
            benchmark_id=OPENMANUS_BENCHMARK_ID,
            benchmark_version="v0.1",
            mode="openmanus_real",
        )
    )
    report = service.get_report(status.report_id or status.evaluation_id, tenant_id="tenant_1")

    assert report.benchmark_id == OPENMANUS_BENCHMARK_ID
    assert report.summary["runtime_mode"] == "openmanus_real"
    assert report.summary["real_runtime"] is True
    assert report.summary["simulated"] is False
    assert report.summary["baseline_attack_success_rate"] == 1.0
    assert report.attack_success_rate == 0.0
    assert report.false_positive_rate == 0.0
    assert report.summary["real_tool_execution_count"] >= len(report.scenario_results)
