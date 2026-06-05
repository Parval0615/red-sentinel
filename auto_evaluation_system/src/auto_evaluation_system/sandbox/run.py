from __future__ import annotations

from datetime import datetime, timezone

from auto_attack_system.injectors.memory_poisoning import MemoryPoisoningInjector
from auto_evaluation_system.sandbox.backends.autogen import AutoGenBackend
from auto_evaluation_system.sandbox.backends.direct_api import DirectAPIBackend
from auto_evaluation_system.sandbox.backends.langgraph import LangGraphBackend
from auto_evaluation_system.sandbox.config import ScenarioConfig
from auto_evaluation_system.sandbox.session import SandboxEnvironment
from auto_evaluation_system.telemetry import TrajectoryRecorder


def get_backend(framework: str):
    if framework == "direct_api":
        return DirectAPIBackend()
    if framework == "langgraph":
        return LangGraphBackend()
    if framework == "autogen":
        return AutoGenBackend()
    raise ValueError(f"Unsupported framework: {framework}")


def run_scenario(path: str) -> dict:
    config = ScenarioConfig.from_yaml(path)
    env = SandboxEnvironment()
    session = env.create_session(config)
    backend = get_backend(config.agent.framework)
    started_at = datetime.now(tz=timezone.utc)
    MemoryPoisoningInjector().apply(session)
    backend.run(session)
    return TrajectoryRecorder.from_session(session, started_at=started_at)
