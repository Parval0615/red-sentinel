import json
from datetime import datetime, timezone
from pathlib import Path

from jsonschema import validate

from redsentinel.runtime.engine.events import LLMInferencePayload, StepEvent, StepType
from redsentinel.evaluation.engine.runner import ExperimentRunner
from redsentinel.runtime.engine.sandbox.config import ScenarioConfig
from redsentinel.runtime.engine.sandbox.session import SandboxEnvironment
from redsentinel.runtime.engine.telemetry import TrajectoryRecorder


ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "pyproject.toml").is_file())
SCHEMA = json.loads((ROOT / "schemas" / "trajectory-v1.schema.json").read_text(encoding="utf-8"))
SCENARIO = ROOT / "configs" / "scenarios" / "p1-sandbox-5step-direct-api.yaml"


def test_runner_sandbox_telemetry_results_chain(tmp_path: Path) -> None:
    result = ExperimentRunner(results_root=tmp_path / "runs").run_scenario(SCENARIO)

    assert result.output_dir.exists()
    validate(instance=result.trajectory, schema=SCHEMA)
    assert result.trajectory["experiment_id"] == "p1-sandbox-5step-direct-api"


def test_sandbox_memory_telemetry_chain() -> None:
    config = ScenarioConfig.from_yaml(SCENARIO)
    session = SandboxEnvironment().create_session(config)
    audit = session.memory_store.write(
        session.memory_namespace,
        "short_term",
        "k1",
        {"fact": "value"},
    )
    session.emitter.emit(
        StepEvent(
            step_type=StepType.LLM_INFERENCE,
            timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc),
            llm=LLMInferencePayload(
                model="gpt-4o-mini",
                input_messages=[{"role": "user", "content": "use memory"}],
                turn_index=0,
            ),
            memory_ops=[audit.to_payload()],
        )
    )

    trajectory = TrajectoryRecorder.from_session(session)

    validate(instance=trajectory, schema=SCHEMA)
    assert trajectory["steps"][0]["memory_ops"][0]["namespace"] == session.memory_namespace
