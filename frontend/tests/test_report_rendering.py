from __future__ import annotations

import json
from pathlib import Path

from auto_evaluation_system.product_api.contracts import (
    AgentSecurityReport,
    Finding,
    ReportArtifacts,
    ScenarioResult,
)


def test_generate_dashboard_html() -> None:
    report = AgentSecurityReport(
        tenant_id="test_tenant",
        agent_id="test_agent",
        benchmark="test-benchmark",
        overall_score=80,
        risk_level="medium",
        findings=[
            Finding(
                finding_id="F001",
                scenario_id="test-scenario-1",
                severity="high",
                title="Test finding",
                description="Test description",
                business_impact="Test impact",
                recommendation="Test recommendation",
            )
        ],
        scenario_results=[
            ScenarioResult(
                scenario_id="test-scenario-1",
                category="test",
                severity="high",
                expected_decision="block",
                actual_decision="block",
                clean_decision="allow",
                passed=True,
                business_impact="None",
                trajectory_ref="trajectory-1.json",
            )
        ],
        artifacts=ReportArtifacts(
            trajectory_refs=["trajectory-1.json"],
            audit_refs=["audit-1.log"],
            report_path="reports/test.json",
        ),
        attack_success_rate=0.2,
        false_positive_rate=0.05,
    )

    from frontend.generator import generate_dashboard_html

    html = generate_dashboard_html(report)

    assert "<html" in html.lower()
    assert "<head>" in html.lower()
    assert "<body>" in html.lower()
    assert "RedSentinel" in html
    assert "test_agent" in html
    assert "test_tenant" in html
    assert "80" in html
    assert "medium" in html.lower()


def test_write_dashboard_html(tmp_path: Path) -> None:
    report = AgentSecurityReport(
        tenant_id="test_tenant",
        agent_id="test_agent",
        benchmark="test-benchmark",
        overall_score=90,
        risk_level="low",
        findings=[],
        scenario_results=[],
        artifacts=ReportArtifacts(
            trajectory_refs=[],
            audit_refs=[],
            report_path="reports/test.json",
        ),
        attack_success_rate=0.0,
        false_positive_rate=0.0,
    )

    from frontend.generator import write_dashboard_html

    output_path = tmp_path / "dashboard.html"
    write_dashboard_html(report, output_path)

    assert output_path.exists()
    content = output_path.read_text(encoding="utf-8")
    assert "<html" in content.lower()
    assert "90" in content
    assert "low" in content.lower()


def test_render_markdown_report() -> None:
    from auto_evaluation_system.product_api.reports import render_markdown_report

    report = AgentSecurityReport(
        tenant_id="test_tenant",
        agent_id="test_agent",
        benchmark="test-benchmark",
        overall_score=75,
        risk_level="medium",
        findings=[],
        scenario_results=[],
        artifacts=ReportArtifacts(
            trajectory_refs=[],
            audit_refs=[],
            report_path="reports/test.json",
        ),
        attack_success_rate=0.3,
        false_positive_rate=0.1,
    )

    md = render_markdown_report(report)

    assert "# Agent Security Report" in md
    assert "test_agent" in md
    assert "test_tenant" in md
    assert "75" in md
    assert "medium" in md


def test_write_report_artifacts_with_dashboard(tmp_path: Path) -> None:
    from auto_evaluation_system.product_api.reports import write_report_artifacts

    report = AgentSecurityReport(
        tenant_id="test_tenant",
        agent_id="test_agent",
        benchmark="test-benchmark",
        overall_score=85,
        risk_level="low",
        findings=[],
        scenario_results=[],
        artifacts=ReportArtifacts(
            trajectory_refs=[],
            audit_refs=[],
            report_path="reports/test.json",
        ),
        attack_success_rate=0.15,
        false_positive_rate=0.02,
    )

    report_path = tmp_path / "report.json"
    md_path = tmp_path / "report.md"
    dashboard_path = tmp_path / "dashboard.html"

    write_report_artifacts(report, report_path, md_path, dashboard_path)

    assert report_path.exists()
    assert md_path.exists()
    assert dashboard_path.exists()

    report_data = json.loads(report_path.read_text(encoding="utf-8"))
    assert report_data["agent_id"] == "test_agent"
    assert report_data["overall_score"] == 85


def test_risk_level_from_findings() -> None:
    from auto_evaluation_system.product_api.reports import risk_level_from_findings

    assert risk_level_from_findings([]) == "low"
    assert risk_level_from_findings([Finding(finding_id="F1", scenario_id="S1", severity="low", title="t", description="d", business_impact="i", recommendation="r")]) == "low"
    assert risk_level_from_findings([Finding(finding_id="F1", scenario_id="S1", severity="medium", title="t", description="d", business_impact="i", recommendation="r")]) == "medium"
    assert risk_level_from_findings([Finding(finding_id="F1", scenario_id="S1", severity="high", title="t", description="d", business_impact="i", recommendation="r")]) == "high"
    assert risk_level_from_findings([Finding(finding_id="F1", scenario_id="S1", severity="critical", title="t", description="d", business_impact="i", recommendation="r")]) == "critical"
    assert risk_level_from_findings([
        Finding(finding_id="F1", scenario_id="S1", severity="low", title="t", description="d", business_impact="i", recommendation="r"),
        Finding(finding_id="F2", scenario_id="S2", severity="critical", title="t", description="d", business_impact="i", recommendation="r"),
    ]) == "critical"


def test_score_from_findings() -> None:
    from auto_evaluation_system.product_api.reports import score_from_findings

    assert score_from_findings([]) == 100
    assert score_from_findings([Finding(finding_id="F1", scenario_id="S1", severity="low", title="t", description="d", business_impact="i", recommendation="r")]) == 95
    assert score_from_findings([Finding(finding_id="F1", scenario_id="S1", severity="medium", title="t", description="d", business_impact="i", recommendation="r")]) == 90
    assert score_from_findings([Finding(finding_id="F1", scenario_id="S1", severity="high", title="t", description="d", business_impact="i", recommendation="r")]) == 80
    assert score_from_findings([Finding(finding_id="F1", scenario_id="S1", severity="critical", title="t", description="d", business_impact="i", recommendation="r")]) == 70
    assert score_from_findings([
        Finding(finding_id="F1", scenario_id="S1", severity="critical", title="t", description="d", business_impact="i", recommendation="r"),
        Finding(finding_id="F2", scenario_id="S2", severity="critical", title="t", description="d", business_impact="i", recommendation="r"),
        Finding(finding_id="F3", scenario_id="S3", severity="critical", title="t", description="d", business_impact="i", recommendation="r"),
        Finding(finding_id="F4", scenario_id="S4", severity="critical", title="t", description="d", business_impact="i", recommendation="r"),
    ]) == 0