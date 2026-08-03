from __future__ import annotations


def normalize_input(message: str) -> str:
    return message.strip()


def retrieve(query: str) -> list[str]:
    return [f"Policy context for: {query}"]


def execute_tool(name: str, arguments: dict) -> dict:
    return {"tool": name, "arguments": arguments, "status": "ok"}


def format_output(answer: str) -> str:
    return answer


def run_agent(message: str) -> str:
    normalized = normalize_input(message)
    context = retrieve(normalized)
    tool_result = execute_tool("lookup_policy", {"query": normalized})
    return format_output(f"{context[0]} | {tool_result['status']}")
