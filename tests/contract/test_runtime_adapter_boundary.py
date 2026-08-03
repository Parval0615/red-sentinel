from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import validate

from redsentinel.adapters.engine.adapter import AgentAdapter
from redsentinel.adapters.engine.openmanus import OpenManusAdapter as LegacyOpenManusAdapter
from redsentinel.application.engine.hosted_adapter import HostedAPIAdapter
from redsentinel.runtime.engine.sandbox.backends.direct_api import DirectAPIBackend as LegacyDirectAPIBackend
from redsentinel.runtime.engine.sandbox.backends.docker import DockerBackend as LegacyDockerBackend
from redsentinel.runtime.engine.sandbox.backends.langgraph import LangGraphBackend as LegacyLangGraphBackend
from redsentinel.adapters import (
    HTTPAdapter,
    RUNNABLE_ADAPTERS,
    SCAFFOLD_ADAPTERS,
    DirectAPIBackend,
    DockerBackend,
    LangGraphBackend,
    OpenManusAdapter,
    SDKAdapter,
    adapter_class,
)
from redsentinel.runtime import SandboxEnvironment, ScenarioConfig, TrajectoryRecorder, run_scenario

ROOT = Path(__file__).resolve().parents[2]
EVALUATION_ROOT = ROOT
TRAJECTORY_SCHEMA = json.loads(
    (EVALUATION_ROOT / "schemas" / "trajectory-v1.schema.json").read_text(encoding="utf-8")
)


def test_public_adapter_boundary_reuses_legacy_implementations() -> None:
    assert DirectAPIBackend is LegacyDirectAPIBackend
    assert LangGraphBackend is LegacyLangGraphBackend
    assert DockerBackend is LegacyDockerBackend
    assert OpenManusAdapter is LegacyOpenManusAdapter
    assert HTTPAdapter is HostedAPIAdapter
    assert SDKAdapter is AgentAdapter


def test_autogen_is_scaffold_only_and_not_runnable() -> None:
    assert "autogen" not in RUNNABLE_ADAPTERS
    assert SCAFFOLD_ADAPTERS == ("autogen",)
    with pytest.raises(ValueError, match="scaffold-only"):
        adapter_class("autogen")


@pytest.mark.parametrize(
    ("adapter_name", "scenario_name"),
    [
        ("direct_api", "p1-sandbox-5step-direct-api.yaml"),
        ("langgraph", "p1-sandbox-5step-langgraph.yaml"),
    ],
)
def test_public_replay_adapters_emit_schema_valid_trajectories(
    adapter_name: str,
    scenario_name: str,
) -> None:
    assert adapter_class(adapter_name) in {DirectAPIBackend, LangGraphBackend}
    trajectory = run_scenario(str(EVALUATION_ROOT / "configs" / "scenarios" / scenario_name))
    validate(instance=trajectory, schema=TRAJECTORY_SCHEMA)
    assert trajectory["framework"] == adapter_name
    assert [step["step_type"] for step in trajectory["steps"]] == [
        "llm_inference",
        "tool_call",
        "llm_inference",
        "tool_call",
        "llm_inference",
    ]


def test_public_docker_adapter_events_record_a_schema_valid_fixture_trajectory() -> None:
    config = ScenarioConfig.model_validate(
        {
            "experiment_id": "docker-public-boundary",
            "agent": {
                "framework": "docker",
                "goal": "Run fixture",
                "system_prompt": "Fixture",
                "framework_config": {"docker_image": "fixture-only"},
            },
            "runner": {"max_steps": 2},
        }
    )
    session = SandboxEnvironment().create_session(config)
    backend = DockerBackend()
    events = backend._parse_output_to_events(
        "\n".join(
            [
                '{"type":"llm_inference","model":"fixture","output_content":"plan"}',
                '{"type":"tool_call","call_id":"call-1","tool_name":"fixture_tool","arguments":{}}',
            ]
        ),
        "",
    )
    for event in events:
        session.emitter.emit(event)

    trajectory = TrajectoryRecorder.from_session(session)
    validate(instance=trajectory, schema=TRAJECTORY_SCHEMA)
    assert trajectory["framework"] == "docker"
    assert [step["step_type"] for step in trajectory["steps"]] == ["llm_inference", "tool_call"]


def test_public_openmanus_adapter_preserves_fixture_trajectory_contract() -> None:
    adapter = OpenManusAdapter(session_id="public-openmanus")
    result = adapter.send_message("researcher", "search public security guidance", {"role": "analyst"})
    trajectory = adapter.export_trajectory()

    assert trajectory["session_id"] == "public-openmanus"
    assert trajectory["agent_framework"] == "OpenManus"
    assert trajectory["tool_calls"] == result.tool_calls
    assert trajectory["audit_events"] == result.audit_events
    assert trajectory["turns"]
