from __future__ import annotations

import json
from pathlib import Path

import pytest

from redsentinel.research.analysis import analyze_files, render_paper_tables, write_analysis_artifacts
from redsentinel.research.analysis_cli import main


def _write_comparison(
    root: Path,
    *,
    seed: int,
    fixed_asr: float,
    coevolution_asr: float,
    ablated: bool = False,
) -> Path:
    path = root / f"seed-{seed}-{'ablated' if ablated else 'full'}.json"
    payload = {
        "schema_version": "baseline-comparison-v1",
        "experiment_id": "rq2-fixture",
        "seed": seed,
        "ablations": {
            "profile": not ablated,
            "trajectory_anomaly": True,
            "node_attribution": True,
            "reflection": True,
            "utility_constraints": True,
        },
        "results": [
            _arm("fixed", fixed_asr, 0.92),
            _arm("coevolution", coevolution_asr, 0.88),
        ],
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _arm(name: str, asr: float, utility: float) -> dict:
    return {
        "name": name,
        "final_metrics": {"asr": asr, "utility": utility},
        "run": {
            "rounds": [
                {
                    "round_index": 0,
                    "regression_evaluation": {"metrics": {"asr": min(asr + 0.2, 1.0), "utility": utility}},
                },
                {
                    "round_index": 1,
                    "regression_evaluation": {"metrics": {"asr": asr, "utility": utility}},
                },
            ]
        },
    }


def test_analysis_aggregates_multi_seed_statistics_and_paired_effect(tmp_path: Path) -> None:
    paths = [
        _write_comparison(tmp_path, seed=1, fixed_asr=0.8, coevolution_asr=0.4),
        _write_comparison(tmp_path, seed=2, fixed_asr=0.7, coevolution_asr=0.5),
        _write_comparison(tmp_path, seed=3, fixed_asr=0.9, coevolution_asr=0.3),
    ]

    analysis = analyze_files(paths)
    fixed = next(
        item for item in analysis.summaries
        if item.arm == "fixed" and item.metric == "asr" and item.ablation == "full"
    )
    test = next(item for item in analysis.significance_tests if item.metric == "asr")

    assert fixed.count == 3
    assert fixed.mean == pytest.approx(0.8)
    assert fixed.variance == pytest.approx(0.01)
    assert fixed.standard_deviation == pytest.approx(0.1)
    assert fixed.confidence_interval == pytest.approx((0.551566, 1.048434), abs=1e-5)
    assert test.status == "computed"
    assert test.paired_seeds == [1, 2, 3]
    assert test.mean_difference == pytest.approx(-0.4)
    assert test.effect_size_cohens_dz == pytest.approx(-2.0)
    assert test.p_value_two_sided == pytest.approx(0.25)
    assert "exchangeable paired differences" in " ".join(test.assumptions)


def test_analysis_marks_significance_not_applicable_for_one_seed(tmp_path: Path) -> None:
    analysis = analyze_files([_write_comparison(tmp_path, seed=7, fixed_asr=0.8, coevolution_asr=0.4)])

    result = next(item for item in analysis.significance_tests if item.metric == "asr")

    assert result.status == "not_applicable"
    assert result.p_value_two_sided is None
    assert result.reason == "at least two paired seeds are required"


def test_tables_and_svg_figures_trace_every_number_to_raw_json(tmp_path: Path) -> None:
    source = _write_comparison(tmp_path, seed=11, fixed_asr=0.75, coevolution_asr=0.25)
    ablation = _write_comparison(
        tmp_path,
        seed=11,
        fixed_asr=0.85,
        coevolution_asr=0.55,
        ablated=True,
    )
    analysis = analyze_files([source, ablation])

    artifacts = write_analysis_artifacts(analysis, tmp_path / "paper", prefer_matplotlib=False)
    markdown = artifacts["tables"].read_text(encoding="utf-8")
    analysis_payload = json.loads(artifacts["analysis"].read_text(encoding="utf-8"))

    assert str(source) in markdown
    assert "/results/0/final_metrics/asr" in markdown
    assert analysis_payload["observations"]
    assert all(item["source"]["sha256"] for item in analysis_payload["observations"])
    for name in ("convergence", "pareto", "ablation"):
        svg = artifacts[name].read_text(encoding="utf-8")
        assert "<metadata>" in svg
        assert str(source) in svg


def test_experiment_run_schema_is_supported(tmp_path: Path) -> None:
    source = tmp_path / "experiment.json"
    source.write_text(
        json.dumps(
            {
                "schema_version": "experiment-run-v1",
                "experiment_id": "rq1-fixture",
                "records": [
                    {
                        "seed": 13,
                        "status": "completed",
                        "evaluation": {"metrics": {"coverage": 0.8}},
                    },
                    {
                        "seed": 17,
                        "status": "failed",
                        "evaluation": None,
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    analysis = analyze_files([source])

    assert len(analysis.observations) == 1
    assert analysis.summaries[0].metric == "coverage"
    assert analysis.summaries[0].confidence_interval is None
    assert not analysis.significance_tests


def test_cli_writes_traceable_artifacts(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    source = _write_comparison(tmp_path, seed=19, fixed_asr=0.7, coevolution_asr=0.2)
    output = tmp_path / "output"

    assert main([str(source), "--output-dir", str(output), "--svg"]) == 0

    stdout = capsys.readouterr().out
    assert "ANALYSIS=" in stdout
    assert (output / "analysis.json").exists()
    assert (output / "paper-tables.md").exists()
    assert (output / "convergence.svg").exists()


def test_matplotlib_figures_embed_raw_source_metadata(tmp_path: Path) -> None:
    pytest.importorskip("matplotlib")
    source = _write_comparison(tmp_path, seed=23, fixed_asr=0.7, coevolution_asr=0.2)

    artifacts = write_analysis_artifacts(analyze_files([source]), tmp_path / "png")

    for name in ("convergence", "pareto", "ablation"):
        assert artifacts[name].suffix == ".png"
        assert str(source).encode() in artifacts[name].read_bytes()


def test_unsupported_schema_and_non_finite_metric_are_rejected(tmp_path: Path) -> None:
    unsupported = tmp_path / "unsupported.json"
    unsupported.write_text('{"schema_version":"unknown"}', encoding="utf-8")
    with pytest.raises(ValueError, match="Unsupported"):
        analyze_files([unsupported])

    invalid = _write_comparison(tmp_path, seed=1, fixed_asr=0.8, coevolution_asr=0.4)
    payload = json.loads(invalid.read_text(encoding="utf-8"))
    payload["results"][0]["final_metrics"]["asr"] = float("nan")
    invalid.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="finite"):
        analyze_files([invalid])


def test_rendered_table_records_test_assumptions(tmp_path: Path) -> None:
    paths = [
        _write_comparison(tmp_path, seed=1, fixed_asr=0.8, coevolution_asr=0.4),
        _write_comparison(tmp_path, seed=2, fixed_asr=0.7, coevolution_asr=0.5),
    ]

    markdown = render_paper_tables(analyze_files(paths))

    assert "paired_sign_flip_permutation" in markdown
    assert "observations are paired by identical seed" in markdown
    assert "Cohen dz" in markdown
