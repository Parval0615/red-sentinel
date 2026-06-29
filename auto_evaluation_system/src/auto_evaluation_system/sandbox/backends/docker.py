from __future__ import annotations

import json
import subprocess
from typing import Any

from auto_evaluation_system.events.models import StepEvent, StepType, ToolCallPayload, LLMInferencePayload
from auto_evaluation_system.sandbox.backends.base import utcnow
from auto_evaluation_system.sandbox.session import SandboxSession


class DockerBackend:
    framework = "docker"

    def run(self, session: SandboxSession) -> list[StepEvent]:
        config = session.config
        docker_image = config.agent.framework_config.get("docker_image", "")
        if not docker_image:
            return []

        args = ["docker", "run", "--rm", "--network=none"]

        if config.agent.system_prompt:
            args.extend(["-e", f"SYSTEM_PROMPT={config.agent.system_prompt}"])
        if config.agent.goal:
            args.extend(["-e", f"USER_GOAL={config.agent.goal}"])

        args.append(docker_image)

        try:
            result = subprocess.run(
                args,
                capture_output=True,
                text=True,
                timeout=300,
            )
        except (subprocess.TimeoutExpired, TimeoutError):
            return []

        return self._parse_output_to_events(result.stdout, result.stderr)

    def _parse_output_to_events(self, stdout: str, stderr: str) -> list[StepEvent]:
        events: list[StepEvent] = []
        lines = stdout.strip().split("\n")

        for line in lines:
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
                event = self._create_event_from_payload(payload)
                if event:
                    events.append(event)
            except json.JSONDecodeError:
                continue

        return events

    def _create_event_from_payload(self, payload: dict[str, Any]) -> StepEvent | None:
        event_type = payload.get("type", "").lower()

        if event_type == "llm_inference":
            return StepEvent(
                step_type=StepType.LLM_INFERENCE,
                timestamp=utcnow(),
                llm=LLMInferencePayload(
                    model=payload.get("model", "unknown"),
                    input_messages=payload.get("input_messages", []),
                    output_content=payload.get("output_content", ""),
                    tool_call_intents=[],
                    turn_index=payload.get("turn_index", 0),
                ),
            )

        if event_type == "tool_call":
            return StepEvent(
                step_type=StepType.TOOL_CALL,
                timestamp=utcnow(),
                tool_call=ToolCallPayload(
                    call_id=payload.get("call_id", ""),
                    name=payload.get("tool_name", ""),
                    arguments=payload.get("arguments", {}),
                    response=payload.get("response"),
                    parent_turn_index=payload.get("parent_turn_index", 0),
                ),
            )

        return None
