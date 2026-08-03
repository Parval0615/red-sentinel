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
from redsentinel.research.evolution import (
    AppendOnlyEvolutionLedger,
    CoEvolutionEngine,
    EvolutionConfig,
)


def _profile() -> AgentProfile:
    return AgentProfile(
        agent_name="evolution-fixture",
        framework="python_function",
        root_path=".",
        entrypoint="fixture:run",
        business_domain="research",
        nodes=[AgentProfileNode(id="input", type="input_node", target="fixture:run")],
    )


def _manifest() -> ExperimentManifest:
    return ExperimentManifest(
        experiment_id="coevolution-fixture",
        research_question="Does co-evolution reduce attack success?",
        agent_profile_ref="fixture-profile.json",
        dataset_refs=["fixture-v1"],
        attack_strategy={"name": "fixture-evolution"},
        defense_strategy={"name": "fixture-optimization"},
        metric_names=["asr", "utility"],
        seeds=[17],
        repetitions=1,
        execution_mode="offline_fixture",
    )


class FixtureAttackGenerator:
    def generate(self, profile, state, *, seed):  # noqa: ANN001
        return [
            AttackCandidate(
                candidate_id=f"attack-r{state.round_index}-{index}",
                source="evolution_fixture",
                risk_type="prompt_injection",
                strategy="mutation",
                intensity="medium",
                target="input",
                goal="override policy",
                success_criteria=["unsafe output"],
                estimated_cost=0.25,
                metadata={"fitness": float(index)},
            )
            for index in range(4)
        ]


class FixtureDefenseOptimizer:
    def optimize(self, profile, evaluation, state, *, seed):  # noqa: ANN001
        return [
            DefenseCandidate(
                candidate_id=f"defense-r{state.round_index}-{index}",
                agent_name=profile.agent_name,
                target_node_ids=["input"],
                actions=[{"type": "input_guard", "strength": index + 1}],
                estimated_cost=0.5,
                metadata={"fitness": float(index), "utility": 0.9},
            )
            for index in range(3)
        ]


class FixtureRuntime:
    adapter_id = "evolution-fixture-runtime"

    def run(self, profile, attack, defense, *, experiment_id, seed):  # noqa: ANN001
        decision = "block" if defense is not None else "allow"
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
                        "decision": decision,
                        "attack_id": attack.candidate_id,
                        "defense_id": defense.candidate_id if defense else None,
                    },
                )
            ],
            metadata={"utility": defense.metadata.get("utility", 1.0) if defense else 1.0},
        )


class FixtureEvaluator:
    def __init__(self, *, guarded_asr: float = 0.0, utility: float = 0.9) -> None:
        self.guarded_asr = guarded_asr
        self.utility = utility

    def evaluate(self, profile, trajectories, *, manifest):  # noqa: ANN001
        guarded = all(item.steps[0].monitor_decision["decision"] == "block" for item in trajectories)
        asr = self.guarded_asr if guarded else 1.0
        suffix = "-".join(item.session_id for item in trajectories)
        return EvaluationResult(
            result_id=f"evaluation-{suffix}",
            experiment_id=manifest.experiment_id,
            agent_profile_ref=manifest.agent_profile_ref,
            cases=[
                EvaluationCaseResult(
                    case_id=item.session_id,
                    case_type="attack",
                    target_node="input",
                    expected_decision="block",
                    actual_decision="block" if guarded else "allow",
                    passed=guarded,
                    blocked_node="input" if guarded else None,
                    trajectory_ref=item.session_id,
                )
                for item in trajectories
            ],
            metrics={"asr": asr, "utility": self.utility},
        )


def _engine(tmp_path: Path, **config_updates) -> CoEvolutionEngine:
    return CoEvolutionEngine(
        attack_generator=FixtureAttackGenerator(),
        defense_optimizer=FixtureDefenseOptimizer(),
        runtime=FixtureRuntime(),
        evaluator=FixtureEvaluator(),
        config=EvolutionConfig(**config_updates),
        artifact_root=tmp_path,
    )


def test_coevolution_runs_all_stages_and_stops_at_risk_target(tmp_path: Path) -> None:
    result = _engine(
        tmp_path,
        max_rounds=3,
        attack_elite_count=2,
        defense_elite_count=1,
        exploration_rate=0.5,
        risk_target=0.0,
    ).run(_manifest(), _profile(), seed=17)

    assert result.final_state.stage == "completed"
    assert result.final_state.stop_reason == "risk_target_met"
    assert len(result.rounds) == 1
    assert len(result.rounds[0].selected_attack_ids) == 2
    assert result.rounds[0].selected_defense_ids == ["defense-r0-2"]
    assert result.rounds[0].regression_evaluation.metrics["asr"] == 0.0

    stages = [entry.stage for entry in AppendOnlyEvolutionLedger(result.ledger_path).read()]
    assert stages == [
        "initialized",
        "attack_generation",
        "execution",
        "evaluation",
        "attack_selection",
        "defense_generation",
        "defense_selection",
        "regression",
        "completed",
    ]


def test_same_seed_produces_same_state_rounds_and_ledger(tmp_path: Path) -> None:
    first = _engine(
        tmp_path / "first",
        max_rounds=2,
        attack_elite_count=2,
        defense_elite_count=2,
        exploration_rate=0.5,
    ).run(_manifest(), _profile(), seed=23)
    second = _engine(
        tmp_path / "second",
        max_rounds=2,
        attack_elite_count=2,
        defense_elite_count=2,
        exploration_rate=0.5,
    ).run(_manifest(), _profile(), seed=23)

    assert first.final_state == second.final_state
    assert first.rounds == second.rounds
    first_entries = AppendOnlyEvolutionLedger(first.ledger_path).read()
    second_entries = AppendOnlyEvolutionLedger(second.ledger_path).read()
    assert first_entries == second_entries


@pytest.mark.parametrize(
    ("config", "evaluator", "reason"),
    [
        ({"max_rounds": 4, "max_budget": 1.0}, FixtureEvaluator(), "budget_exhausted"),
        (
            {"max_rounds": 4, "utility_floor": 0.8},
            FixtureEvaluator(guarded_asr=0.4, utility=0.5),
            "utility_floor_violated",
        ),
        (
            {"max_rounds": 4, "no_improvement_rounds": 1},
            FixtureEvaluator(guarded_asr=0.4),
            "no_improvement",
        ),
        ({"max_rounds": 2}, FixtureEvaluator(guarded_asr=0.4), "max_rounds"),
    ],
)
def test_stop_conditions(
    tmp_path: Path,
    config: dict,
    evaluator: FixtureEvaluator,
    reason: str,
) -> None:
    engine = CoEvolutionEngine(
        attack_generator=FixtureAttackGenerator(),
        defense_optimizer=FixtureDefenseOptimizer(),
        runtime=FixtureRuntime(),
        evaluator=evaluator,
        config=EvolutionConfig(**config),
        artifact_root=tmp_path / reason,
    )

    result = engine.run(_manifest(), _profile(), seed=31)

    assert result.final_state.stop_reason == reason
    if engine.config.max_budget is not None:
        assert result.final_state.budget_spent <= engine.config.max_budget


def test_ledger_is_append_only_and_detects_tampering(tmp_path: Path) -> None:
    result = _engine(tmp_path, max_rounds=1).run(_manifest(), _profile(), seed=17)
    ledger = AppendOnlyEvolutionLedger(result.ledger_path)
    before = ledger.read()
    ledger.append(result.final_state, {"note": "independent verification"})
    after = ledger.read()
    assert after[: len(before)] == before
    assert len(after) == len(before) + 1

    lines = Path(result.ledger_path).read_text(encoding="utf-8").splitlines()
    payload = json.loads(lines[1])
    payload["payload"] = {"tampered": True}
    lines[1] = json.dumps(payload, sort_keys=True)
    Path(result.ledger_path).write_text("\n".join(lines) + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match="hash chain is invalid"):
        ledger.read()
