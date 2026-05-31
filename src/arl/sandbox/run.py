from __future__ import annotations

from datetime import datetime, timezone

from arl.sandbox.backends.autogen import AutoGenBackend
from arl.sandbox.backends.direct_api import DirectAPIBackend
from arl.sandbox.backends.langgraph import LangGraphBackend
from arl.sandbox.config import ScenarioConfig
from arl.sandbox.session import SandboxEnvironment
from arl.telemetry import TrajectoryRecorder


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
    backend.run(session)
    return TrajectoryRecorder.from_session(session, started_at=started_at)
