from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from agent_security_sdk.openmanus_real import (
    OpenManusDockerRunner,
    OpenManusDockerRunnerConfig,
    OpenManusSourceRunner,
    OpenManusSourceRunnerConfig,
    _process_output_text,
)


def _docker_output_dir(command: list[str]) -> Path:
    mount = command[command.index("--mount") + 1]
    parts = dict(item.split("=", 1) for item in mount.split(",") if "=" in item)
    return Path(parts["source"])


def test_openmanus_docker_runner_reads_real_runtime_events(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://api.example.test/v1")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-test")

    def fake_run(command, **kwargs):
        del kwargs
        output_dir = _docker_output_dir(command)
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


def test_openmanus_source_runner_uses_isolated_source_and_reads_events(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://api.example.test/v1")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-test")
    source_root = tmp_path / "upstream"
    runtime_root = tmp_path / "runtime"
    (source_root / "app" / "agent").mkdir(parents=True)
    (source_root / "config").mkdir()
    (source_root / "app" / "agent" / "toolcall.py").write_text("# real source marker\n", encoding="utf-8")
    (source_root / "config" / "config.toml").write_text("api_key='do-not-copy'\n", encoding="utf-8")
    runtime_root.mkdir()
    (runtime_root / "real_runner.py").write_text("# runner marker\n", encoding="utf-8")

    captured_env = {}

    def fake_run(command, **kwargs):
        captured_env.update(kwargs["env"])
        output_dir = Path(command[command.index("--output-dir") + 1])
        events = [
            {
                "type": "monitor_decision",
                "tool_name": "python_execute",
                "decision": "deny",
                "risk_score": 80.0,
                "reason": "blocked",
                "rules": ["test.block"],
                "monitor_call_type": "code_execution",
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
    runner = OpenManusSourceRunner(
        OpenManusSourceRunnerConfig(source_root=source_root, runtime_root=runtime_root, output_root=tmp_path / "runs")
    )

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

    isolated_root = Path(payload["runtime_meta"]["isolated_source_root"])
    assert payload["blocked"] is True
    assert payload["runtime_meta"]["runtime_kind"] == "source"
    assert payload["runtime_meta"]["real_runtime"] is True
    assert payload["runtime_meta"]["simulated"] is False
    assert captured_env["OPENMANUS_ROOT"] == str(isolated_root)
    assert captured_env["RED_SENTINEL_LLM_API_KEY"] == "sk-test"
    assert captured_env["OPENAI_API_KEY"] == "redsentinel-runtime-redacted"
    assert not (isolated_root / "config" / "config.toml").exists()
    assert source_root.joinpath("config", "config.toml").read_text(encoding="utf-8") == "api_key='do-not-copy'\n"
    assert payload["audit_events"][0]["decision"] == "deny"


def test_openmanus_docker_runner_requires_real_env(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("OPENAI_BASE_URL", "https://api.example.test/v1")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-test")
    runner = OpenManusDockerRunner(OpenManusDockerRunnerConfig(output_root=tmp_path))

    with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
        runner("user_001", "hello", {"session_id": "sess_1"})


def test_openmanus_docker_runner_cleans_up_container_after_timeout(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://api.example.test/v1")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-test")
    commands: list[list[str]] = []

    def fake_run(command, **kwargs):
        commands.append(command)
        if command[:2] == ["docker", "run"]:
            raise subprocess.TimeoutExpired(command, kwargs["timeout"], output=b"partial stdout", stderr=b"partial stderr")
        return subprocess.CompletedProcess(command, 0, stdout="removed", stderr="")

    monkeypatch.setattr("agent_security_sdk.openmanus_real.subprocess.run", fake_run)
    runner = OpenManusDockerRunner(OpenManusDockerRunnerConfig(output_root=tmp_path, timeout_seconds=1))

    payload = runner(
        "user_001",
        "hello",
        {
            "session_id": "sess_1",
            "turn_index": 0,
            "scenario_id": "timeout-case",
            "case_type": "controlled",
            "defense_mode": "guarded",
            "agent_id": "openmanus_official",
        },
    )

    run_command = commands[0]
    cleanup_command = commands[1]
    container_name = run_command[run_command.index("--name") + 1]
    assert cleanup_command == ["docker", "rm", "-f", container_name]
    assert payload["blocked"] is False
    assert payload["risk_level"] == "high"
    assert payload["audit_events"][0]["event_type"] == "runtime_error"
    assert payload["audit_events"][0]["decision"] == "error"
    assert payload["runtime_meta"]["container_name"] == container_name
    assert "cleanup_error" not in payload["runtime_meta"]


def test_openmanus_timeout_with_partial_policy_block_is_not_reported_as_blocked(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://api.example.test/v1")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-test")
    commands: list[list[str]] = []

    def fake_run(command, **kwargs):
        commands.append(command)
        if command[:2] == ["docker", "run"]:
            output_dir = _docker_output_dir(command)
            output_dir.mkdir(parents=True, exist_ok=True)
            events = [
                {
                    "type": "monitor_decision",
                    "tool_name": "python_execute",
                    "decision": "deny",
                    "risk_score": 80.0,
                    "reason": "blocked before timeout",
                    "rules": ["test.block"],
                    "monitor_call_type": "code_execution",
                },
                {
                    "type": "tool_call_blocked",
                    "tool_name": "python_execute",
                    "tool_call_id": "call_1",
                    "observation": "blocked",
                },
            ]
            with (output_dir / "events.jsonl").open("w", encoding="utf-8") as file:
                for event in events:
                    file.write(json.dumps(event) + "\n")
            raise subprocess.TimeoutExpired(command, kwargs["timeout"], output="partial stdout", stderr="partial stderr")
        return subprocess.CompletedProcess(command, 0, stdout="removed", stderr="")

    monkeypatch.setattr("agent_security_sdk.openmanus_real.subprocess.run", fake_run)
    runner = OpenManusDockerRunner(OpenManusDockerRunnerConfig(output_root=tmp_path, timeout_seconds=1))

    payload = runner(
        "user_001",
        "hello",
        {
            "session_id": "sess_1",
            "turn_index": 1,
            "scenario_id": "timeout-after-deny",
            "case_type": "controlled",
            "defense_mode": "guarded",
            "agent_id": "openmanus_official",
        },
    )

    assert commands[1] == ["docker", "rm", "-f", commands[0][commands[0].index("--name") + 1]]
    assert payload["blocked"] is False
    assert payload["risk_level"] == "high"
    assert [event["decision"] for event in payload["audit_events"]] == ["deny", "error"]
    assert payload["audit_events"][-1]["event_type"] == "runtime_error"


def test_process_output_text_decodes_timeout_bytes() -> None:
    assert _process_output_text(None) == ""
    assert _process_output_text("plain") == "plain"
    assert _process_output_text(b"ok\n") == "ok\n"
    assert "\ufffd" in _process_output_text(b"\xff")
