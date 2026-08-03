from __future__ import annotations

from redsentinel.profiling.manifest import load_agent_config
from redsentinel.profiling.builder import build_agent_security_profile
from redsentinel.profiling import analyze_source_profile
from redsentinel.attacks.engine.attack_agent import AttackAgent
from redsentinel.attacks.engine.llm_client import SharedLLMClient
from redsentinel.attacks.engine.profile_driven import (
    build_profile_driven_attack_plan,
    build_profile_driven_attack_plan_from_candidate,
)
from redsentinel.core.agent_security import AgentProfile, AgentProfileNode, AgentProfileTool


EXAMPLE_CONFIG = "examples/agents/simple_agent/redsentinel.yaml"
EXAMPLE_ROOT = "examples/agents/simple_agent"


def test_profile_driven_attack_plan_targets_profile_risk_surfaces() -> None:
    config = load_agent_config(EXAMPLE_CONFIG)
    profile = build_agent_security_profile(config)

    plan = build_profile_driven_attack_plan(profile)

    targeted_risks = {spec.risk_type for spec in plan.targeted_specs}
    assert "prompt_injection" in targeted_risks
    assert "knowledge_poisoning" in targeted_risks
    assert "parameter_tampering" in targeted_risks
    assert all(spec.metadata["source"] == "profile" for spec in plan.targeted_specs)


def test_profile_driven_attack_plan_adds_fallback_without_duplicate_exposed_risks() -> None:
    config = load_agent_config(EXAMPLE_CONFIG)
    profile = build_agent_security_profile(config)

    plan = build_profile_driven_attack_plan(profile)
    exposed = {spec.risk_type for spec in plan.targeted_specs}

    assert plan.fallback_specs
    assert all(spec.risk_type not in exposed for spec in plan.fallback_specs)
    assert all(spec.metadata["source"] == "fallback" for spec in plan.fallback_specs)


def test_profile_driven_attack_only_targets_exposed_risk_surfaces() -> None:
    profile = AgentProfile(
        agent_name="thin_agent",
        framework="python_function",
        root_path=".",
        entrypoint="app:run",
        business_domain="support",
        nodes=[
            AgentProfileNode(
                id="entry",
                type="input_node",
                target="app:run",
                risk_surfaces=["prompt_injection", "parameter_tampering"],
            )
        ],
    )

    plan = build_profile_driven_attack_plan(profile)

    assert {spec.risk_type for spec in plan.targeted_specs} == {"prompt_injection", "parameter_tampering"}


def test_profile_driven_attack_fallback_covers_seven_baseline_risks() -> None:
    profile = AgentProfile(
        agent_name="unknown_agent",
        framework="python_function",
        root_path=".",
        entrypoint="app:run",
        business_domain="support",
        nodes=[AgentProfileNode(id="entry", type="input_node", target="app:run", risk_surfaces=[])],
    )

    plan = build_profile_driven_attack_plan(profile)

    assert {spec.risk_type for spec in plan.fallback_specs} == {
        "prompt_injection",
        "knowledge_poisoning",
        "unauthorized_retrieval",
        "tool_tampering",
        "memory_poisoning",
        "goal_drift",
        "pii_leakage",
    }


def test_profile_driven_attack_accepts_m15_standardized_candidate_profile() -> None:
    config = load_agent_config(EXAMPLE_CONFIG)
    base_profile = build_agent_security_profile(config)
    candidate = analyze_source_profile(EXAMPLE_ROOT, base_profile)

    plan = build_profile_driven_attack_plan_from_candidate(candidate)

    run_agent_specs = [spec for spec in plan.targeted_specs if spec.metadata["node_id"] == "run_agent"]
    assert {spec.risk_type for spec in run_agent_specs} == {"goal_drift", "instruction_hijacking"}
    assert all(spec.metadata["profile_source"] == candidate.source for spec in plan.specs)
    assert all(spec.metadata["profile_confidence"] == candidate.confidence for spec in plan.specs)


def test_attack_agent_runs_m15_profile_aware_attacks() -> None:
    config = load_agent_config(EXAMPLE_CONFIG)
    base_profile = build_agent_security_profile(config)
    candidate = analyze_source_profile(EXAMPLE_ROOT, base_profile)

    result = AttackAgent.from_profile_candidate(
        candidate,
        llm=SharedLLMClient(force_offline=True),
    ).run()

    run_agent_attempts = [attempt for attempt in result.attempts if attempt.target_node_id == "run_agent"]
    assert {attempt.category for attempt in run_agent_attempts} == {"goal_drift", "instruction_hijacking"}
    assert all(attempt.profile_source == candidate.source for attempt in result.attempts)
    assert all("node=run_agent" in attempt.payload for attempt in run_agent_attempts)


def test_attack_agent_changes_output_for_different_profiles() -> None:
    input_profile = AgentProfile(
        agent_name="input_only_agent",
        framework="python_function",
        root_path=".",
        entrypoint="app:run",
        business_domain="support",
        nodes=[
            AgentProfileNode(
                id="entry",
                type="input_node",
                target="app:run",
                risk_surfaces=["prompt_injection"],
            )
        ],
        sensitive_data=["email"],
    )
    tool_profile = AgentProfile(
        agent_name="tool_agent",
        framework="python_function",
        root_path=".",
        entrypoint="app:run",
        business_domain="ecommerce",
        nodes=[
            AgentProfileNode(
                id="checkout_tool",
                type="tool_node",
                target="app:checkout",
                risk_surfaces=["tool_abuse", "parameter_tampering"],
            )
        ],
        tools=[AgentProfileTool(name="refund_order", risk_level="high", side_effect=True)],
        sensitive_data=["payment_token"],
    )

    input_result = AttackAgent.from_agent_profile(input_profile, llm=SharedLLMClient(force_offline=True)).run()
    tool_result = AttackAgent.from_agent_profile(tool_profile, llm=SharedLLMClient(force_offline=True)).run()
    input_targeted = {attempt.category for attempt in input_result.attempts if attempt.attack_source == "profile"}
    tool_targeted = {attempt.category for attempt in tool_result.attempts if attempt.attack_source == "profile"}

    assert input_targeted == {"prompt_injection"}
    assert tool_targeted == {"tool_abuse", "parameter_tampering"}
    assert "memory_poisoning" not in tool_targeted
    assert any("refund_order" in attempt.payload for attempt in tool_result.attempts)
    assert all("refund_order" not in attempt.payload for attempt in input_result.attempts)
