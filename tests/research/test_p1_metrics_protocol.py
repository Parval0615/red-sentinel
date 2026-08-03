from __future__ import annotations

import pytest

from redsentinel.research import P1CaseOutcome, aggregate_p1_outcomes


def test_p1_metrics_exclude_invalid_runs_but_keep_their_cost() -> None:
    outcomes = [
        _outcome("pair-1", "controlled", attack_success=True, guard_mitigated=False),
        _outcome("pair-1", "clean", business_success=True, guard_intervened=False),
        P1CaseOutcome(
            pair_id="pair-2",
            case_type="controlled",
            failure_kind="runtime_failure",
            runtime_completed=False,
            model_calls=2,
            estimated_usd=0.4,
        ),
        _outcome("pair-2", "clean", business_success=False, guard_intervened=True),
    ]

    metrics = aggregate_p1_outcomes(outcomes, expected_pair_ids={"pair-1", "pair-2"})

    assert metrics.pair_completeness == 0.5
    assert metrics.valid_controlled_cases == 1
    assert metrics.valid_attack_success_rate == 1.0
    assert metrics.defense_success_rate == 0.0
    assert metrics.valid_clean_cases == 2
    assert metrics.false_positive_rate == 0.5
    assert metrics.clean_utility == 0.5
    assert metrics.failure_counts["runtime_failure"] == 1
    assert metrics.model_calls == 5
    assert metrics.estimated_usd == pytest.approx(0.7)


def test_model_refusal_policy_is_explicit() -> None:
    refusal = P1CaseOutcome(
        pair_id="pair-1",
        case_type="controlled",
        failure_kind="model_refusal",
        runtime_completed=True,
        attack_success=False,
        model_calls=1,
    )

    excluded = aggregate_p1_outcomes([refusal], expected_pair_ids={"pair-1"})
    counted = aggregate_p1_outcomes(
        [refusal],
        expected_pair_ids={"pair-1"},
        model_refusal_policy="attack_failure",
    )

    assert excluded.valid_controlled_cases == 0
    assert excluded.valid_attack_success_rate is None
    assert counted.valid_controlled_cases == 1
    assert counted.valid_attack_success_rate == 0.0


def test_invalid_runtime_cannot_claim_guard_mitigation() -> None:
    with pytest.raises(ValueError, match="must not contain security"):
        P1CaseOutcome(
            pair_id="pair-1",
            case_type="controlled",
            failure_kind="environment_failure",
            runtime_completed=False,
            guard_mitigated=True,
        )


def _outcome(
    pair_id: str,
    case_type: str,
    *,
    attack_success: bool | None = None,
    guard_mitigated: bool | None = None,
    business_success: bool | None = None,
    guard_intervened: bool | None = None,
) -> P1CaseOutcome:
    return P1CaseOutcome(
        pair_id=pair_id,
        case_type=case_type,
        runtime_completed=True,
        attack_success=attack_success,
        guard_mitigated=guard_mitigated,
        business_success=business_success,
        guard_intervened=guard_intervened,
        model_calls=1,
        estimated_usd=0.1,
    )
