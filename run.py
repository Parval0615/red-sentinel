from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent
SOURCE_DIRS = (
    "auto_attack_system/src",
    "auto_defense_system/src",
    "auto_evaluation_system/src",
)


def main() -> int:
    args = _parse_args()
    repo_root = REPO_ROOT
    _add_source_paths(repo_root)

    from auto_evaluation_system.runner import run_closed_loop_evaluation

    results_root = _resolve_results_root(repo_root, args.results_root)
    scenario_manifest = repo_root / "auto_evaluation_system" / "configs" / "scenarios" / "manifest.yaml"
    acceptance_manifest = repo_root / "auto_evaluation_system" / "datasets" / "acceptance" / "detectors" / "manifest.yaml"

    report = run_closed_loop_evaluation(
        scenario_manifest,
        acceptance_manifest,
        repo_root=repo_root,
        results_root=results_root,
    )

    _print_summary(report)
    return 0 if all(record.passed for record in report.records) else 1


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the deterministic offline Attack -> Defense -> Evaluation closed-loop experiment.",
    )
    parser.add_argument(
        "--results-root",
        type=Path,
        default=None,
        help="Directory for generated runs and closed-loop-report-v0.1.json. Defaults to runs/closed-loop-<timestamp>.",
    )
    return parser.parse_args()


def _add_source_paths(repo_root: Path) -> None:
    for rel_path in reversed(SOURCE_DIRS):
        source_path = str(repo_root / rel_path)
        if source_path not in sys.path:
            sys.path.insert(0, source_path)


def _default_results_root(repo_root: Path) -> Path:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return repo_root / "runs" / f"closed-loop-{stamp}"


def _resolve_results_root(repo_root: Path, requested: Path | None) -> Path:
    if requested is None:
        return _default_results_root(repo_root)
    if requested.is_absolute():
        return requested
    return repo_root / requested


def _print_summary(report) -> None:
    print(f"REPORT_PATH={report.metadata['report_path']}")
    print(f"SCHEMA={report.schema_version}")
    print(f"RECORDS={len(report.records)}")

    for record in report.records:
        print(
            f"{record.pair_id} | "
            f"risk={record.risk_type} | "
            f"metric={record.metric} | "
            f"detector={record.detector_output.decision} | "
            f"clean={record.clean_defense_decision.decision} | "
            f"controlled={record.controlled_defense_decision.decision} | "
            f"audit={record.audit_integrity.valid} | "
            f"passed={record.passed}"
        )
        if record.failure_notes:
            for note in record.failure_notes:
                print(f"  failure: {note}")


if __name__ == "__main__":
    raise SystemExit(main())
