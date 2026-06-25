from __future__ import annotations

from agent_integration_system.config.loader import load_agent_config
from agent_integration_system.profile.builder import build_agent_security_profile
from auto_attack_system.profile_driven import build_profile_driven_attack_plan
from auto_evaluation_system.contracts.agent_security import AgentProfile, AgentProfileNode


def test_profile_driven_attack_plan_targets_profile_risk_surfaces() -> None:
    config = load_agent_config("agent_integration_system/examples/simple_agent/redsentinel.yaml")
    profile = build_agent_security_profile(config)

    plan = build_profile_driven_attack_plan(profile)

    targeted_risks = {spec.risk_type for spec in plan.targeted_specs}
    assert "prompt_injection" in targeted_risks
    assert "knowledge_poisoning" in targeted_risks
    assert "parameter_tampering" in targeted_risks
    assert all(spec.metadata["source"] == "profile" for spec in plan.targeted_specs)


def test_profile_driven_attack_plan_adds_fallback_without_duplicate_exposed_risks() -> None:
    config = load_agent_config("agent_integration_system/examples/simple_agent/redsentinel.yaml")
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
