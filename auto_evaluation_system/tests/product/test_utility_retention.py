from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from auto_evaluation_system.product_api.contracts import AgentRegistration, AgentSecurityReport, EvaluationRequest
from auto_evaluation_system.product_api.service import ProductEvaluationService


@dataclass(frozen=True)
class UtilityRetentionMetrics:
    sample_scope: str
    clean_case_count: int
    clean_allowed_count: int
    clean_blocked_count: int
    allow_rate: float
    false_positive_rate: float


def _utility_metrics(report: AgentSecurityReport) -> UtilityRetentionMetrics:
    clean_decisions = [item.clean_decision for item in report.scenario_results]
    clean_case_count = len(clean_decisions)
    clean_blocked_count = sum(1 for decision in clean_decisions if decision == "block")
    clean_allowed_count = clean_case_count - clean_blocked_count
    allow_rate = clean_allowed_count / clean_case_count if clean_case_count else 0.0
    false_positive_rate = clean_blocked_count / clean_case_count if clean_case_count else 0.0
    return UtilityRetentionMetrics(
        sample_scope="clean_steps from ecommerce-security-v0.1 product benchmark scenarios",
        clean_case_count=clean_case_count,
        clean_allowed_count=clean_allowed_count,
        clean_blocked_count=clean_blocked_count,
        allow_rate=allow_rate,
        false_positive_rate=false_positive_rate,
    )


def test_utility_retention_reports_allow_rate_and_fpr(tmp_path: Path) -> None:
    service = ProductEvaluationService(storage_root=tmp_path)
    registration = service.register_agent(
        AgentRegistration(
            tenant_id="utility_tenant",
            agent_id="utility_ecommerce_agent",
            name="Utility E-commerce Agent",
            adapter_type="ecommerce_demo",
        )
    )

    status = service.run_evaluation(
        EvaluationRequest(
            tenant_id=registration.tenant_id,
            agent_id=registration.agent_id,
            mode="offline_trace",
        )
    )
    report = service.get_report(status.report_id or status.evaluation_id)
    metrics = _utility_metrics(report)

    assert metrics.sample_scope == "clean_steps from ecommerce-security-v0.1 product benchmark scenarios"
    assert metrics.clean_case_count == report.deterministic_metrics.clean_case_count
    assert metrics.clean_allowed_count == metrics.clean_case_count
    assert metrics.clean_blocked_count == 0
    assert metrics.allow_rate == 1.0
    assert metrics.false_positive_rate == 0.0
    assert report.false_positive_rate == metrics.false_positive_rate
