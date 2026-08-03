from __future__ import annotations

import hashlib
import json
import shlex
import subprocess
import sys
from pathlib import Path

import pytest

from redsentinel.datasets import (
    DatasetIntegrityError,
    assign_split,
    load_dataset_manifest,
    load_jsonl_split,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
MANIFEST_ROOT = REPO_ROOT / "datasets" / "manifests"


@pytest.mark.parametrize(
    "name,dataset_id",
    [
        ("attack-cases-v1.json", "redsentinel-attack-cases"),
        ("benign-cases-v1.json", "redsentinel-benign-cases"),
        ("trajectory-fixtures-v1.json", "redsentinel-trajectory-fixtures"),
        ("benchmarks-v1.json", "redsentinel-benchmarks"),
    ],
)
def test_governed_datasets_have_verified_manifests(name: str, dataset_id: str) -> None:
    manifest = load_dataset_manifest(MANIFEST_ROOT / name, repo_root=REPO_ROOT, expected_version="v1.0")

    assert manifest.dataset_id == dataset_id
    assert manifest.license
    assert manifest.source
    assert manifest.labels
    assert manifest.validation_command
    assert manifest.split_policy.names == ("development", "holdout")


def test_attack_dataset_declares_runnable_generation_commands() -> None:
    manifest = load_dataset_manifest(MANIFEST_ROOT / "attack-cases-v1.json", repo_root=REPO_ROOT)

    assert manifest.generation == "generated"
    assert manifest.generation_seed == 2026
    assert manifest.generator and "--dry-run" in manifest.generator and "--seed 2026" in manifest.generator
    assert manifest.write_command and "--write" in manifest.write_command and "--seed 2026" in manifest.write_command
    result = _run_manifest_command(manifest.generator)
    summary = json.loads(result.stdout)
    assert summary["mode"] == "dry-run"
    assert summary["seed"] == manifest.generation_seed
    assert summary["scenario_count"] == 7


@pytest.mark.parametrize(
    "name",
    [
        "attack-cases-v1.json",
        "benign-cases-v1.json",
        "trajectory-fixtures-v1.json",
        "benchmarks-v1.json",
    ],
)
def test_manifest_validation_commands_execute_and_preserve_hashes(name: str) -> None:
    path = MANIFEST_ROOT / name
    manifest = load_dataset_manifest(path, repo_root=REPO_ROOT)

    result = _run_manifest_command(manifest.validation_command)
    summary = json.loads(result.stdout)
    assert summary == {
        "dataset_id": manifest.dataset_id,
        "file_count": len(manifest.files),
        "generation": manifest.generation,
        "status": "verified",
        "version": manifest.version,
    }
    load_dataset_manifest(path, repo_root=REPO_ROOT, expected_version=manifest.version)


@pytest.mark.parametrize(
    "name",
    ["benign-cases-v1.json", "trajectory-fixtures-v1.json", "benchmarks-v1.json"],
)
def test_authored_fixtures_do_not_claim_generator_commands(name: str) -> None:
    manifest = load_dataset_manifest(MANIFEST_ROOT / name, repo_root=REPO_ROOT)

    assert manifest.generation == "frozen_authored"
    assert manifest.generation_seed is None
    assert manifest.generator is None
    assert manifest.write_command is None


def test_attack_source_groups_do_not_cross_development_and_holdout() -> None:
    path = MANIFEST_ROOT / "attack-cases-v1.json"
    manifest = load_dataset_manifest(path, repo_root=REPO_ROOT)
    development = load_jsonl_split(path, "development", repo_root=REPO_ROOT)
    holdout = load_jsonl_split(path, "holdout", repo_root=REPO_ROOT)

    def groups(records: list[dict]) -> set[tuple[str, str]]:
        return {
            (record["payload_source"]["path"], record["payload_subcategory"])
            for record in records
        }

    assert development
    assert holdout
    assert groups(development).isdisjoint(groups(holdout))
    assert all(assign_split(record, manifest.split_policy) == "development" for record in development)
    assert all(assign_split(record, manifest.split_policy) == "holdout" for record in holdout)


def test_loader_rejects_version_mismatch() -> None:
    with pytest.raises(DatasetIntegrityError, match="version mismatch"):
        load_dataset_manifest(
            MANIFEST_ROOT / "attack-cases-v1.json",
            repo_root=REPO_ROOT,
            expected_version="v2.0",
        )


def test_loader_rejects_content_hash_mismatch(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text("", encoding="utf-8")
    data_path = tmp_path / "data.jsonl"
    data_path.write_text('{"id":"case-1","family":"same-source"}\n', encoding="utf-8")
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "schema_version": "dataset-manifest-v1",
                "dataset_id": "tampered-fixture",
                "version": "v1.0",
                "description": "Integrity test fixture.",
                "source": ["test"],
                "license": "Apache-2.0",
                "labels": ["family"],
                "generation": "frozen_authored",
                "validation_command": "python -m redsentinel.datasets.verify manifest.json --repo-root .",
                "files": [
                    {
                        "path": "data.jsonl",
                        "sha256": hashlib.sha256(data_path.read_bytes()).hexdigest(),
                        "format": "jsonl",
                    }
                ],
                "split_policy": {
                    "names": ["development", "holdout"],
                    "group_by": ["family"],
                    "seed": 1,
                    "holdout_fraction": 0.2,
                },
            }
        ),
        encoding="utf-8",
    )
    data_path.write_text('{"id":"case-1","family":"modified"}\n', encoding="utf-8")

    with pytest.raises(DatasetIntegrityError, match="hash mismatch"):
        load_dataset_manifest(manifest_path, repo_root=tmp_path)


def test_split_assignment_requires_declared_provenance_group() -> None:
    manifest = load_dataset_manifest(MANIFEST_ROOT / "attack-cases-v1.json", repo_root=REPO_ROOT)

    with pytest.raises(DatasetIntegrityError, match="payload_source.path"):
        assign_split({"payload_subcategory": "variant"}, manifest.split_policy)


def _run_manifest_command(command: str) -> subprocess.CompletedProcess[str]:
    argv = shlex.split(command)
    argv[0] = sys.executable
    return subprocess.run(
        argv,
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
