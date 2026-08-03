from pathlib import Path

from redsentinel.core.agent_security import AgentProfile, AgentProfileNode
from redsentinel.evaluation.engine.feedback import route_optimizer_feedback, write_feedback_artifacts
from redsentinel.evaluation.engine.optimizer import build_optimizer_hub_result
from redsentinel.evaluation.engine.runner import run_closed_loop_evaluation


ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "pyproject.toml").is_file())
SCENARIO_MANIFEST = ROOT / "configs" / "scenarios" / "manifest.yaml"
ACCEPTANCE_MANIFEST = ROOT / "datasets" / "acceptance" / "detectors" / "manifest.yaml"


def test_feedback_router_splits_optimizer_result_into_stable_channels(tmp_path: Path) -> None:
    optimizer_result = _optimizer_result(tmp_path)

    routed = route_optimizer_feedback(optimizer_result)
    replay = route_optimizer_feedback(optimizer_result)

    assert routed.model_dump(mode="json") == replay.model_dump(mode="json")
    assert routed.schema_version == "feedback-route-v0.1"
    assert routed.report.agent_id == "simple-agent"
    assert len(routed.attack.directives) == 3
    assert len(routed.defense.directives) == 3
    assert {item.recommended_actions[0].type for item in routed.attack.directives} == {"generate_attack"}
    assert {item.recommended_actions[0].type for item in routed.defense.directives} == {"tune_defense"}
    assert routed.attack.consumer == "attack_self_evolution"
    assert routed.defense.consumer == "defense_self_optimization"
    assert routed.dashboard.consumer == "security_dashboard"


def test_feedback_router_exposes_frontend_fields_without_dashboard_writes(tmp_path: Path) -> None:
    routed = route_optimizer_feedback(_optimizer_result(tmp_path))

    assert routed.dashboard.overview == {
        "agent_id": "simple-agent",
        "tenant_id": "tenant-c",
        "benchmark": "closed-loop-m3",
        "overall_score": 100,
        "risk_level": "low",
        "attack_success_rate": 0.0,
        "false_positive_rate": 0.0,
    }
    assert len(routed.dashboard.scenario_rows) == 3
    assert len(routed.dashboard.node_attribution_rows) == 3
    assert {
        row["risk_type"] for row in routed.dashboard.node_attribution_rows
    } == {"goal_perturbation", "memory_poisoning", "tool_tampering"}


def test_feedback_router_writes_channel_artifacts(tmp_path: Path) -> None:
    routed = route_optimizer_feedback(_optimizer_result(tmp_path))

    paths = write_feedback_artifacts(routed, tmp_path / "feedback")

    assert Path(paths.route_path).exists()
    assert Path(paths.attack_path).exists()
    assert Path(paths.defense_path).exists()
    assert Path(paths.dashboard_path).exists()
    assert paths.route_path.endswith("feedback-route-v0.1.json")
    assert paths.attack_path.endswith("attack-feedback-v0.1.json")
    assert paths.defense_path.endswith("defense-feedback-v0.1.json")
    assert paths.dashboard_path.endswith("dashboard-feedback-v0.1.json")


def _optimizer_result(tmp_path: Path):
    closed_loop_report = run_closed_loop_evaluation(
        SCENARIO_MANIFEST,
        ACCEPTANCE_MANIFEST,
        repo_root=ROOT,
        results_root=tmp_path / "closed-loop",
    )
    return build_optimizer_hub_result(
        closed_loop_report,
        _agent_profile(),
        tenant_id="tenant-c",
        benchmark="closed-loop-m3",
        report_path="optimizer/agent-security-report-v0.1.json",
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
