import pytest

from arl.sandbox.backends.autogen import AutoGenBackend
from arl.sandbox.config import ScenarioConfig
from arl.sandbox.session import SandboxEnvironment
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_autogen_backend_is_stub() -> None:
    config = ScenarioConfig.from_yaml(
        ROOT / "configs" / "scenarios" / "p1-sandbox-5step-direct-api.yaml"
    )
    config = config.model_copy(
        update={"agent": config.agent.model_copy(update={"framework": "autogen"})}
    )
    session = SandboxEnvironment().create_session(config)
    backend = AutoGenBackend()
    with pytest.raises(NotImplementedError):
        backend.run(session)
