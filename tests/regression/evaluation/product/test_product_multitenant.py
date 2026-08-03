from pathlib import Path

import pytest

from redsentinel.application.contracts import AgentRegistration, AgentSecurityReport, ReportArtifacts
from redsentinel.reporting.engine.reports import write_report_artifacts
from redsentinel.application.engine.service import ProductEvaluationService


def test_same_agent_id_is_isolated_by_tenant(tmp_path: Path) -> None:
    service = ProductEvaluationService(storage_root=tmp_path)

    tenant_a = service.register_agent(AgentRegistration(tenant_id="tenant_a", agent_id="agent", name="Agent A"))
    tenant_b = service.register_agent(AgentRegistration(tenant_id="tenant_b", agent_id="agent", name="Agent B"))

    assert tenant_a.tenant_id == "tenant_a"
    assert tenant_b.tenant_id == "tenant_b"
    assert (tmp_path / "tenant_a" / "agents" / "agent.json").exists()
    assert (tmp_path / "tenant_b" / "agents" / "agent.json").exists()
    assert (tmp_path / "tenant_a" / "agents" / "agent.json").read_text(encoding="utf-8") != (
        tmp_path / "tenant_b" / "agents" / "agent.json"
    ).read_text(encoding="utf-8")


def test_report_lookup_requires_tenant_when_ids_collide(tmp_path: Path) -> None:
    service = ProductEvaluationService(storage_root=tmp_path)
    _write_report(tmp_path, tenant_id="tenant_a", report_id="eval_shared", agent_id="agent_a")
    _write_report(tmp_path, tenant_id="tenant_b", report_id="eval_shared", agent_id="agent_b")

    tenant_a_report = service.get_report("eval_shared", tenant_id="tenant_a")

    assert tenant_a_report.tenant_id == "tenant_a"
    assert tenant_a_report.agent_id == "agent_a"
    with pytest.raises(ValueError, match="tenant_id is required"):
        service.get_report("eval_shared")


def test_tenant_cannot_read_other_tenant_uploaded_trajectory(tmp_path: Path) -> None:
    service = ProductEvaluationService(storage_root=tmp_path)
    service.register_agent(AgentRegistration(tenant_id="tenant_a", agent_id="agent", name="Agent A"))
    service.register_agent(AgentRegistration(tenant_id="tenant_b", agent_id="agent", name="Agent B"))

    uploaded = service.upload_trajectory("tenant_a", "agent", {"turns": [{"message": "tenant-a-secret"}]})

    own = service.get_uploaded_trajectory("tenant_a", uploaded["trajectory_id"])
    assert own["turns"][0]["message"] == "tenant-a-secret"
    with pytest.raises(ValueError, match="Trajectory not found"):
        service.get_uploaded_trajectory("tenant_b", uploaded["trajectory_id"])


def test_compare_reports_rejects_cross_tenant_ids(tmp_path: Path) -> None:
    service = ProductEvaluationService(storage_root=tmp_path)
    _write_report(tmp_path, tenant_id="tenant_a", report_id="eval_a", agent_id="agent")
    _write_report(tmp_path, tenant_id="tenant_b", report_id="eval_b", agent_id="agent")

    with pytest.raises(ValueError, match="same tenant"):
        service.compare_reports("eval_a", "eval_b")


def _write_report(tmp_path: Path, *, tenant_id: str, report_id: str, agent_id: str) -> None:
    report_path = tmp_path / tenant_id / "evaluations" / report_id / "agent-security-report-v0.1.json"
    report = AgentSecurityReport(
        tenant_id=tenant_id,
        agent_id=agent_id,
        benchmark="m6-isolation",
        overall_score=100,
        risk_level="low",
        artifacts=ReportArtifacts(report_path=str(report_path)),
    )
    write_report_artifacts(report, report_path, report_path.with_suffix(".md"))
