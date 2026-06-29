from __future__ import annotations

from unittest.mock import MagicMock, patch

from auto_evaluation_system.sandbox.backends.docker import DockerBackend


def test_docker_backend_framework_name() -> None:
    backend = DockerBackend()
    assert backend.framework == "docker"


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


def test_docker_backend_run_with_timeout() -> None:
    backend = DockerBackend()
    session = MagicMock()
    session.config.agent.framework_config = {"docker_image": "test-image"}
    session.config.agent.system_prompt = "system prompt"
    session.config.agent.goal = "user goal"

    with patch("subprocess.run", side_effect=TimeoutError):
        events = backend.run(session)

    assert len(events) == 0
