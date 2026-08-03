from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

from redsentinel.core.models import (
    AgentProfile,
    AgentProfileNode,
    AttackCandidate,
    EvaluationCaseResult,
    EvaluationResult,
    ExperimentManifest,
    Trajectory,
    TrajectoryStep,
)
from redsentinel.research.runner import SingleRoundExperimentRunner


def _profile() -> AgentProfile:
    return AgentProfile(
        agent_name="fixture-agent",
        framework="python_function",
        root_path=".",
        entrypoint="fixture:run",
        business_domain="research",
        nodes=[AgentProfileNode(id="input", type="input_node", target="fixture:run")],
    )


def _manifest(**updates) -> ExperimentManifest:
    values = {
        "experiment_id": "single-round-fixture",
        "research_question": "Does the fixed defense block the fixed attack?",
        "agent_profile_ref": "fixture-agent-profile.json",
        "dataset_refs": ["redsentinel-attack-cases"],
        "attack_strategy": {"name": "fixed"},
        "defense_strategy": {"name": "fixed"},
        "metric_names": ["asr", "fpr"],
        "seeds": [7, 11],
        "repetitions": 2,
        "budget": {},
        "execution_mode": "offline_fixture",
    }
    values.update(updates)
    return ExperimentManifest(**values)


def _attacks() -> list[AttackCandidate]:
    return [
        AttackCandidate(
            candidate_id="attack-1",
            source="runner_fixture",
            risk_type="prompt_injection",
            strategy="direct",
            intensity="medium",
            target="input",
            goal="override policy",
            success_criteria=["unsafe output"],
        )
    ]


class FixtureRuntime:
    adapter_id = "fixture-runtime"

    def run(self, profile, attack, defense, *, experiment_id, seed):  # noqa: ANN001
        return Trajectory(
            session_id=f"{attack.candidate_id}-{seed}",
            experiment_id=experiment_id,
            seed=seed,
            framework="direct_api",
            steps=[
                TrajectoryStep(
                    step_index=0,
                    step_type="monitor_decision",
                    timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc),
                    monitor_decision={"decision": "block", "attack_id": attack.candidate_id},
                )
            ],
        )


class FixtureEvaluator:
    def evaluate(self, profile, trajectories, *, manifest):  # noqa: ANN001
        return EvaluationResult(
            result_id=f"{manifest.experiment_id}-{trajectories[0].seed}",
            experiment_id=manifest.experiment_id,
            agent_profile_ref=manifest.agent_profile_ref,
            cases=[
                EvaluationCaseResult(
                    case_id=trajectory.session_id,
                    case_type="attack",
                    target_node="input",
                    expected_decision="block",
                    actual_decision="block",
                    passed=True,
                    blocked_node="input",
                    trajectory_ref=trajectory.session_id,
                )
                for trajectory in trajectories
            ],
            metrics={"asr": 0.0, "fpr": 0.0},
        )


def test_single_round_runner_is_deterministic_and_persists_complete_artifact(tmp_path: Path) -> None:
    runner = SingleRoundExperimentRunner(
        runtime=FixtureRuntime(),
        evaluator=FixtureEvaluator(),
        artifact_root=tmp_path,
    )

    first = runner.run(_manifest(), _profile(), _attacks())
    first_payload = json.loads(Path(first.artifact_path or "").read_text(encoding="utf-8"))
    second = runner.run(_manifest(), _profile(), _attacks())

    excluded = {"provenance": True, "manifest": {"provenance"}}
    first_comparable = first.model_dump(mode="json", exclude=excluded)
    second_comparable = second.model_dump(mode="json", exclude=excluded)
    assert first_comparable == second_comparable
    assert len(first.records) == 4
    assert all(record.status == "completed" for record in first.records)
    assert all(record.evaluation and record.evaluation.cases for record in first.records)
    assert first.aggregate_metrics == {"asr": 0.0, "fpr": 0.0}
    assert first_payload["manifest"]["execution_mode"] == "offline_fixture"
    assert first_payload["records"][0]["trajectories"][0]["steps"]
    assert first.provenance.git_commit
    assert first.provenance.dataset_sha256["redsentinel-attack-cases"]
    evidence_index = Path(first.evidence_index_path or "")
    assert evidence_index.exists()
    evidence_payload = json.loads(evidence_index.read_text(encoding="utf-8"))
    assert {item["role"] for item in evidence_payload["artifacts"]} == {
        "manifest",
        "provenance",
        "raw_result",
    }


def test_research_runner_imports_when_fastapi_is_unavailable() -> None:
    script = """
import builtins
real_import = builtins.__import__
def guarded_import(name, *args, **kwargs):
    if name == "fastapi" or name.startswith("fastapi."):
        raise ModuleNotFoundError(name)
    return real_import(name, *args, **kwargs)
builtins.__import__ = guarded_import
from redsentinel.research.runner import SingleRoundExperimentRunner
assert SingleRoundExperimentRunner
"""
    completed = subprocess.run(
        [sys.executable, "-c", script],
        check=False,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parents[2] / "src")},
    )

    assert completed.returncode == 0, completed.stderr


def test_single_round_runner_preserves_failure_reason(tmp_path: Path) -> None:
    class FailingRuntime(FixtureRuntime):
        def run(self, profile, attack, defense, *, experiment_id, seed):  # noqa: ANN001
            raise RuntimeError("fixture runtime failed")

    result = SingleRoundExperimentRunner(
        runtime=FailingRuntime(),
        evaluator=FixtureEvaluator(),
        artifact_root=tmp_path,
    ).run(_manifest(seeds=[7], repetitions=1), _profile(), _attacks())

    assert result.records[0].status == "failed"
    assert result.records[0].evaluation is None
    assert result.records[0].failure_reason == "RuntimeError: fixture runtime failed"
    assert result.failures == [
        {"run_id": "single-round-fixture-s7-r0", "reason": "RuntimeError: fixture runtime failed"}
    ]
    assert result.aggregate_metrics == {}


def test_single_round_runner_enforces_case_budget(tmp_path: Path) -> None:
    result = SingleRoundExperimentRunner(
        runtime=FixtureRuntime(),
        evaluator=FixtureEvaluator(),
        artifact_root=tmp_path,
    ).run(
        _manifest(seeds=[7, 11], repetitions=1, budget={"max_cases": 1}),
        _profile(),
        _attacks(),
    )

    assert result.records[0].status == "completed"
    assert result.records[1].status == "budget_exhausted"
    assert result.records[1].failure_reason == "max_cases budget exhausted"


def test_single_round_runner_rejects_fractional_discrete_budget(tmp_path: Path) -> None:
    runner = SingleRoundExperimentRunner(
        runtime=FixtureRuntime(),
        evaluator=FixtureEvaluator(),
        artifact_root=tmp_path,
    )

    with pytest.raises(ValueError, match="max_runs budget must be an integer"):
        runner.run(
            _manifest(seeds=[7], repetitions=1, budget={"max_runs": 1.5}),
            _profile(),
            _attacks(),
        )
