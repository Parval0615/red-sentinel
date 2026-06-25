from __future__ import annotations

from agent_integration_system.config.loader import load_agent_config
from agent_integration_system.profile.builder import build_agent_security_profile
from auto_attack_system.profile_driven import build_profile_driven_attack_plan


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
