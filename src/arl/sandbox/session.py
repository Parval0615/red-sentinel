from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

from arl.memory import InMemoryMemoryStore
from arl.sandbox.config import ScenarioConfig
from arl.sandbox.llm.vcr_client import VCRCachedLLMClient
from arl.sandbox.tools.registry import ToolRegistry
from arl.telemetry import TelemetryStepEmitter


@dataclass
class SandboxSession:
    config: ScenarioConfig
    session_id: str
    emitter: TelemetryStepEmitter
    tools: ToolRegistry
    llm: VCRCachedLLMClient
    memory_store: InMemoryMemoryStore

    @property
    def memory_namespace(self) -> str:
        if self.config.memory:
            return self.config.memory.namespace
        return f"session-{self.session_id}"


class SandboxEnvironment:
    """Creates isolated sandbox sessions with no shared mutable state."""

    def create_session(self, config: ScenarioConfig) -> SandboxSession:
        emitter = TelemetryStepEmitter(max_steps=config.runner.max_steps)
        tools = ToolRegistry(mode=config.tools.mode)
        tools.register_defaults()
        llm = VCRCachedLLMClient(config=config, session_id=str(uuid4()))
        return SandboxSession(
            config=config,
            session_id=str(uuid4()),
            emitter=emitter,
            tools=tools,
            llm=llm,
            memory_store=InMemoryMemoryStore(),
        )
