from __future__ import annotations

import argparse
import importlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence


ROOT = Path(__file__).resolve().parents[4]
REQUIRED_CASE_FIELDS = {
    "id",
    "scenario",
    "category",
    "canonical_category",
    "payload_id",
    "payload_source",
    "attack_goal",
    "expected_violation",
    "success_criteria",
    "script_entry",
}


@dataclass(frozen=True)
class ScenarioConfig:
    scenario: str
    case_path: Path


def run_scenario_cli(config: ScenarioConfig, argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=f"{config.scenario} attack scenario runner")
    parser.add_argument("--dry-run", action="store_true", help="Validate and preview cases without calling a target model")
    parser.add_argument("--cases", type=Path, default=config.case_path, help="Override the scenario cases JSONL path")
    args = parser.parse_args(argv)

    if not args.dry_run:
        parser.error("live attack execution requires an explicit target runner; use --dry-run for offline validation")

    cases = load_cases(args.cases)
    summary = {
        "scenario": config.scenario,
        "mode": "dry-run",
        "cases_path": str(args.cases),
        "case_count": len(cases),
        "case_ids": [case["id"] for case in cases],
        "payload_ids": [case["payload_id"] for case in cases],
        "metrics": {
            "asr": None,
            "status": "not_evaluated",
            "reason": "dry-run validates case metadata only and does not call a target model",
        },
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def load_cases(path: Path) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            if not line.strip():
                continue
            try:
                case = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_number}: invalid JSONL record: {exc.msg}") from exc
            validate_case(case, path, line_number)
            cases.append(case)

    if not cases:
        raise ValueError(f"{path}: no JSONL cases found")
    return cases


def validate_case(case: dict[str, Any], path: Path, line_number: int) -> None:
    missing = REQUIRED_CASE_FIELDS - set(case)
    if missing:
        raise ValueError(f"{path}:{line_number}: missing required fields: {sorted(missing)}")
    if not isinstance(case["success_criteria"], list) or not case["success_criteria"]:
        raise ValueError(f"{path}:{line_number}: success_criteria must be a non-empty list")

    source = case["payload_source"]
    for field in ("module", "symbol", "path", "payload_id"):
        if field not in source:
            raise ValueError(f"{path}:{line_number}: payload_source missing {field}")
    if case["payload_id"] != source["payload_id"]:
        raise ValueError(f"{path}:{line_number}: payload_id does not match payload_source")
    if not isinstance(case["script_entry"], str) or not case["script_entry"].strip():
        raise ValueError(f"{path}:{line_number}: script_entry must be a non-empty string")
    if not (ROOT / source["path"]).exists():
        raise ValueError(f"{path}:{line_number}: payload source path does not exist: {source['path']}")

    module = importlib.import_module(source["module"])
    payloads = getattr(module, source["symbol"])
    payload_ids = {payload["id"] for payload in payloads}
    if source["payload_id"] not in payload_ids:
        raise ValueError(f"{path}:{line_number}: unknown payload_id: {source['payload_id']}")
