from __future__ import annotations

from typing import Any

from redsentinel.adapters.engine.adapter import AgentAdapter
from redsentinel.adapters.engine.models import AgentTurnResult, ToolSpec
from redsentinel.application.contracts import AgentRegistration, EvaluationRequest
from redsentinel.application.engine.service import OPENMANUS_BENCHMARK_ID, ProductEvaluationService


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


class RuntimeErrorOpenManusRealAdapter(AgentAdapter):
    def __init__(self) -> None:
        self.session_id = ""
        self.turns: list[dict[str, Any]] = []

    def send_message(self, user_id: str, message: str, context: dict[str, Any]) -> AgentTurnResult:
        result = AgentTurnResult(
            user_id=user_id,
            message=message,
            answer="docker timed out after 1s",
            blocked=True,
            risk_level="high",
            tool_calls=[],
            audit_events=[
                {
                    "event_type": "runtime_error",
                    "call_type": "runtime",
                    "tool_name": "openmanus_runtime",
                    "decision": "error",
                    "risk_score": 100.0,
                    "reason": "docker timed out after 1s",
                    "rules": ["openmanus_real.runtime_error"],
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
        "redsentinel.application.engine.service._openmanus_real_adapter_for",
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


def test_openmanus_runtime_errors_do_not_count_as_defense_blocks(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://api.example.test/v1")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-test")
    monkeypatch.setattr(
        "redsentinel.application.engine.service._openmanus_real_adapter_for",
        lambda _registration, output_root: RuntimeErrorOpenManusRealAdapter(),
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

    assert report.status == "incomplete"
    assert report.false_positive_rate == 0.0
    assert report.defense_success_rate == 0.0
    assert report.attack_success_rate == 0.0
    assert report.summary["baseline_runtime_error_count"] == len(report.scenario_results)
    assert report.summary["runtime_error_count"] == len(report.scenario_results)
    assert set(report.summary["baseline_runtime_error_scenarios"]) == {
        item.scenario_id for item in report.scenario_results
    }
    assert set(report.summary["runtime_error_scenarios"]) == {item.scenario_id for item in report.scenario_results}
    assert any("baseline runtime errors in scenarios" in issue for issue in report.summary["integrity_issues"])
    assert all(item.clean_decision == "allow" for item in report.scenario_results)
    assert all(item.actual_decision == "allow" for item in report.scenario_results)
    assert all(item.node_status.get(item.category) == "runtime_error" for item in report.scenario_results)
    assert not any(finding.title == "Clean business flow was blocked." for finding in report.findings)
