from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, validate
from pydantic import ValidationError

from redsentinel.profiling.manifest import load_agent_config
from redsentinel.profiling.builder import build_agent_security_profile
from redsentinel.core.agent_security import AgentManifest, OptimizationAction, OptimizationDirective

REPO_ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "pyproject.toml").is_file())
SCHEMA_ROOT = REPO_ROOT / "schemas"
EXAMPLE_CONFIG = REPO_ROOT / "examples" / "agents" / "simple_agent" / "redsentinel.yaml"


def _schema(name: str) -> dict:
    schema = json.loads((SCHEMA_ROOT / name).read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return schema


def test_agent_manifest_contract_matches_example_config() -> None:
    config = load_agent_config(EXAMPLE_CONFIG)
    payload = config.model_dump(mode="json")

    AgentManifest.model_validate(payload)
    validate(instance=payload, schema=_schema("agent-manifest-v1.schema.json"))


def test_agent_profile_contract_matches_builder_output() -> None:
    config = load_agent_config(EXAMPLE_CONFIG)
    profile = build_agent_security_profile(config)
    payload = profile.model_dump(mode="json")

    assert payload["schema_version"] == "agent-profile-v1"
    validate(instance=payload, schema=_schema("agent-profile-v1.schema.json"))


def test_optimization_directive_contract_accepts_minimal_directive() -> None:
    directive = OptimizationDirective(
        directive_id="directive-simple-agent-input-001",
        agent_name="simple_agent",
        source="evaluation",
        target_node_id="input",
        risk_type="prompt_injection",
        priority="high",
        recommended_actions=[
            OptimizationAction(
                type="add_defense",
                name="input_guard",
                mode="block",
                parameters={"sensitivity": "medium"},
            )
        ],
        rationale="Prompt injection was allowed during controlled evaluation.",
        evidence_refs=["runs/example/trajectory.json#steps/0"],
    )
    payload = directive.model_dump(mode="json")

    validate(instance=payload, schema=_schema("optimization-directive-v1.schema.json"))


def test_optimization_directive_rejects_empty_actions() -> None:
    with pytest.raises(ValidationError):
        OptimizationDirective(
            directive_id="directive-simple-agent-input-001",
            agent_name="simple_agent",
            source="evaluation",
            target_node_id="input",
            risk_type="prompt_injection",
            priority="high",
            recommended_actions=[],
            rationale="Prompt injection was allowed during controlled evaluation.",
        )
