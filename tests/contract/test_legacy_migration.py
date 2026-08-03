from __future__ import annotations

import json
from pathlib import Path

from redsentinel.migration import (
    legacy_config_to_manifest,
    migrate_legacy_artifact,
    read_legacy_artifact,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_agent_manifest_converts_to_experiment_manifest() -> None:
    manifest = legacy_config_to_manifest(
        REPO_ROOT / "examples" / "agents" / "simple_agent" / "redsentinel.yaml",
        seed=17,
    )

    assert manifest.schema_version == "experiment-manifest-v1"
    assert manifest.seeds == [17]
    assert manifest.metadata["legacy_config"]["kind"] == "agent_manifest"
    assert manifest.agent_profile_ref.startswith("legacy-agent-manifest:")
    assert "input_guard" in manifest.defense_strategy["mounted_defenses"]


def test_scenario_config_preserves_seed_and_injection() -> None:
    manifest = legacy_config_to_manifest(
        REPO_ROOT / "configs" / "scenarios" / "example-baseline.yaml"
    )

    assert manifest.experiment_id == "p1-baseline-direct-api"
    assert manifest.seeds == [42]
    assert manifest.metadata["legacy_config"]["kind"] == "scenario"
    assert manifest.attack_strategy["injection"]["mode"] == "none"


def test_product_cli_config_drops_credentials() -> None:
    manifest = legacy_config_to_manifest(REPO_ROOT / "agent_config.example.json")
    serialized = json.dumps(manifest.model_dump(mode="json"), ensure_ascii=False)

    assert manifest.metadata["legacy_config"]["kind"] == "product_cli"
    assert "YOUR_ATTACK_AGENT_API_KEY" not in serialized
    assert "api_key" not in serialized
    assert {target["id"] for target in manifest.metadata["targets"]} == {
        "ecommerce_customer_guide",
        "openmanus_official",
    }


def test_legacy_artifact_reader_detects_known_shape() -> None:
    artifact = read_legacy_artifact(REPO_ROOT / "docs" / "competition" / "evidence-pack" / "convergence.json")

    assert artifact.artifact_kind == "comp4-convergence"
    assert artifact.payload["asr_initial"] == 0.4375


def test_legacy_artifact_migration_writes_canonical_evidence(tmp_path: Path) -> None:
    evidence = migrate_legacy_artifact(
        REPO_ROOT / "docs" / "competition" / "evidence-pack" / "convergence.json",
        tmp_path,
        seed=23,
        repo_root=REPO_ROOT,
    )

    manifest = json.loads(Path(evidence.manifest_path).read_text(encoding="utf-8"))
    result = json.loads(Path(evidence.raw_result_path).read_text(encoding="utf-8"))
    index = json.loads(Path(evidence.evidence_index_path).read_text(encoding="utf-8"))
    assert manifest["seeds"] == [23]
    assert result["schema_version"] == "legacy-artifact-envelope-v1"
    assert result["artifact_kind"] == "comp4-convergence"
    assert {item["role"] for item in index["artifacts"]} >= {"manifest", "raw_result", "provenance"}
