from __future__ import annotations

from redsentinel.attacks.engine.attack_spec import AttackSpec
from redsentinel.attacks.engine.evolution import evolve_attack_specs
from redsentinel.core.agent_security import OptimizationAction, OptimizationDirective
from redsentinel.application.contracts import (
    AgentSecurityReport,
    Finding,
    ReportArtifacts,
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

    result = evolve_attack_specs([_base_spec()], report=report, round_index=2, based_on="round_1_report.json", seed=7)

    assert len(result.evolved_specs) == 1
    assert result.evolved_specs[0].risk_type == "tool_tampering"
    assert result.evolved_specs[0].intensity == "heavy"
    assert result.evolved_specs[0].metadata["source"] == "self_evolution"
    assert result.evolved_specs[0].metadata["trigger_reason"] == "Finding f1 remained unresolved."
    assert result.evolution_records[0]["round"] == 2
    assert result.evolution_records[0]["based_on"] == "round_1_report.json"
    assert result.evolution_records[0]["seed"] == 7
    assert result.evolution_records[0]["weakness"] == "defense_bypass"
    assert result.evolution_records[0]["previous_attack_id"] == "agent:tool:tool_tampering:baseline"
    assert result.evolution_records[0]["mutation_strategy"] == "exploit_hardening_chain_hijack_s7_i1"
    assert result.evolution_records[0]["diff_from_previous"]["strategy"]["from"] == "baseline_probe"
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


def test_evolve_attack_specs_changes_strategy_for_different_sources() -> None:
    directive = OptimizationDirective(
        directive_id="dir-1",
        agent_name="agent",
        source="evaluation",
        target_node_id="memory",
        risk_type="memory_poisoning",
        priority="medium",
        recommended_actions=[OptimizationAction(type="generate_attack", name="memory_variant")],
        rationale="Memory poisoning missing.",
        evidence_refs=["trace-1"],
    )

    from_directive = evolve_attack_specs([_base_spec()], directives=[directive], seed=3)
    from_failed_attempt = evolve_attack_specs(
        [_base_spec()],
        failed_attempts=[{"risk_type": "memory_poisoning", "node_id": "memory", "attempt_id": "attempt-1"}],
        seed=3,
    )

    assert from_directive.evolution_records[0]["weakness"] == "optimizer_directive"
    assert from_failed_attempt.evolution_records[0]["weakness"] == "failed_attack_attempt"
    assert from_directive.evolution_records[0]["mutation_strategy"] != from_failed_attempt.evolution_records[0]["mutation_strategy"]
