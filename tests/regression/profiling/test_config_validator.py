from __future__ import annotations

from pathlib import Path

import pytest

from redsentinel.profiling.manifest import load_agent_config
from redsentinel.core.agent_security import AgentManifest as AgentConfig
from redsentinel.profiling.validation import ConfigValidationError, validate_agent_config


EXAMPLE_CONFIG = next(parent for parent in Path(__file__).resolve().parents if (parent / "pyproject.toml").is_file()) / "examples" / "agents" / "simple_agent" / "redsentinel.yaml"


def test_validate_example_config() -> None:
    config = load_agent_config(EXAMPLE_CONFIG)

    validate_agent_config(config, config_path=EXAMPLE_CONFIG)


def test_reject_duplicate_node_id() -> None:
    config = load_agent_config(EXAMPLE_CONFIG)
    payload = config.model_dump(mode="json")
    payload["nodes"].append(dict(payload["nodes"][0]))
    invalid_config = AgentConfig.model_validate(payload)

    with pytest.raises(ConfigValidationError, match="duplicate node id"):
        validate_agent_config(invalid_config, config_path=EXAMPLE_CONFIG)


def test_reject_incompatible_defense() -> None:
    config = load_agent_config(EXAMPLE_CONFIG)
    payload = config.model_dump(mode="json")
    payload["nodes"][0]["defenses"] = ["tool_guard"]
    invalid_config = AgentConfig.model_validate(payload)

    with pytest.raises(ConfigValidationError, match="not compatible"):
        validate_agent_config(invalid_config, config_path=EXAMPLE_CONFIG)


def test_reject_missing_rag_source_when_enabled() -> None:
    config = load_agent_config(EXAMPLE_CONFIG)
    payload = config.model_dump(mode="json")
    payload["rag"]["document_paths"] = []
    invalid_config = AgentConfig.model_validate(payload)

    with pytest.raises(ConfigValidationError, match="rag.enabled requires"):
        validate_agent_config(invalid_config, config_path=EXAMPLE_CONFIG)


def test_reject_missing_callable() -> None:
    config = load_agent_config(EXAMPLE_CONFIG)
    payload = config.model_dump(mode="json")
    payload["nodes"][0]["target"] = "app:missing_callable"
    invalid_config = AgentConfig.model_validate(payload)

    with pytest.raises(ConfigValidationError, match="callable not found"):
        validate_agent_config(invalid_config, config_path=EXAMPLE_CONFIG)
