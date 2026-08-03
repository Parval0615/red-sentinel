from pathlib import Path

from redsentinel.core.agent_security import AgentProfile, AgentProfileNode
from redsentinel.evaluation.engine.optimizer import build_optimizer_hub_result, write_optimizer_artifacts
from redsentinel.evaluation.engine.optimizer.ledger import load_ledger_entries, verify_ledger_entries
from redsentinel.evaluation.engine.runner import run_closed_loop_evaluation


ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "pyproject.toml").is_file())
SCENARIO_MANIFEST = ROOT / "configs" / "scenarios" / "manifest.yaml"
ACCEPTANCE_MANIFEST = ROOT / "datasets" / "acceptance" / "detectors" / "manifest.yaml"


def test_optimizer_hub_builds_report_and_dual_directives_deterministically(tmp_path: Path) -> None:
    closed_loop_report = _closed_loop_report(tmp_path)

    result = build_optimizer_hub_result(
        closed_loop_report,
        _agent_profile(),
        tenant_id="tenant-c",
        benchmark="closed-loop-m3",
        report_path="optimizer/agent-security-report-v0.1.json",
    )
    replay = build_optimizer_hub_result(
        closed_loop_report,
        _agent_profile(),
        tenant_id="tenant-c",
        benchmark="closed-loop-m3",
        report_path="optimizer/agent-security-report-v0.1.json",
    )

    assert result.agent_security_report.model_dump(mode="json") == replay.agent_security_report.model_dump(mode="json")
    assert [item.model_dump(mode="json") for item in result.directives] == [
        item.model_dump(mode="json") for item in replay.directives
    ]
    assert result.agent_security_report.schema_version == "agent-security-report-v0.1"
    assert result.agent_security_report.agent_id == "simple-agent"
    assert result.agent_security_report.overall_score == 100
    assert result.agent_security_report.attack_success_rate == 0.0
    assert result.agent_security_report.false_positive_rate == 0.0
    assert result.agent_security_report.findings == []
    assert len(result.agent_security_report.scenario_results) == 3
    assert len(result.attack_directives) == 3
    assert len(result.defense_directives) == 3
    assert {item.recommended_actions[0].type for item in result.attack_directives} == {"generate_attack"}
    assert {item.recommended_actions[0].type for item in result.defense_directives} == {"tune_defense"}
    assert {item.target_node_id for item in result.defense_directives} == {
        "input-gateway",
        "memory-store",
        "tool-executor",
    }
    assert all(item.source == "evaluation" for item in result.directives)


def test_optimizer_hub_preserves_node_attribution_and_evidence_refs(tmp_path: Path) -> None:
    result = build_optimizer_hub_result(
        _closed_loop_report(tmp_path),
        _agent_profile(),
        tenant_id="tenant-c",
        benchmark="closed-loop-m3",
        report_path="optimizer/agent-security-report-v0.1.json",
    )

    memory_attribution = next(item for item in result.node_attributions if item.risk_type == "memory_poisoning")
    memory_directive = next(item for item in result.defense_directives if item.risk_type == "memory_poisoning")

    assert memory_attribution.node_id == "memory-store"
    assert memory_attribution.node_type == "memory_node"
    assert memory_attribution.evidence_refs[0].startswith("detector:MIS:p2-memory-poison-direct-api")
    assert memory_attribution.evidence_refs[0] in memory_directive.evidence_refs
    assert memory_directive.target_node_id == memory_attribution.node_id
    assert result.agent_security_report.summary["node_attribution"][0]["node_id"]
    assert {
        item["risk_type"] for item in result.agent_security_report.summary["node_attribution"]
    } == {"goal_perturbation", "memory_poisoning", "tool_tampering"}


def test_optimizer_hub_writes_artifacts_and_append_only_ledger(tmp_path: Path) -> None:
    result = build_optimizer_hub_result(
        _closed_loop_report(tmp_path),
        _agent_profile(),
        tenant_id="tenant-c",
        benchmark="closed-loop-m3",
        report_path="optimizer/agent-security-report-v0.1.json",
    )

    paths = write_optimizer_artifacts(result, tmp_path / "optimizer")
    ledger_entries = load_ledger_entries(paths.ledger_path)
    verification = verify_ledger_entries(ledger_entries)

    assert Path(paths.report_path).exists()
    assert Path(paths.attack_directives_path).exists()
    assert Path(paths.defense_directives_path).exists()
    assert Path(paths.ledger_path).exists()
    assert len(ledger_entries) == 1 + len(result.directives)
    assert ledger_entries[0].artifact_type == "agent_security_report"
    assert {item.artifact_id for item in ledger_entries[1:]} == {item.directive_id for item in result.directives}
    assert verification.valid is True

    write_optimizer_artifacts(result, tmp_path / "optimizer")
    appended_entries = load_ledger_entries(paths.ledger_path)

    assert len(appended_entries) == len(ledger_entries) * 2
    assert appended_entries[len(ledger_entries)].previous_hash == ledger_entries[-1].entry_hash
    assert verify_ledger_entries(appended_entries).valid is True


def _closed_loop_report(tmp_path: Path):
    return run_closed_loop_evaluation(
        SCENARIO_MANIFEST,
        ACCEPTANCE_MANIFEST,
        repo_root=ROOT,
        results_root=tmp_path / "closed-loop",
    )


def _agent_profile() -> AgentProfile:
    return AgentProfile(
        agent_name="simple-agent",
        framework="python_function",
        root_path="examples/agents/simple_agent",
        entrypoint="app:handle",
        business_domain="ecommerce",
        nodes=[
            AgentProfileNode(
                id="input-gateway",
                type="input_node",
                target="app:handle",
                risk_surfaces=["goal_perturbation"],
            ),
            AgentProfileNode(
                id="memory-store",
                type="memory_node",
                target="memory:store",
                risk_surfaces=["memory_poisoning"],
            ),
            AgentProfileNode(
                id="tool-executor",
                type="tool_node",
                target="tools:execute",
                risk_surfaces=["tool_tampering"],
            ),
        ],
        attack_entries=["prompt"],
        sensitive_data=["customer_email"],
        rag_enabled=False,
    )
