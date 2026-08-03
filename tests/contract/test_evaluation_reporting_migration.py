from __future__ import annotations

import ast
import json
from pathlib import Path

from redsentinel.evaluation.engine.detection.oracle import evaluate_oracle as legacy_evaluate_oracle
from redsentinel.evaluation.engine.benchmarks.evaluate import evaluate_classifier as legacy_evaluate_classifier
from redsentinel.evaluation.engine.benchmarks.output_eval import evaluate_output_filter as legacy_evaluate_output_filter
from redsentinel.application.contracts import (
    AgentSecurityReport as LegacyAgentSecurityReport,
)
from redsentinel.application.contracts import (
    MetricInputs as LegacyMetricInputs,
)
from redsentinel.application.contracts import ReportArtifacts
from redsentinel.reporting.engine.reports import (
    compute_deterministic_metrics as legacy_compute_metrics,
)
from redsentinel.reporting.engine.reports import (
    score_breakdown_from_metric_inputs as legacy_score_breakdown,
)
from redsentinel.evaluation.engine.runner.paired_evaluation import (
    build_paired_evaluation_report_skeleton as legacy_build_paired_report,
)
from redsentinel.evaluation import (
    MetricInputs,
    build_paired_evaluation_report_skeleton,
    compute_deterministic_metrics,
    evaluate_oracle,
    score_breakdown_from_metric_inputs,
)
from redsentinel.evaluation.benchmarks import evaluate_classifier, evaluate_output_filter
from redsentinel.reporting import AgentSecurityReport, write_structured_report

ROOT = Path(__file__).resolve().parents[2]
EVALUATION_ROOT = ROOT
ACCEPTANCE_MANIFEST = (
    EVALUATION_ROOT / "datasets" / "acceptance" / "detectors" / "manifest.yaml"
)


def test_report_and_metric_contracts_preserve_legacy_object_identity() -> None:
    assert AgentSecurityReport is LegacyAgentSecurityReport
    assert MetricInputs is LegacyMetricInputs


def test_legacy_benchmark_entrypoints_are_available_from_one_namespace() -> None:
    assert evaluate_classifier is legacy_evaluate_classifier
    assert evaluate_output_filter is legacy_evaluate_output_filter


def test_metric_and_score_golden_are_identical_across_namespaces() -> None:
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

    new_metrics = compute_deterministic_metrics(inputs)
    old_metrics = legacy_compute_metrics(inputs)
    new_score = score_breakdown_from_metric_inputs(inputs)
    old_score = legacy_score_breakdown(inputs)

    assert new_metrics.model_dump() == old_metrics.model_dump()
    assert new_metrics.asr == 0.25
    assert new_metrics.fpr == 0.5
    assert new_metrics.coverage_gap == 0.25
    assert new_score.model_dump() == old_score.model_dump()
    assert new_score.score == 65


def test_oracle_output_is_identical_across_namespaces() -> None:
    observation = {
        "call_type": "tool_call",
        "tool_name": "send_email",
        "arguments": {"to": "external@example.net", "body": "api_key=sk-abcdefghijklmnop"},
    }

    assert evaluate_oracle(observation).model_dump() == legacy_evaluate_oracle(observation).model_dump()


def test_paired_evaluation_golden_is_identical_across_namespaces() -> None:
    new_report = build_paired_evaluation_report_skeleton(ACCEPTANCE_MANIFEST, repo_root=EVALUATION_ROOT)
    old_report = legacy_build_paired_report(ACCEPTANCE_MANIFEST, repo_root=EVALUATION_ROOT)

    assert new_report.model_dump(mode="json") == old_report.model_dump(mode="json")


def test_structured_reporting_does_not_statically_import_dashboard_or_frontend() -> None:
    source = Path("src/redsentinel/reporting/structured.py").read_text(encoding="utf-8")
    imports = _imports(source)

    assert "redsentinel.reporting.html" not in imports
    assert all(not name.startswith("frontend") for name in imports)


def test_structured_writer_sanitizes_secrets_without_html(tmp_path: Path) -> None:
    report = AgentSecurityReport(
        tenant_id="tenant",
        agent_id="agent",
        benchmark="benchmark",
        overall_score=100,
        risk_level="low",
        summary={"api_key": "raw-secret", "masked_api_key": "raw...cret"},
        artifacts=ReportArtifacts(report_path=str(tmp_path / "report.json")),
    )

    artifacts = write_structured_report(
        report,
        json_path=tmp_path / "report.json",
        markdown_path=tmp_path / "report.md",
    )
    payload = json.loads(Path(artifacts["json"]).read_text(encoding="utf-8"))

    assert "api_key" not in payload["summary"]
    assert payload["summary"]["masked_api_key"] == "raw...cret"
    assert "raw-secret" not in Path(artifacts["markdown"]).read_text(encoding="utf-8")
    assert not (tmp_path / "report.html").exists()


def _imports(source: str) -> set[str]:
    tree = ast.parse(source)
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names
