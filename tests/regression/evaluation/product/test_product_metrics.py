from redsentinel.application.contracts import DeterministicMetrics, MetricInputs
from redsentinel.reporting.engine.reports import (
    compute_deterministic_metrics,
    risk_level_from_score,
    score_breakdown_from_metric_inputs,
)


def test_deterministic_metrics_handle_empty_data() -> None:
    metrics = compute_deterministic_metrics(MetricInputs())
    breakdown = score_breakdown_from_metric_inputs(MetricInputs())

    assert metrics.asr == 0.0
    assert metrics.dsr == 0.0
    assert metrics.fpr == 0.0
    assert metrics.coverage_gap == 0.0
    assert breakdown.score == 100
    assert breakdown.risk_level == "low"


def test_risk_mapping_score_boundaries() -> None:
    assert risk_level_from_score(90) == "low"
    assert risk_level_from_score(89) == "medium"
    assert risk_level_from_score(75) == "medium"
    assert risk_level_from_score(74) == "high"
    assert risk_level_from_score(60) == "high"
    assert risk_level_from_score(59) == "critical"


def test_critical_bypass_promotes_risk_to_high() -> None:
    metrics = DeterministicMetrics(critical_attack_bypass_count=1)

    assert risk_level_from_score(95, metrics) == "high"


def test_high_fpr_promotes_risk_to_medium() -> None:
    metrics = DeterministicMetrics(fpr=0.30)

    assert risk_level_from_score(95, metrics) == "medium"


def test_score_formula_uses_asr_fpr_coverage_critical_and_severity_penalty() -> None:
    inputs = MetricInputs(
        attack_case_count=4,
        clean_case_count=2,
        attack_success_count=1,
        attack_blocked_count=3,
        clean_blocked_count=1,
        bypassed_critical_node_count=1,
        critical_node_test_count=2,
        critical_attack_bypass_count=1,
        tested_node_count=3,
        total_required_node_count=4,
        failed_attack_severity_weights=[4],
    )
    metrics = compute_deterministic_metrics(inputs)
    breakdown = score_breakdown_from_metric_inputs(inputs)

    assert metrics.asr == 0.25
    assert metrics.dsr == 0.75
    assert metrics.fpr == 0.5
    assert metrics.coverage_gap == 0.25
    assert metrics.critical_node_bypass_rate == 0.5
    assert metrics.severity_penalty == 1.0
    assert breakdown.score == 65
    assert breakdown.risk_level == "high"
