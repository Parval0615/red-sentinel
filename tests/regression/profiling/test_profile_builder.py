from __future__ import annotations

from pathlib import Path

from redsentinel.profiling.manifest import load_agent_config
from redsentinel.profiling.builder import build_agent_security_profile


EXAMPLE_CONFIG = next(parent for parent in Path(__file__).resolve().parents if (parent / "pyproject.toml").is_file()) / "examples" / "agents" / "simple_agent" / "redsentinel.yaml"


def test_build_agent_security_profile() -> None:
    config = load_agent_config(EXAMPLE_CONFIG)
    profile = build_agent_security_profile(config)

    assert profile.schema_version == "agent-profile-v1"
    assert profile.agent_name == "simple_agent"
    assert profile.framework == "python_function"
    assert profile.attack_entries == ["prompt", "rag_text"]
    assert profile.sensitive_data == ["phone", "address", "payment_token", "system_prompt"]
    assert len(profile.nodes) == 4


def test_profile_infers_risk_surfaces_from_node_types() -> None:
    config = load_agent_config(EXAMPLE_CONFIG)
    profile = build_agent_security_profile(config)
    risks_by_node = {node.id: node.risk_surfaces for node in profile.nodes}

    assert risks_by_node["input"] == ["prompt_injection", "jailbreak"]
    assert risks_by_node["rag"] == [
        "indirect_prompt_injection",
        "knowledge_poisoning",
        "unauthorized_retrieval",
    ]
    assert risks_by_node["tool_executor"] == ["tool_abuse", "privilege_escalation", "parameter_tampering"]
    assert risks_by_node["output"] == ["pii_leakage", "unsafe_output"]
