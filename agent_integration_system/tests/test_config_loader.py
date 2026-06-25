from __future__ import annotations

from pathlib import Path

from agent_integration_system.config.loader import load_agent_config


EXAMPLE_CONFIG = Path(__file__).resolve().parents[1] / "examples" / "simple_agent" / "redsentinel.yaml"


def test_load_example_config() -> None:
    config = load_agent_config(EXAMPLE_CONFIG)

    assert config.agent.name == "simple_agent"
    assert config.agent.framework == "python_function"
    assert len(config.nodes) == 4
    assert config.evaluation.attack_entries == ["prompt", "rag_text"]
