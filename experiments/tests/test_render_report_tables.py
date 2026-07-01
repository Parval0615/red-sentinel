from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from experiments.render_report_tables import load_result, render_markdown_tables, write_svg_figures


def _sample_payload() -> dict:
    return {
        "schema_version": "asr-before-after-v0.2",
        "generated_at": "2026-07-01T00:00:00+00:00",
        "scenario_results": [
            {
                "scenario": "prompt_injection",
                "cases_total": 4,
                "benign_cases_total": 2,
                "asr_no_defense": 0.75,
                "asr_with_defense": 0.25,
                "fpr": 0.0,
                "blocked": 2,
                "asked": 1,
                "false_positives": 0,
                "decision_distribution": {"allow": 2, "deny": 1, "ask": 1},
                "benign_decision_distribution": {"allow": 2, "deny": 0, "ask": 0},
            },
            {
                "scenario": "tool_tampering",
                "cases_total": 2,
                "benign_cases_total": 10,
                "asr_no_defense": 1.0,
                "asr_with_defense": 0.5,
                "fpr": 0.1,
                "blocked": 1,
                "asked": 0,
                "false_positives": 1,
                "decision_distribution": {"allow": 1, "deny": 1, "ask": 0},
                "benign_decision_distribution": {"allow": 9, "deny": 1, "ask": 0},
            },
        ],
        "summary": {
            "cases_total": 6,
            "benign_cases_total": 12,
            "asr_no_defense": 0.8333,
            "asr_with_defense": 0.3333,
            "fpr": 0.0833,
            "blocked": 3,
            "asked": 1,
            "false_positives": 1,
            "decision_distribution": {"allow": 3, "deny": 2, "ask": 1},
            "benign_decision_distribution": {"allow": 11, "deny": 1, "ask": 0},
        },
    }


def test_render_markdown_tables_contains_required_columns_and_delta(tmp_path: Path) -> None:
    input_path = tmp_path / "asr_before_after.json"
    input_path.write_text(json.dumps(_sample_payload()), encoding="utf-8")

    markdown = render_markdown_tables(load_result(input_path))

    assert "| scenario | cases_total | asr_no_defense | asr_with_defense | delta | fpr | blocked | asked |" in markdown
    assert "| `prompt_injection` | 4 | 75.0% | 25.0% | 50.0% | 0.0% | 2 | 1 |" in markdown
    assert "| `tool_tampering` | 2 | 100.0% | 50.0% | 50.0% | 10.0% | 1 | 0 |" in markdown
    assert "| `summary` | 6 | 83.3% | 33.3% | 50.0% | 8.3% | 3 | 1 |" in markdown


def test_render_markdown_tables_contains_fpr_and_decision_distribution_tables(tmp_path: Path) -> None:
    input_path = tmp_path / "asr_before_after.json"
    input_path.write_text(json.dumps(_sample_payload()), encoding="utf-8")

    markdown = render_markdown_tables(load_result(input_path))

    assert "## FPR Distribution" in markdown
    assert "| scope | benign_cases_total | false_positives | fpr | benign_allow | benign_deny | benign_ask |" in markdown
    assert "| `tool_tampering` | 10 | 1 | 10.0% | 9 | 1 | 0 |" in markdown
    assert "| `summary` | 12 | 1 | 8.3% | 11 | 1 | 0 |" in markdown
    assert "## Asked/Decision Distribution" in markdown
    assert "| scope | cases_total | allow | deny | ask | blocked | asked | asr_with_defense |" in markdown
    assert "| `prompt_injection` | 4 | 2 | 1 | 1 | 2 | 1 | 25.0% |" in markdown
    assert "| `summary` | 6 | 3 | 2 | 1 | 3 | 1 | 33.3% |" in markdown


def test_write_svg_figures_outputs_reproducible_fallback_assets(tmp_path: Path) -> None:
    figure_paths = write_svg_figures(_sample_payload(), tmp_path)

    assert set(figure_paths) == {"asr_comparison", "attack_radar"}
    for path in figure_paths.values():
        content = path.read_text(encoding="utf-8")
        assert path.suffix == ".svg"
        assert content.startswith("<svg ")
        assert "</svg>" in content
