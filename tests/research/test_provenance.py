from __future__ import annotations

import json
from pathlib import Path

import pytest

from redsentinel.core.models import ExperimentManifest
from redsentinel.research.provenance import capture_provenance, write_evidence_index


def _manifest(**updates) -> ExperimentManifest:
    values = {
        "experiment_id": "provenance-fixture",
        "research_question": "Can every claim be reproduced?",
        "agent_profile_ref": "fixture-profile.json",
        "dataset_refs": ["fixture-data"],
        "attack_strategy": {"name": "fixed"},
        "defense_strategy": {"name": "fixed"},
        "metric_names": ["asr"],
        "seeds": [7],
        "execution_mode": "external_model",
        "metadata": {
            "external_model": {
                "provider": "openai-compatible",
                "model": "fixture-model",
                "temperature": 0,
                "parameters": {"max_tokens": 128},
                "cache_policy": "read_write_v1",
            }
        },
    }
    values.update(updates)
    return ExperimentManifest(**values)


def test_capture_provenance_records_code_config_data_environment_and_model(tmp_path: Path) -> None:
    dataset = tmp_path / "cases.jsonl"
    dataset.write_text('{"id":"case-1"}\n', encoding="utf-8")

    provenance = capture_provenance(
        _manifest(),
        repo_root=Path(__file__).resolve().parents[2],
        dataset_paths={"fixture-data": dataset},
    )

    assert provenance.git_commit
    assert isinstance(provenance.git_dirty, bool)
    assert len(provenance.config_sha256) == 64
    assert len(provenance.dataset_sha256["fixture-data"]) == 64
    assert provenance.python_version
    assert "pydantic" in provenance.dependency_versions
    assert provenance.external_model == {
        "cache_policy": "read_write_v1",
        "model": "fixture-model",
        "parameters": {"max_tokens": 128},
        "provider": "openai-compatible",
        "temperature": 0,
    }


def test_capture_provenance_rejects_secret_fields_at_any_depth(tmp_path: Path) -> None:
    dataset = tmp_path / "cases.jsonl"
    dataset.write_text("{}\n", encoding="utf-8")
    manifest = _manifest()
    manifest.metadata["external_model"]["parameters"]["api_key"] = "must-not-be-recorded"

    with pytest.raises(ValueError, match="secret-like field"):
        capture_provenance(
            manifest,
            repo_root=Path(__file__).resolve().parents[2],
            dataset_paths={"fixture-data": dataset},
        )


def test_evidence_index_links_figures_to_manifest_and_raw_result(tmp_path: Path) -> None:
    experiment_dir = tmp_path / "experiment"
    experiment_dir.mkdir()
    manifest = experiment_dir / "experiment-manifest-v1.json"
    result = experiment_dir / "experiment-run-v1.json"
    provenance = experiment_dir / "provenance-v1.json"
    figure = experiment_dir / "figures" / "convergence.svg"
    figure.parent.mkdir()
    manifest.write_text("{}\n", encoding="utf-8")
    result.write_text("{}\n", encoding="utf-8")
    provenance.write_text("{}\n", encoding="utf-8")
    figure.write_text("<svg></svg>\n", encoding="utf-8")

    index_path = write_evidence_index(
        experiment_id="provenance-fixture",
        experiment_dir=experiment_dir,
        manifest_path=manifest,
        raw_result_path=result,
        provenance_path=provenance,
    )
    payload = json.loads(index_path.read_text(encoding="utf-8"))
    figure_entry = next(item for item in payload["artifacts"] if item["path"] == str(figure))

    assert figure_entry["role"] == "figure"
    assert figure_entry["manifest_path"] == str(manifest)
    assert figure_entry["raw_result_path"] == str(result)
    assert len(figure_entry["sha256"]) == 64
