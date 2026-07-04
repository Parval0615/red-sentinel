from app.agent.base import BaseAgent
from app.agent.mcp import MCPAgent
from app.agent.react import ReActAgent
from app.agent.swe import SWEAgent
from app.agent.toolcall import ToolCallAgent

try:
    from app.agent.browser import BrowserAgent
except ModuleNotFoundError:
    BrowserAgent = None  # type: ignore[assignment]

__all__ = [
    "BaseAgent",
    "ReActAgent",
    "SWEAgent",
    "ToolCallAgent",
    "MCPAgent",
]

if BrowserAgent is not None:
    __all__.append("BrowserAgent")
