from __future__ import annotations

from pathlib import Path

import yaml

from agent_integration_system.config.schema import AgentConfig


def load_agent_config(path: str | Path) -> AgentConfig:
    config_path = Path(path)
    payload = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    if payload is None:
        payload = {}
    if not isinstance(payload, dict):
        raise ValueError("Agent config must be a YAML mapping.")
    return AgentConfig.model_validate(payload)
