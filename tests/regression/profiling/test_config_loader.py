from __future__ import annotations

from pathlib import Path

from redsentinel.profiling.manifest import load_agent_config


EXAMPLE_CONFIG = next(parent for parent in Path(__file__).resolve().parents if (parent / "pyproject.toml").is_file()) / "examples" / "agents" / "simple_agent" / "redsentinel.yaml"


def test_load_example_config() -> None:
    config = load_agent_config(EXAMPLE_CONFIG)

    assert config.agent.name == "simple_agent"
    assert config.agent.framework == "python_function"
    assert len(config.nodes) == 4
    assert config.evaluation.attack_entries == ["prompt", "rag_text"]
