from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Protocol

from arl.events.models import (
    LLMInferencePayload,
    StepEvent,
    StepType,
    ToolCallIntent,
    ToolCallPayload,
)
from arl.sandbox.session import SandboxSession


class AgentBackend(Protocol):
    framework: str

    def run(self, session: SandboxSession) -> list[StepEvent]:
        ...


def utcnow() -> datetime:
    return datetime.now(tz=timezone.utc)


def emit_llm_step(session: SandboxSession, messages: list[dict[str, Any]], response: dict[str, Any]) -> int:
    intents = [
        ToolCallIntent(
            call_id=tc["id"],
            name=tc["function"]["name"],
            arguments=session.tools.parse_arguments(tc["function"]["arguments"]),
        )
        for tc in response.get("tool_calls", [])
    ]
    event = StepEvent(
        step_type=StepType.LLM_INFERENCE,
        timestamp=utcnow(),
        llm=LLMInferencePayload(
            model=session.config.agent.model,
            input_messages=messages,
            output_content=response.get("content"),
            tool_call_intents=intents,
            turn_index=response["turn_index"],
            latency_ms=response.get("latency_ms"),
        ),
        state_delta={"framework": session.config.agent.framework},
    )
    return session.emitter.emit(event)


def emit_tool_step(
    session: SandboxSession,
    call_id: str,
    name: str,
    arguments: dict[str, Any],
    response: Any,
    parent_turn_index: int,
    latency_ms: float = 1.0,
    state_delta: dict[str, Any] | None = None,
) -> int:
    delta = state_delta or {"framework": session.config.agent.framework}
    event = StepEvent(
        step_type=StepType.TOOL_CALL,
        timestamp=utcnow(),
        tool_call=ToolCallPayload(
            call_id=call_id,
            name=name,
            arguments=arguments,
            response=response,
            parent_turn_index=parent_turn_index,
            latency_ms=latency_ms,
        ),
        state_delta=delta,
    )
    return session.emitter.emit(event)


def append_assistant_tool_message(
    messages: list[dict[str, Any]], tool_calls: list[dict[str, Any]]
) -> None:
    messages.append(
        {
            "role": "assistant",
            "content": None,
            "tool_calls": tool_calls,
        }
    )


def append_tool_result(messages: list[dict[str, Any]], call_id: str, content: str) -> None:
    messages.append({"role": "tool", "tool_call_id": call_id, "content": content})
