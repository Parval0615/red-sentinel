from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from redsentinel.core.models import (
    AgentProfile,
    AgentProfileNode,
    AttackCandidate,
    DefenseCandidate,
    EvaluationCaseResult,
    EvaluationResult,
    ExperimentManifest,
    Trajectory,
    TrajectoryStep,
)
from redsentinel.research.baselines import AblationConfig, BaselineMatrixRunner
from redsentinel.research.evolution import EvolutionConfig


def _profile() -> AgentProfile:
    return AgentProfile(
        agent_name="baseline-fixture",
        framework="python_function",
        root_path=".",
        entrypoint="fixture:run",
        business_domain="research",
        nodes=[
            AgentProfileNode(
                id="input",
                type="input_node",
                target="fixture:run",
                risk_surfaces=["prompt_injection"],
                defenses=["input_guard"],
            )
        ],
        attack_entries=["prompt"],
        sensitive_data=["email"],
    )


def _manifest() -> ExperimentManifest:
    return ExperimentManifest(
        experiment_id="baseline-matrix-fixture",
        research_question="Which evolution arm performs best under shared controls?",
        agent_profile_ref="fixture-profile.json",
        dataset_refs=["shared-fixture-v1"],
        attack_strategy={"name": "matrix"},
        defense_strategy={"name": "matrix"},
        metric_names=["asr", "utility"],
        seeds=[19],
        repetitions=1,
        budget={"max_cases": 20},
        execution_mode="offline_fixture",
    )


class FixedAttackGenerator:
    def __init__(self) -> None:
        self.calls: list[tuple[bool, int]] = []

    def generate(self, profile, state, *, seed):  # noqa: ANN001
        self.calls.append((bool(profile.nodes[0].risk_surfaces), len(state.evaluation_refs)))
        return [_attack("fixed-attack", fitness=1.0)]


class EvolvingAttackGenerator(FixedAttackGenerator):
    def generate(self, profile, state, *, seed):  # noqa: ANN001
        self.calls.append((bool(profile.nodes[0].risk_surfaces), len(state.evaluation_refs)))
        return [_attack(f"evolved-attack-r{state.round_index}", fitness=2.0)]


class FixedDefenseOptimizer:
    def __init__(self) -> None:
        self.attribution_seen: list[bool] = []

    def optimize(self, profile, evaluation, state, *, seed):  # noqa: ANN001
        self.attribution_seen.append(bool(evaluation.attribution))
        return [_defense("fixed-defense", fitness=1.0)]


class EvolvingDefenseOptimizer(FixedDefenseOptimizer):
    def optimize(self, profile, evaluation, state, *, seed):  # noqa: ANN001
        self.attribution_seen.append(bool(evaluation.attribution))
        return [_defense(f"evolved-defense-r{state.round_index}", fitness=2.0)]


class FixtureRuntime:
    adapter_id = "baseline-fixture-runtime"

    def run(self, profile, attack, defense, *, experiment_id, seed):  # noqa: ANN001
        return Trajectory(
            session_id=f"{attack.candidate_id}-{defense.candidate_id if defense else 'none'}-{seed}",
            experiment_id=experiment_id,
            seed=seed,
            framework="direct_api",
            steps=[
                TrajectoryStep(
                    step_index=0,
                    step_type="monitor_decision",
                    timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc),
                    monitor_decision={
                        "decision": "block" if defense else "allow",
                        "anomaly_score": 0.9,
                    },
                )
            ],
            metadata={"anomaly_score": 0.9},
        )


class FixtureEvaluator:
    def __init__(self, *, utility: float = 0.9) -> None:
        self.utility = utility
        self.anomaly_seen: list[bool] = []

    def evaluate(self, profile, trajectories, *, manifest):  # noqa: ANN001
        self.anomaly_seen.append("anomaly_score" in trajectories[0].metadata)
        session_id = trajectories[0].session_id
        attack_evolved = "evolved-attack" in session_id
        defense_evolved = "evolved-defense" in session_id
        asr = 0.7 + (0.1 if attack_evolved else 0.0) - (0.2 if defense_evolved else 0.0)
        guarded = "-none-" not in session_id
        return EvaluationResult(
            result_id=f"evaluation-{session_id}",
            experiment_id=manifest.experiment_id,
            agent_profile_ref=manifest.agent_profile_ref,
            cases=[
                EvaluationCaseResult(
                    case_id=session_id,
                    case_type="attack",
                    target_node="input",
                    expected_decision="block",
                    actual_decision="block" if guarded else "allow",
                    passed=guarded,
                    blocked_node="input" if guarded else None,
                    bypassed_nodes=[] if guarded else ["input"],
                    trajectory_ref=session_id,
                )
            ],
            metrics={
                "asr": asr,
                "fpr": 0.05,
                "utility": self.utility,
                "business_success_rate": self.utility,
                "overhead": 0.1,
            },
            attribution={"target_node": "input"},
        )


def _attack(candidate_id: str, *, fitness: float) -> AttackCandidate:
    return AttackCandidate(
        candidate_id=candidate_id,
        source="baseline_fixture",
        risk_type="prompt_injection",
        strategy="fixture",
        intensity="medium",
        target="input",
        goal="override policy",
        success_criteria=["unsafe output"],
        metadata={"fitness": fitness},
    )


def _defense(candidate_id: str, *, fitness: float) -> DefenseCandidate:
    return DefenseCandidate(
        candidate_id=candidate_id,
        agent_name="baseline-fixture",
        target_node_ids=["input"],
        actions=[{"type": "input_guard"}],
        utility_constraints={"minimum_utility": 0.8},
        metadata={"fitness": fitness},
    )


def _runner(
    tmp_path: Path,
    *,
    evaluator: FixtureEvaluator | None = None,
    config: EvolutionConfig | None = None,
) -> tuple[
    BaselineMatrixRunner,
    FixedAttackGenerator,
    EvolvingAttackGenerator,
    FixedDefenseOptimizer,
    EvolvingDefenseOptimizer,
    FixtureEvaluator,
]:
    fixed_attack = FixedAttackGenerator()
    evolving_attack = EvolvingAttackGenerator()
    fixed_defense = FixedDefenseOptimizer()
    evolving_defense = EvolvingDefenseOptimizer()
    active_evaluator = evaluator or FixtureEvaluator()
    dataset_path = tmp_path / "shared-fixture-v1.json"
    dataset_path.parent.mkdir(parents=True, exist_ok=True)
    dataset_path.write_text('{"schema_version":"fixture-v1"}\n', encoding="utf-8")
    return (
        BaselineMatrixRunner(
            fixed_attack_generator=fixed_attack,
            evolving_attack_generator=evolving_attack,
            fixed_defense_optimizer=fixed_defense,
            evolving_defense_optimizer=evolving_defense,
            runtime=FixtureRuntime(),
            evaluator=active_evaluator,
            config=config or EvolutionConfig(max_rounds=2),
            artifact_root=tmp_path,
            dataset_paths={"shared-fixture-v1": dataset_path},
        ),
        fixed_attack,
        evolving_attack,
        fixed_defense,
        evolving_defense,
        active_evaluator,
    )


def test_matrix_runs_four_comparable_arms_and_persists_result(tmp_path: Path) -> None:
    runner, *_ = _runner(tmp_path)
    comparison = runner.run(_manifest(), _profile(), seed=19)

    assert [item.name for item in comparison.results] == [
        "fixed",
        "attack_only",
        "defense_only",
        "coevolution",
    ]
    assert [(item.attack_evolution, item.defense_evolution) for item in comparison.results] == [
        (False, False),
        (True, False),
        (False, True),
        (True, True),
    ]
    assert comparison.dataset_refs == ["shared-fixture-v1"]
    assert comparison.budget == {"max_cases": 20.0}
    assert comparison.seed == 19
    assert comparison.metric_names == ["asr", "utility"]
    metrics = {item.name: item.final_metrics["asr"] for item in comparison.results}
    assert metrics["fixed"] == pytest.approx(0.7)
    assert metrics["attack_only"] == pytest.approx(0.8)
    assert metrics["defense_only"] == pytest.approx(0.5)
    assert metrics["coevolution"] == pytest.approx(0.6)
    payload = json.loads(Path(comparison.artifact_path).read_text(encoding="utf-8"))
    assert payload["schema_version"] == "baseline-comparison-v1"
    assert len(payload["results"]) == 4
    assert Path(comparison.provenance_path).is_file()
    assert Path(comparison.evidence_index_path).is_file()
    assert comparison.results[0].utility_constrained_metrics == {
        "asr": pytest.approx(0.7),
        "fpr": pytest.approx(0.05),
        "business_success_rate": pytest.approx(0.9),
        "overhead": pytest.approx(0.1),
    }


def test_same_seed_produces_identical_comparison(tmp_path: Path) -> None:
    first, *_ = _runner(tmp_path / "first")
    second, *_ = _runner(tmp_path / "second")

    first_result = first.run(_manifest(), _profile(), seed=23)
    second_result = second.run(_manifest(), _profile(), seed=23)

    volatile_paths = {"artifact_path", "provenance_path", "evidence_index_path"}
    first_payload = first_result.model_dump(mode="json", exclude=volatile_paths)
    second_payload = second_result.model_dump(mode="json", exclude=volatile_paths)
    for result in first_payload["results"]:
        result["run"].pop("ledger_path")
    for result in second_payload["results"]:
        result["run"].pop("ledger_path")
    assert first_payload == second_payload


def test_all_ablation_switches_remove_only_their_research_signals(tmp_path: Path) -> None:
    low_utility_evaluator = FixtureEvaluator(utility=0.5)
    runner, fixed_attack, evolving_attack, fixed_defense, evolving_defense, evaluator = _runner(
        tmp_path,
        evaluator=low_utility_evaluator,
        config=EvolutionConfig(max_rounds=2, utility_floor=0.8),
    )
    switches = AblationConfig(
        profile=False,
        trajectory_anomaly=False,
        node_attribution=False,
        reflection=False,
        utility_constraints=False,
    )

    comparison = runner.run(_manifest(), _profile(), seed=19, ablations=switches)

    assert Path(comparison.provenance_path).is_file()
    assert Path(comparison.evidence_index_path).is_file()
    assert all(not profile_signal for profile_signal, _ in [*fixed_attack.calls, *evolving_attack.calls])
    assert all(ref_count == 0 for _, ref_count in [*fixed_attack.calls, *evolving_attack.calls])
    assert evaluator.anomaly_seen and not any(evaluator.anomaly_seen)
    assert not any([*fixed_defense.attribution_seen, *evolving_defense.attribution_seen])
    assert all(item.run.final_state.stop_reason == "max_rounds" for item in comparison.results)
    for result in comparison.results:
        assert result.run.final_state.defense_population
        assert all(not item.utility_constraints for item in result.run.final_state.defense_population)
        final_evaluation = result.run.rounds[-1].regression_evaluation
        assert final_evaluation.attribution == {}
        assert final_evaluation.cases[0].blocked_node is None
