from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

from redsentinel.attacks.engine.attack_spec import AttackSpec
from redsentinel.core.agent_security import AgentProfile as LegacyAgentProfile
from redsentinel.core import (
    AgentProfile,
    AttackCandidate,
    DefenseCandidate,
    EvaluationCaseResult,
    EvaluationResult,
    EvidenceRef,
    EvolutionState,
    ExperimentManifest,
    Provenance,
    Trajectory,
    TrajectoryStep,
    agent_profile_from_legacy,
)

SHA256 = "a" * 64


def _profile_payload() -> dict:
    return {
        "schema_version": "agent-profile-v1",
        "agent_name": "research_agent",
        "framework": "python_function",
        "root_path": ".",
        "entrypoint": "agent:run",
        "business_domain": "research",
        "nodes": [
            {
                "id": "input",
                "type": "input_node",
                "target": "agent:run",
                "risk_surfaces": ["prompt_injection"],
                "defenses": ["input_guard"],
            }
        ],
        "tools": [],
        "attack_entries": ["prompt"],
        "sensitive_data": [],
        "rag_enabled": False,
    }


def _provenance() -> Provenance:
    return Provenance(
        git_commit="0123456789abcdef",
        git_dirty=False,
        python_version="3.10.14",
        dependency_versions={"pydantic": "2"},
        config_sha256=SHA256,
        dataset_sha256={"cases": "b" * 64},
        execution_mode="offline_fixture",
    )


def test_agent_profile_reuses_legacy_v1_contract_without_payload_drift() -> None:
    payload = _profile_payload()

    core_profile = AgentProfile.model_validate(payload)
    legacy_profile = LegacyAgentProfile.model_validate(payload)

    assert LegacyAgentProfile is AgentProfile
    assert core_profile.profile_id == legacy_profile.profile_id
    assert core_profile.profile_id.startswith("profile_")
    assert core_profile.model_dump(mode="json", exclude={"profile_id", "evidence_refs"}) == payload


def test_agent_profile_identity_is_stable_and_evidence_is_structured() -> None:
    payload = _profile_payload()
    payload["evidence_refs"] = [
        {
            "ref": "agent.py",
            "kind": "source",
            "locator": {"line_start": 1, "line_end": 20},
        }
    ]

    first = AgentProfile.model_validate(payload)
    second = AgentProfile.model_validate(payload)
    restored = AgentProfile.model_validate_json(first.model_dump_json())

    assert first.profile_id == second.profile_id == restored.profile_id
    assert restored.evidence_refs[0].kind == "source"
    assert restored.evidence_refs[0].locator["line_start"] == 1


def test_legacy_profile_converter_accepts_v1_model_and_payload() -> None:
    legacy = LegacyAgentProfile.model_validate(_profile_payload())

    from_model = agent_profile_from_legacy(legacy)
    from_payload = agent_profile_from_legacy(_profile_payload())

    assert from_model == from_payload
    assert from_model.profile_id.startswith("profile_")


def test_core_models_round_trip_with_explicit_versions() -> None:
    evidence = EvidenceRef(ref="runs/trajectory.json#steps/0", kind="trajectory", sha256=SHA256)
    attack = AttackCandidate(
        candidate_id="attack-001",
        source="authored_fixture",
        risk_type="prompt_injection",
        strategy="instruction_override",
        intensity="medium",
        target="input",
        goal="Cause instruction hierarchy violation.",
        success_criteria=["unsafe instruction accepted"],
        evidence_refs=[evidence],
    )
    defense = DefenseCandidate(
        candidate_id="defense-001",
        agent_name="research_agent",
        target_node_ids=["input"],
        actions=[{"type": "add_defense", "name": "input_guard"}],
        utility_constraints={"minimum_clean_allow_rate": 0.95},
        evidence_refs=[evidence],
    )
    trajectory = Trajectory(
        session_id="session-001",
        experiment_id="experiment-001",
        seed=7,
        framework="direct_api",
        steps=[
            TrajectoryStep(
                step_index=0,
                step_type="llm_inference",
                timestamp="2026-08-01T00:00:00Z",
                llm={"model": "fixture", "input_messages": []},
            )
        ],
    )
    result = EvaluationResult(
        result_id="result-001",
        experiment_id="experiment-001",
        agent_profile_ref="profiles/research-agent.json",
        cases=[
            EvaluationCaseResult(
                case_id="case-001",
                case_type="attack",
                target_node="input",
                expected_decision="block",
                actual_decision="block",
                passed=True,
                trajectory_ref="runs/trajectory.json",
            )
        ],
        metrics={"asr": 0.0, "fpr": 0.0},
        evidence_refs=[evidence],
    )
    state = EvolutionState(
        experiment_id="experiment-001",
        stage="evaluation",
        attack_population=[attack],
        defense_population=[defense],
        evaluation_refs=["runs/result.json"],
    )
    manifest = ExperimentManifest(
        experiment_id="experiment-001",
        research_question="RQ2",
        agent_profile_ref="profiles/research-agent.json",
        dataset_refs=["datasets/cases.jsonl"],
        attack_strategy={"name": "evidence_guided"},
        defense_strategy={"name": "utility_constrained"},
        metric_names=["asr", "fpr"],
        seeds=[7, 11],
        repetitions=2,
        budget={"max_rounds": 5},
        execution_mode="offline_fixture",
        provenance=_provenance(),
    )

    models = [evidence, attack, defense, trajectory, result, state, manifest]
    restored = [type(model).model_validate_json(model.model_dump_json()) for model in models]

    assert restored == models
    assert {model.schema_version for model in models} == {
        "evidence-ref-v1",
        "attack-candidate-v1",
        "defense-candidate-v1",
        "1.0",
        "evaluation-result-v1",
        "evolution-state-v1",
        "experiment-manifest-v1",
    }


def test_explicit_legacy_converters_preserve_source_meaning() -> None:
    attack_spec = AttackSpec(
        attack_id="legacy-attack-001",
        risk_type="prompt_injection",
        strategy="override",
        intensity="medium",
        target="input",
        label="controlled",
        goal="Override instructions.",
        success_criteria=["override accepted"],
        metadata={"seed": 7},
    )

    attack = AttackCandidate.from_attack_spec(attack_spec)
    evidence = EvidenceRef.from_legacy_source(
        {"file": "agent.py", "line_start": 10, "line_end": 12, "reason": "Tool registration."}
    )

    assert attack.candidate_id == attack_spec.attack_id
    assert attack.source == "legacy_attack_spec"
    assert attack.metadata == {"seed": 7, "legacy_label": "controlled"}
    assert evidence.ref == "agent.py"
    assert evidence.locator == {"line_start": 10, "line_end": 12}


@pytest.mark.parametrize(
    ("model", "payload", "message"),
    [
        (
            AgentProfile,
            {
                **_profile_payload(),
                "nodes": [
                    _profile_payload()["nodes"][0],
                    {**_profile_payload()["nodes"][0], "target": "agent:other"},
                ],
            },
            "node ids must be unique",
        ),
        (
            Trajectory,
            {
                "session_id": "session-001",
                "experiment_id": "experiment-001",
                "seed": 7,
                "framework": "direct_api",
                "steps": [
                    {
                        "step_index": 1,
                        "step_type": "tool_call",
                        "timestamp": "2026-08-01T00:00:00Z",
                        "tool_call": {},
                    }
                ],
            },
            "step indexes must be contiguous",
        ),
        (
            EvolutionState,
            {"experiment_id": "experiment-001", "stage": "completed"},
            "terminal evolution states require stop_reason",
        ),
        (
            ExperimentManifest,
            {
                "experiment_id": "experiment-001",
                "research_question": "RQ2",
                "agent_profile_ref": "profile.json",
                "dataset_refs": ["cases.jsonl"],
                "attack_strategy": {},
                "defense_strategy": {},
                "metric_names": ["asr"],
                "seeds": [7, 7],
                "execution_mode": "offline_fixture",
            },
            "seeds must be unique",
        ),
    ],
)
def test_core_contracts_reject_invalid_inputs(model: type, payload: dict, message: str) -> None:
    with pytest.raises(ValidationError, match=message):
        model.model_validate(payload)


def test_provenance_rejects_credentials_and_invalid_hashes() -> None:
    with pytest.raises(ValidationError, match="must not contain credentials"):
        Provenance(
            git_commit="0123456789abcdef",
            git_dirty=True,
            python_version="3.10.14",
            config_sha256=SHA256,
            execution_mode="external_model",
            external_model={"model": "example", "api_key": "must-not-be-recorded"},
        )

    with pytest.raises(ValidationError):
        Provenance(
            git_commit="0123456789abcdef",
            git_dirty=True,
            python_version="3.10.14",
            config_sha256="not-a-hash",
            execution_mode="offline_fixture",
        )


def test_core_import_does_not_load_application_or_runtime_modules() -> None:
    forbidden_prefixes = (
        "fastapi",
        "redsentinel.application.engine",
        "redsentinel.runtime.engine.sandbox",
        "redsentinel.adapters.engine",
    )
    before = set(sys.modules)
    importlib.reload(importlib.import_module("redsentinel.core"))
    loaded = set(sys.modules) - before

    assert not any(name == prefix or name.startswith(f"{prefix}.") for prefix in forbidden_prefixes for name in loaded)

    source = Path(importlib.import_module("redsentinel.core.models").__file__).read_text(encoding="utf-8")
    assert "fastapi" not in source
    assert "product_api" not in source
    assert "redsentinel.runtime.engine.sandbox" not in source
