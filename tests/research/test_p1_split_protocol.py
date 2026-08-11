from __future__ import annotations

import json
from pathlib import Path

import pytest

from redsentinel.datasets import DatasetIntegrityError, load_p1_experiment_split


REPO_ROOT = Path(__file__).resolve().parents[2]
SPLIT_PATH = REPO_ROOT / "datasets" / "splits" / "p1-split-v2.json"
ARCHIVED_SPLIT_PATH = REPO_ROOT / "datasets" / "splits" / "p1-split-v1.json"


def test_p1_split_is_pinned_complete_and_lineage_disjoint() -> None:
    split = load_p1_experiment_split(SPLIT_PATH, repo_root=REPO_ROOT)

    assert split.version == "v2.0"
    development = {item.payload_lineage for item in split.assignments if item.split == "development"}
    holdout = {item.payload_lineage for item in split.assignments if item.split == "holdout"}
    assert len(split.assignments) == 6
    assert len(development) == 4
    assert len(holdout) == 2
    assert development.isdisjoint(holdout)
    assert {item.pair_id for item in split.assignments} == {
        "py-exec-rce",
        "file-op-path-traversal",
        "prompt-injection-ignore",
        "exfil-via-email",
        "browser-ssrf",
        "jailbreak-roleplay",
    }


def test_archived_p1_split_remains_loadable() -> None:
    split = load_p1_experiment_split(ARCHIVED_SPLIT_PATH, repo_root=REPO_ROOT)

    assert split.version == "v1.0"


def test_p1_split_rejects_source_hash_drift(tmp_path: Path) -> None:
    payload = json.loads(SPLIT_PATH.read_text(encoding="utf-8"))
    payload["source_sha256"] = "0" * 64
    path = tmp_path / "split.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(DatasetIntegrityError, match="hash mismatch"):
        load_p1_experiment_split(path, repo_root=REPO_ROOT)


def test_p1_split_rejects_payload_lineage_leakage(tmp_path: Path) -> None:
    payload = json.loads(SPLIT_PATH.read_text(encoding="utf-8"))
    payload["assignments"][-1]["payload_lineage"] = payload["assignments"][0]["payload_lineage"]
    path = tmp_path / "split.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(DatasetIntegrityError, match="payload lineage"):
        load_p1_experiment_split(path, repo_root=REPO_ROOT)


def test_p1_split_rejects_assignment_drift_from_benchmark(tmp_path: Path) -> None:
    payload = json.loads(SPLIT_PATH.read_text(encoding="utf-8"))
    payload["assignments"][0]["business_flow"] = "changed_after_freeze"
    path = tmp_path / "split.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(DatasetIntegrityError, match="does not match source benchmark"):
        load_p1_experiment_split(path, repo_root=REPO_ROOT)
