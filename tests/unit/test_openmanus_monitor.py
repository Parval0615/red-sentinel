from __future__ import annotations

import asyncio
from types import SimpleNamespace
from typing import Any

import pytest

from redsentinel.adapters.engine.openmanus_agent.real_openmanus import (
    attach_real_openmanus_monitor,
)


class FakeHooks:
    def __init__(self) -> None:
        self.llm_inputs: list[list[dict[str, Any]]] = []

    def before_llm_call(self, messages: list[dict[str, Any]]) -> SimpleNamespace:
        self.llm_inputs.append(messages)
        return SimpleNamespace(decision="allow", reason="allowed", ask_id=None)

    def after_llm_call(self, _content: str) -> SimpleNamespace:
        return SimpleNamespace(decision="allow", reason="allowed", ask_id=None)

    def before_tool_call(self, _name: str, _arguments: dict[str, Any]) -> SimpleNamespace:
        return SimpleNamespace(decision="allow", reason="allowed", ask_id=None)

    def after_tool_call(self, _name: str, _arguments: dict[str, Any], _result: Any) -> None:
        return None


class FakeLLM:
    async def ask_tool(self, *_args: Any, **_kwargs: Any) -> SimpleNamespace:
        return SimpleNamespace(content="ok", tool_calls=[])


class FakeAgent:
    def __init__(self) -> None:
        self.llm = FakeLLM()

    async def execute_tool(self, _command: Any) -> str:
        return "ok"


@pytest.mark.parametrize("call_style", ["keyword", "positional"])
def test_openmanus_monitor_observes_keyword_and_positional_messages(call_style: str) -> None:
    agent = FakeAgent()
    hooks = FakeHooks()
    attach_real_openmanus_monitor(agent, hooks)
    messages = [{"role": "user", "content": "inspect me"}]

    if call_style == "keyword":
        asyncio.run(agent.llm.ask_tool(messages=messages))
    else:
        asyncio.run(agent.llm.ask_tool(messages))

    assert hooks.llm_inputs == [messages]


def test_openmanus_monitor_handles_missing_messages_as_empty_list() -> None:
    agent = FakeAgent()
    hooks = FakeHooks()
    attach_real_openmanus_monitor(agent, hooks)

    asyncio.run(agent.llm.ask_tool())

    assert hooks.llm_inputs == [[]]


def test_openmanus_monitor_serializes_non_list_message_without_character_splitting() -> None:
    agent = FakeAgent()
    hooks = FakeHooks()
    attach_real_openmanus_monitor(agent, hooks)

    asyncio.run(agent.llm.ask_tool("single message"))

    assert hooks.llm_inputs == [[{"content": "single message"}]]
