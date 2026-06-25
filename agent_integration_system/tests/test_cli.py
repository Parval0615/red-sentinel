from __future__ import annotations

import json
from pathlib import Path

from agent_integration_system.cli import main


EXAMPLE_CONFIG = Path(__file__).resolve().parents[1] / "examples" / "simple_agent" / "redsentinel.yaml"


def test_cli_validate(capsys) -> None:
    exit_code = main(["validate", str(EXAMPLE_CONFIG)])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "CONFIG_VALID=true" in output
    assert "NODES=4" in output


def test_cli_profile(tmp_path: Path, capsys) -> None:
    output_path = tmp_path / "agent-profile.json"

    exit_code = main(["profile", str(EXAMPLE_CONFIG), "--output", str(output_path)])

    output = capsys.readouterr().out
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert exit_code == 0
    assert "PROFILE_PATH=" in output
    assert payload["schema_version"] == "agent-profile-v1"
    assert payload["agent_name"] == "simple_agent"
