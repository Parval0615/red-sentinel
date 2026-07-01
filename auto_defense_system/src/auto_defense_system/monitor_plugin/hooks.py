from __future__ import annotations

from typing import Any

from auto_defense_system.monitor_plugin.interceptor import MonitorDecision, MonitorInterceptor
from auto_defense_system.openmanus_agent.adapter import OpenManusAdapter


class OpenManusMonitorHooks:
    def __init__(self, interceptor: MonitorInterceptor) -> None:
        self.interceptor = interceptor

    def before_llm_call(self, messages: list[dict[str, Any]]) -> MonitorDecision:
        return self.interceptor.intercept("llm_input", {"messages": messages, "content": str(messages)})

    def after_llm_call(self, content: str) -> MonitorDecision:
        return self.interceptor.intercept("llm_output", {"content": content})

    def before_tool_call(self, tool_name: str, arguments: dict[str, Any]) -> MonitorDecision:
        return self.interceptor.intercept("tool_call", {"tool_name": tool_name, "arguments": arguments})

    def after_tool_call(self, tool_name: str, arguments: dict[str, Any], result: Any) -> MonitorDecision:
        return self.interceptor.intercept(
            "tool_result",
            {"tool_name": tool_name, "arguments": arguments, "content": str(result)},
        )

    def wrap_adapter(self, adapter: OpenManusAdapter) -> OpenManusAdapter:
        hooks = self
        original_call = adapter.call_tool

        def monitored_call(name: str, arguments: dict[str, Any]) -> str:
            decision = hooks.before_tool_call(name, arguments)
            if decision.decision == "deny":
                return f"[MONITOR_DENY] {decision.reason}"
            if decision.decision == "ask":
                return f"[MONITOR_ASK] {decision.ask_id}: {decision.reason}"
            result = original_call(name, arguments)
            hooks.after_tool_call(name, arguments, result)
            return result

        adapter.call_tool = monitored_call  # type: ignore[method-assign]
        return adapter
