from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any

from auto_attack_system.scripts import (
    attack_environment_awareness_pollution,
    attack_jailbreak,
    attack_training_data_leakage,
)
from auto_attack_system.threat_taxonomy import THREAT_CATEGORIES


ROOT = Path(__file__).resolve().parents[2]
SCENARIOS = {
    "jailbreak": "prompt_injection",
    "training_data_leakage": "sensitive_leakage",
    "environment_awareness_pollution": "memory_poisoning",
}
REQUIRED_FIELDS = {
    "id",
    "scenario",
    "category",
    "canonical_category",
    "payload_source",
    "attack_goal",
    "expected_violation",
    "success_criteria",
}


def test_attack_scenario_jsonl_cases_are_parseable_and_traceable() -> None:
    for scenario, canonical_category in SCENARIOS.items():
        path = ROOT / "docs" / "attack_scenarios" / scenario / "cases.jsonl"
        cases = _load_jsonl(path)

        assert len(cases) >= 2
        assert len({case["id"] for case in cases}) == len(cases)

        for case in cases:
            assert REQUIRED_FIELDS <= set(case)
            assert case["scenario"] == scenario
            assert case["category"] == scenario
            assert case["canonical_category"] == canonical_category
            assert case["canonical_category"] in THREAT_CATEGORIES
            assert case["attack_goal"].strip()
            assert case["expected_violation"].strip()
            assert isinstance(case["success_criteria"], list)
            assert all(criterion.strip() for criterion in case["success_criteria"])
            _assert_payload_source_traceable(case["payload_source"])


def test_attack_scenario_scripts_import_and_dry_run_without_asr(capsys: Any) -> None:
    scripts = [
        (attack_jailbreak, "jailbreak"),
        (attack_training_data_leakage, "training_data_leakage"),
        (attack_environment_awareness_pollution, "environment_awareness_pollution"),
    ]

    for module, scenario in scripts:
        assert module.main(["--dry-run"]) == 0
        output = json.loads(capsys.readouterr().out)
        assert output["scenario"] == scenario
        assert output["mode"] == "dry-run"
        assert output["case_count"] >= 2
        assert output["metrics"]["asr"] is None
        assert output["metrics"]["status"] == "not_evaluated"


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    assert path.exists()
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _assert_payload_source_traceable(source: dict[str, Any]) -> None:
    assert (ROOT / source["path"]).exists()
    module = importlib.import_module(source["module"])
    payloads = getattr(module, source["symbol"])
    assert source["payload_id"] in {payload["id"] for payload in payloads}
