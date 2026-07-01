from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any

from auto_attack_system.threat_taxonomy import THREAT_CATEGORIES


ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = ROOT / "auto_attack_system" / "datasets" / "manifest.json"
REQUIRED_FIELDS = {
    "id",
    "category",
    "source_payload",
    "attack_goal",
    "expected_violation",
    "success_criteria",
    "script_entry",
}


def test_attack_dataset_manifest_is_complete_and_traceable() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    records = manifest["records"]

    ids = [record["id"] for record in records]
    assert len(ids) == len(set(ids))
    assert {record["category"] for record in records} == set(THREAT_CATEGORIES)

    for record in records:
        assert REQUIRED_FIELDS <= set(record)
        assert record["category"] in THREAT_CATEGORIES
        assert record["attack_goal"].strip()
        assert record["expected_violation"].strip()
        assert record["success_criteria"]

        _assert_source_payload_traceable(record["source_payload"])
        _assert_script_entry_traceable(record["script_entry"])


def _assert_source_payload_traceable(source: dict[str, Any]) -> None:
    assert (ROOT / source["path"]).exists()

    module = importlib.import_module(source["module"])
    payload_source = getattr(module, source["symbol"])

    if "payload_ids" in source:
        existing_ids = {item["id"] for item in payload_source}
        assert set(source["payload_ids"]) <= existing_ids
        return

    category_key = source["category_key"]
    strategies = payload_source[category_key]
    existing_strategy_names = {strategy.name for strategy in strategies}
    assert set(source["strategy_names"]) <= existing_strategy_names


def _assert_script_entry_traceable(script_entry: dict[str, Any]) -> None:
    assert script_entry["entry"].strip()
    assert (ROOT / script_entry["path"]).exists()
