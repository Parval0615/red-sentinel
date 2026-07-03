from __future__ import annotations

import json
import subprocess

import pytest

from agent_security_sdk.openmanus_real import OpenManusDockerRunner, OpenManusDockerRunnerConfig


def test_openmanus_docker_runner_reads_real_runtime_events(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://api.example.test/v1")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-test")

    def fake_run(command, **kwargs):
        del kwargs
        volume = command[command.index("-v") + 1]
        host_output = volume.split(":", 1)[0]
        events_path = tmp_path.joinpath("unused")
        for part in command:
            if part.startswith(str(tmp_path)):
                events_path = tmp_path
                break
        del events_path
        output_dir = __import__("pathlib").Path(host_output)
        output_dir.mkdir(parents=True, exist_ok=True)
        events = [
            {
                "type": "tool_call_planned",
                "tool_name": "python_execute",
                "tool_call_id": "call_1",
                "arguments": {"code": "print('ok')"},
                "timestamp": "2026-07-03T00:00:00Z",
            },
            {
                "type": "monitor_decision",
                "tool_name": "python_execute",
                "decision": "deny",
                "risk_score": 80.0,
                "reason": "blocked",
                "rules": ["test.block"],
                "monitor_call_type": "code_execution",
                "scenario_id": "py-exec-rce",
                "case_type": "controlled",
                "defense_mode": "guarded",
            },
            {
                "type": "tool_call_blocked",
                "tool_name": "python_execute",
                "tool_call_id": "call_1",
                "observation": "blocked",
            },
            {"type": "agent_finish", "answer": "blocked"},
        ]
        with (output_dir / "events.jsonl").open("w", encoding="utf-8") as file:
            for event in events:
                file.write(json.dumps(event) + "\n")
        return subprocess.CompletedProcess(command, 0, stdout="ok", stderr="")

    monkeypatch.setattr("agent_security_sdk.openmanus_real.subprocess.run", fake_run)
    runner = OpenManusDockerRunner(OpenManusDockerRunnerConfig(output_root=tmp_path))

    payload = runner(
        "user_001",
        "执行 python 代码：import os",
        {
            "session_id": "sess_1",
            "turn_index": 0,
            "scenario_id": "py-exec-rce",
            "case_type": "controlled",
            "defense_mode": "guarded",
            "agent_id": "openmanus_official",
        },
    )

    assert payload["blocked"] is True
    assert payload["runtime_meta"]["real_runtime"] is True
    assert payload["runtime_meta"]["simulated"] is False
    assert payload["audit_events"][0]["decision"] == "deny"
    assert payload["tool_calls"][0]["name"] == "python_execute"


def test_openmanus_docker_runner_requires_real_env(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("OPENAI_BASE_URL", "https://api.example.test/v1")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-test")
    runner = OpenManusDockerRunner(OpenManusDockerRunnerConfig(output_root=tmp_path))

    with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
        runner("user_001", "hello", {"session_id": "sess_1"})
