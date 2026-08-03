from pathlib import Path

from redsentinel.application.engine.application import ProductApplicationService
from redsentinel.application.contracts import AgentRegistration, EvaluationRequest


def test_product_application_facade_preserves_product_workflow(tmp_path: Path) -> None:
    application = ProductApplicationService(storage_root=tmp_path)
    agent = application.register_agent(
        AgentRegistration(agent_id="research_agent", name="Research Agent")
    )

    status = application.run_evaluation(
        EvaluationRequest(
            tenant_id=agent.tenant_id,
            agent_id=agent.agent_id,
            scenarios=["support-pii-masking"],
        )
    )
    report = application.get_report(status.report_id or status.evaluation_id)

    assert status.status == "completed"
    assert report.agent_id == agent.agent_id
    assert application.agents.get_agent(agent.agent_id) == agent
    assert application.evaluations.get_evaluation(status.evaluation_id) == status
    assert application.reporting.get_dashboard_summary(agent.agent_id).has_data is True


def test_product_application_exposes_single_supervision_store(tmp_path: Path) -> None:
    application = ProductApplicationService(storage_root=tmp_path)

    assert application.supervision.storage is application.storage
