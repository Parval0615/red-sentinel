from __future__ import annotations

from auto_attack_system.attack_spec import AttackSpec
from auto_attack_system.evolution import evolve_attack_specs
from auto_evaluation_system.contracts.agent_security import OptimizationAction, OptimizationDirective
from auto_evaluation_system.product_api.contracts import (
    AgentSecurityReport,
    Finding,
    ReportArtifacts,
    ScenarioResult,
)


def _base_spec() -> AttackSpec:
    return AttackSpec(
        attack_id="agent:tool:tool_tampering:baseline",
        risk_type="tool_tampering",
        strategy="baseline_probe",
        intensity="light",
        target="adapter:invoke",
        label="controlled",
        goal="Probe tool node.",
        success_criteria=["baseline measured"],
        metadata={"node_id": "tool"},
    )


def test_evolve_attack_specs_from_report_findings() -> None:
    report = AgentSecurityReport(
        tenant_id="t1",
        agent_id="agent",
        benchmark="local",
        overall_score=60,
        risk_level="high",
        findings=[
            Finding(
                finding_id="f1",
                scenario_id="tool-node",
                severity="high",
                title="tool_tampering: unsafe tool call",
                description="Controlled attack was allowed.",
                business_impact="unsafe action",
                recommendation="Generate stronger tool_tampering variants.",
            )
        ],
        scenario_results=[],
        artifacts=ReportArtifacts(report_path="report.json"),
    )

    result = evolve_attack_specs([_base_spec()], report=report)

    assert len(result.evolved_specs) == 1
    assert result.evolved_specs[0].risk_type == "tool_tampering"
    assert result.evolved_specs[0].intensity == "heavy"
    assert result.evolved_specs[0].metadata["source"] == "self_evolution"
    assert result.evolved_specs[0].metadata["trigger_reason"] == "Finding f1 remained unresolved."
    assert result.evolution_records[0]["mutation_strategy"] == "chain_hijack"
    assert result.evolution_records[0]["expected_effect"] == "increase multi-step tool misuse coverage"


def test_evolve_attack_specs_from_directive_and_failed_attempts_dedupes() -> None:
    directive = OptimizationDirective(
        directive_id="dir-1",
        agent_name="agent",
        source="evaluation",
        target_node_id="memory",
        risk_type="memory_poisoning",
        priority="critical",
        recommended_actions=[OptimizationAction(type="generate_attack", name="memory_variant")],
        rationale="Memory poisoning persisted.",
        evidence_refs=["trace-1"],
    )

    result = evolve_attack_specs(
        [_base_spec()],
        directives=[directive],
        failed_attempts=[{"risk_type": "memory_poisoning", "node_id": "memory", "attempt_id": "a1"}],
    )

    assert len(result.evolved_specs) == 1
    assert result.evolved_specs[0].risk_type == "memory_poisoning"
    assert result.evolved_specs[0].metadata["target_node_id"] == "memory"
    assert result.source_refs == ["trace-1"]


def test_evolve_attack_specs_is_deterministic() -> None:
    report = AgentSecurityReport(
        tenant_id="t1",
        agent_id="agent",
        benchmark="local",
        overall_score=60,
        risk_level="high",
        findings=[
            Finding(
                finding_id="f1",
                scenario_id="tool-node",
                severity="high",
                title="tool_tampering: unsafe tool call",
                description="Controlled attack was allowed.",
                business_impact="unsafe action",
                recommendation="Generate stronger tool_tampering variants.",
            )
        ],
        scenario_results=[],
        artifacts=ReportArtifacts(report_path="report.json"),
    )

    first = evolve_attack_specs([_base_spec()], report=report)
    second = evolve_attack_specs([_base_spec()], report=report)

    assert first.model_dump(mode="json") == second.model_dump(mode="json")
