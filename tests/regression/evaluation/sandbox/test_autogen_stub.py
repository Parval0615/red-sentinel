import json
from pathlib import Path
from typing import Any

import pytest
import yaml
from pydantic import ValidationError

from redsentinel.runtime.engine.sandbox.backends.autogen import AutoGenBackend
from redsentinel.runtime.engine.sandbox.config import ScenarioConfig
from redsentinel.runtime.engine.sandbox.run import get_backend
from redsentinel.runtime.engine.sandbox.session import SandboxEnvironment


ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "pyproject.toml").is_file())


def _framework_values(value: Any) -> list[str]:
    if isinstance(value, dict):
        values: list[str] = []
        for key, child in value.items():
            if key == "framework" and isinstance(child, str):
                values.append(child)
            values.extend(_framework_values(child))
        return values
    if isinstance(value, list):
        return [framework for child in value for framework in _framework_values(child)]
    return []


def test_autogen_backend_is_scaffold_only() -> None:
    config = ScenarioConfig.from_yaml(
        ROOT / "configs" / "scenarios" / "p1-sandbox-5step-direct-api.yaml"
    )
    session = SandboxEnvironment().create_session(config)
    backend = AutoGenBackend()

    assert backend.framework == "autogen"
    with pytest.raises(NotImplementedError, match="scaffold"):
        backend.run(session)


def test_autogen_scaffold_is_not_public_scenario_framework() -> None:
    with pytest.raises(ValidationError) as exc_info:
        ScenarioConfig.model_validate(
            {
                "experiment_id": "p1-sandbox-autogen",
                "agent": {
                    "framework": "autogen",
                    "goal": "Run an AutoGen agent.",
                    "system_prompt": "You are a test agent.",
                },
            }
        )

    assert "autogen" in str(exc_info.value)


def test_autogen_scaffold_is_not_dispatched_as_runnable_backend() -> None:
    with pytest.raises(ValueError, match="scaffold-only"):
        get_backend("autogen")


def test_public_scenario_templates_do_not_select_autogen_framework() -> None:
    scenario_dir = ROOT / "configs" / "scenarios"

    framework_values = []
    for path in scenario_dir.rglob("*.yaml"):
        framework_values.extend(
            _framework_values(yaml.safe_load(path.read_text(encoding="utf-8")))
        )

    assert "autogen" not in framework_values


def test_public_trajectory_schema_does_not_advertise_autogen_framework() -> None:
    schema = json.loads(
        (ROOT / "schemas" / "trajectory-v1.schema.json").read_text(encoding="utf-8")
    )

    assert "autogen" not in schema["properties"]["framework"]["enum"]
