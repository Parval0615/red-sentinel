from __future__ import annotations

from pathlib import Path

from redsentinel.profiling.manifest import load_agent_config as legacy_load_agent_config
from redsentinel.profiling.builder import build_agent_security_profile as legacy_build_profile
from redsentinel.profiling import analyze_source_profile as legacy_analyze_source_profile
from redsentinel.profiling import (
    analyze_source_profile,
    build_agent_security_profile,
    load_agent_config,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
SIMPLE_CONFIG = REPO_ROOT / "examples" / "agents" / "simple_agent" / "redsentinel.yaml"
OPENMANUS_FIXTURE = REPO_ROOT / "examples" / "agents" / "openmanus_agent"


def test_simple_manifest_and_profile_are_equivalent_across_import_paths() -> None:
    canonical_config = load_agent_config(SIMPLE_CONFIG)
    legacy_config = legacy_load_agent_config(SIMPLE_CONFIG)

    canonical_profile = build_agent_security_profile(canonical_config)
    legacy_profile = legacy_build_profile(legacy_config)

    assert canonical_config.model_dump(mode="json") == legacy_config.model_dump(mode="json")
    assert canonical_profile.model_dump(mode="json") == legacy_profile.model_dump(mode="json")


def test_openmanus_fixture_candidate_is_equivalent_across_import_paths() -> None:
    canonical = analyze_source_profile(OPENMANUS_FIXTURE)
    legacy = legacy_analyze_source_profile(OPENMANUS_FIXTURE)

    assert canonical.model_dump(mode="json") == legacy.model_dump(mode="json")
    assert canonical.diff.evidence_refs


def test_llm_patch_without_ast_evidence_cannot_override_input_profile() -> None:
    base_profile = build_agent_security_profile(load_agent_config(SIMPLE_CONFIG))

    class UnsupportedOverrideClient:
        model = "unsupported-override"

        def complete_json(self, _messages):
            return {
                "agent_name": "llm-overridden-agent",
                "nodes": [],
                "tools": [],
                "rag": None,
                "memory": None,
                "warnings": [],
            }

    result = analyze_source_profile(
        SIMPLE_CONFIG.parent,
        base_profile,
        enable_llm=True,
        llm_client=UnsupportedOverrideClient(),
    )

    assert result.source == "ast_baseline_fallback"
    assert result.failed_safe is True
    assert result.candidate_profile.agent_name == base_profile.agent_name
    assert result.candidate_profile.entrypoint == base_profile.entrypoint
