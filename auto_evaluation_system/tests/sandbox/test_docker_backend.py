from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

from auto_attack_system.ingestion.deep import DockerTracePlan
from auto_evaluation_system.sandbox.backends.docker import DockerBackend
from auto_evaluation_system.sandbox.docker.capture import BoundedCaptureResult, run_bounded_capture
from auto_evaluation_system.sandbox.docker.executor import DockerTraceExecutor
from auto_evaluation_system.sandbox.run import get_backend, run_scenario


def _session_with_docker_image() -> MagicMock:
    session = MagicMock()
    session.config.agent.framework_config = {"docker_image": "test-image"}
    session.config.agent.system_prompt = "system prompt"
    session.config.agent.goal = "user goal"
    session.config.runner.timeout_seconds = 300
    return session


def _docker_plan(node_targets: list[str] | None = None) -> DockerTracePlan:
    return DockerTracePlan(
        agent_name="docker-agent",
        docker_image="local/redsentinel-agent:test",
        adapter_entrypoint="adapter:invoke",
        node_targets=node_targets or [],
    )


def _capture_result(
    tmp_path: Path,
    *,
    stdout: str,
    stderr: str,
    stdout_truncated: bool = False,
    stderr_truncated: bool = False,
    timed_out: bool = False,
    error: str | None = None,
) -> BoundedCaptureResult:
    stdout_path = tmp_path / "stdout.log"
    stderr_path = tmp_path / "stderr.log"
    stdout_path.write_text(stdout, encoding="utf-8")
    stderr_path.write_text(stderr, encoding="utf-8")
    return BoundedCaptureResult(
        args=["docker", "run", "--rm", "test-image"],
        returncode=-9 if timed_out else 0,
        stdout_path=stdout_path,
        stderr_path=stderr_path,
        stdout_truncated=stdout_truncated,
        stderr_truncated=stderr_truncated,
        timed_out=timed_out,
        error=error,
    )


def _audit_complete_entry(audit_path: str) -> dict:
    entries = [json.loads(line) for line in Path(audit_path).read_text(encoding="utf-8").splitlines()]
    return entries[-1]


def test_docker_backend_framework_name() -> None:
    backend = DockerBackend()
    assert backend.framework == "docker"


def test_get_backend_dispatches_docker_backend() -> None:
    backend = get_backend("docker")
    assert isinstance(backend, DockerBackend)


def test_docker_backend_parse_llm_inference_event() -> None:
    backend = DockerBackend()
    stdout = '{"type": "llm_inference", "model": "gpt-4", "input_messages": [{"role": "user", "content": "test"}], "output_content": "response", "turn_index": 1}'
    stderr = ""

    events = backend._parse_output_to_events(stdout, stderr)

    assert len(events) == 1
    assert events[0].step_type.value == "llm_inference"
    assert events[0].llm.model == "gpt-4"
    assert events[0].llm.output_content == "response"


def test_docker_backend_parse_tool_call_event() -> None:
    backend = DockerBackend()
    stdout = '{"type": "tool_call", "call_id": "call_123", "tool_name": "lookup_order", "arguments": {"order_id": "ORD-001"}, "response": {"status": "shipped"}, "parent_turn_index": 1}'
    stderr = ""

    events = backend._parse_output_to_events(stdout, stderr)

    assert len(events) == 1
    assert events[0].step_type.value == "tool_call"
    assert events[0].tool_call.name == "lookup_order"
    assert events[0].tool_call.call_id == "call_123"


def test_docker_backend_skip_invalid_json() -> None:
    backend = DockerBackend()
    stdout = "not valid json\n{\"type\": \"llm_inference\", \"model\": \"test\"}"
    stderr = ""

    events = backend._parse_output_to_events(stdout, stderr)

    assert len(events) == 1


def test_docker_backend_skip_unknown_event_type() -> None:
    backend = DockerBackend()
    stdout = '{"type": "unknown_event", "data": "value"}'
    stderr = ""

    events = backend._parse_output_to_events(stdout, stderr)

    assert len(events) == 0


def test_docker_backend_empty_output() -> None:
    backend = DockerBackend()
    stdout = ""
    stderr = ""

    events = backend._parse_output_to_events(stdout, stderr)

    assert len(events) == 0


def test_docker_backend_multiple_events() -> None:
    backend = DockerBackend()
    stdout = '{"type": "llm_inference", "model": "test", "turn_index": 0}\n{"type": "tool_call", "tool_name": "test_tool", "call_id": "1"}'
    stderr = ""

    events = backend._parse_output_to_events(stdout, stderr)

    assert len(events) == 2


def test_docker_backend_run_without_image() -> None:
    backend = DockerBackend()
    session = MagicMock()
    session.config.agent.framework_config = {}

    events = backend.run(session)

    assert len(events) == 0


def test_docker_backend_run_parses_small_bounded_capture_output(tmp_path: Path) -> None:
    backend = DockerBackend()
    session = _session_with_docker_image()
    result = _capture_result(
        tmp_path,
        stdout='{"type": "llm_inference", "model": "gpt-4", "turn_index": 0}\n',
        stderr="",
    )

    with patch("auto_evaluation_system.sandbox.backends.docker.run_bounded_capture", return_value=result):
        events = backend.run(session)

    assert len(events) == 1
    assert events[0].step_type.value == "llm_inference"
    assert backend.last_error is None


def test_docker_run_scenario_records_emitted_events(tmp_path: Path) -> None:
    scenario = tmp_path / "docker-scenario.yaml"
    scenario.write_text(
        """
experiment_id: p1-sandbox-docker
agent:
  framework: docker
  goal: Run the dockerized agent.
  system_prompt: Emit RedSentinel JSONL events.
  framework_config:
    docker_image: test-image
""".strip(),
        encoding="utf-8",
    )
    result = _capture_result(
        tmp_path,
        stdout='{"type": "llm_inference", "model": "gpt-4", "turn_index": 0}\n',
        stderr="",
    )

    with patch("auto_evaluation_system.sandbox.backends.docker.run_bounded_capture", return_value=result):
        trajectory = run_scenario(str(scenario))

    assert trajectory["framework"] == "docker"
    assert len(trajectory["steps"]) == 1
    assert trajectory["steps"][0]["step_type"] == "llm_inference"


def test_docker_backend_run_with_timeout(tmp_path: Path) -> None:
    backend = DockerBackend()
    session = _session_with_docker_image()
    result = _capture_result(
        tmp_path,
        stdout="",
        stderr="",
        timed_out=True,
        error="process timed out after 300 seconds",
    )

    with patch("auto_evaluation_system.sandbox.backends.docker.run_bounded_capture", return_value=result):
        events = backend.run(session)

    assert len(events) == 0
    assert backend.last_error == "process timed out after 300 seconds"


def test_docker_backend_run_with_output_limit(tmp_path: Path) -> None:
    backend = DockerBackend(max_output_bytes=10)
    session = _session_with_docker_image()
    result = _capture_result(
        tmp_path,
        stdout="x" * 10,
        stderr="",
        stdout_truncated=True,
        error="stdout exceeded 10 bytes",
    )

    with patch("auto_evaluation_system.sandbox.backends.docker.run_bounded_capture", return_value=result):
        events = backend.run(session)

    assert len(events) == 0
    assert backend.last_error == "stdout exceeded 10 bytes"


def test_bounded_capture_preserves_small_jsonl_output(tmp_path: Path) -> None:
    result = run_bounded_capture(
        [
            sys.executable,
            "-c",
            "import sys; print('{\"type\":\"llm_inference\",\"model\":\"gpt-4\"}'); print('warn', file=sys.stderr)",
        ],
        timeout=5,
        max_output_bytes=1024,
        stdout_path=tmp_path / "stdout.log",
        stderr_path=tmp_path / "stderr.log",
    )

    assert result.returncode == 0
    assert result.error is None
    assert json.loads(result.stdout_text())["type"] == "llm_inference"
    assert result.stderr_text() == "warn\n"


def test_bounded_capture_marks_output_limit(tmp_path: Path) -> None:
    result = run_bounded_capture(
        [
            sys.executable,
            "-c",
            "import sys; sys.stdout.write('x' * 20); sys.stderr.write('y' * 20)",
        ],
        timeout=5,
        max_output_bytes=10,
        stdout_path=tmp_path / "stdout.log",
        stderr_path=tmp_path / "stderr.log",
    )

    assert result.stdout_truncated is True
    assert result.stderr_truncated is True
    assert result.stdout_path.read_bytes() == b"x" * 10
    assert result.stderr_path.read_bytes() == b"y" * 10
    assert result.error == "stdout exceeded 10 bytes; stderr exceeded 10 bytes"


def test_docker_trace_executor_audit_hashes_existing_artifacts(tmp_path: Path) -> None:
    executor = DockerTraceExecutor(_docker_plan(), output_dir=tmp_path)
    result = _capture_result(
        tmp_path,
        stdout='{"type": "llm_inference", "model": "gpt-4"}\n',
        stderr="warning\n",
    )

    artifacts = executor._collect_artifacts(result)
    complete_entry = _audit_complete_entry(artifacts.audit_path or "")
    hashes = {artifact["name"]: artifact["hash"] for artifact in complete_entry["artifacts"]}

    assert hashes["trajectory"]
    assert hashes["stdout"]
    assert hashes["stderr"]


def test_docker_trace_executor_audit_ignores_missing_artifacts(tmp_path: Path) -> None:
    executor = DockerTraceExecutor(_docker_plan(), output_dir=tmp_path)
    audit_path = tmp_path / "audit.log"

    executor._generate_audit_log(
        audit_path,
        {
            "trajectory": tmp_path / "missing-trajectory.jsonl",
            "stdout": None,
            "stderr": tmp_path / "missing-stderr.log",
        },
    )
    complete_entry = _audit_complete_entry(str(audit_path))
    hashes = {artifact["name"]: artifact["hash"] for artifact in complete_entry["artifacts"]}

    assert hashes == {"trajectory": None, "stdout": None, "stderr": None}


def test_docker_trace_executor_uses_plural_node_targets_env() -> None:
    executor = DockerTraceExecutor(_docker_plan(["adapter:normalize", "adapter:invoke"]))

    args = executor._build_docker_args()
    env_values = [args[index + 1] for index, value in enumerate(args) if value == "-e"]
    plural_values = [value for value in env_values if value.startswith("RED_SENTINEL_NODE_TARGETS=")]
    singular_values = [value for value in env_values if value.startswith("RED_SENTINEL_NODE_TARGET=")]

    assert len(plural_values) == 1
    assert json.loads(plural_values[0].split("=", 1)[1]) == ["adapter:normalize", "adapter:invoke"]
    assert singular_values == ["RED_SENTINEL_NODE_TARGET=adapter:normalize"]
