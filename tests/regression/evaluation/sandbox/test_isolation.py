from pathlib import Path

from redsentinel.runtime.engine.sandbox.config import ScenarioConfig
from redsentinel.runtime.engine.sandbox.session import SandboxEnvironment


ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "pyproject.toml").is_file())


def test_sessions_are_isolated() -> None:
    path = ROOT / "configs" / "scenarios" / "p1-sandbox-5step-direct-api.yaml"
    config = ScenarioConfig.from_yaml(path)
    env = SandboxEnvironment()
    s1 = env.create_session(config)
    s2 = env.create_session(config)
    assert s1.session_id != s2.session_id
    assert s1.tools is not s2.tools
    assert s1.emitter is not s2.emitter
    assert s1.memory_store is not s2.memory_store
    s1.memory_store.write(s1.memory_namespace, "short_term", "key", 1)
    value, _ = s2.memory_store.read(s2.memory_namespace, "short_term", "key")
    assert value is None
