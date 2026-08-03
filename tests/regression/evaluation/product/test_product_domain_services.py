from pathlib import Path

from redsentinel.application.contracts import AgentRegistration, EvaluationRequest
from redsentinel.application.engine.domain_services import (
    AgentManagementService,
    EvaluationLifecycleService,
    ReportQueryService,
    SupervisionBridgeService,
)
from redsentinel.application.engine.service import ProductEvaluationService


def test_product_service_composes_independent_domain_services(tmp_path: Path) -> None:
    service = ProductEvaluationService(storage_root=tmp_path)

    assert isinstance(service.agents, AgentManagementService)
    assert isinstance(service.evaluations, EvaluationLifecycleService)
    assert isinstance(service.reports, ReportQueryService)
    assert isinstance(service.supervision, SupervisionBridgeService)
    assert service.agents.owner is service
    assert service.evaluations.owner is service
    assert service.reports.owner is service
    assert service.supervision.owner is service


def test_domain_services_run_combined_product_workflow(tmp_path: Path) -> None:
    facade = ProductEvaluationService(storage_root=tmp_path)
    registration = facade.agents.register_agent(
        AgentRegistration(agent_id="decomposed_agent", name="Decomposed Agent")
    )

    status = facade.evaluations.run_evaluation(
        EvaluationRequest(
            tenant_id=registration.tenant_id,
            agent_id=registration.agent_id,
            scenarios=["support-pii-masking"],
        )
    )
    report = facade.reports.get_report(
        status.report_id or status.evaluation_id,
        tenant_id=registration.tenant_id,
    )
    logs = facade.reports.list_logs(registration.agent_id, registration.tenant_id)
    dashboard = facade.reports.get_dashboard_summary(
        registration.agent_id,
        registration.tenant_id,
    )

    assert status.status == "completed"
    assert report.agent_id == registration.agent_id
    assert logs[0].evaluation_id == status.evaluation_id
    assert dashboard.has_data is True


def test_compatibility_facade_delegates_to_domain_services(
    tmp_path: Path,
    monkeypatch,
) -> None:
    facade = ProductEvaluationService(storage_root=tmp_path)
    expected = AgentRegistration(agent_id="delegated_agent", name="Delegated Agent")
    calls = []

    def register_agent(registration, adapter=None):
        calls.append((registration, adapter))
        return expected

    monkeypatch.setattr(facade.agents, "register_agent", register_agent)

    actual = facade.register_agent(expected)

    assert actual is expected
    assert calls == [(expected, None)]
