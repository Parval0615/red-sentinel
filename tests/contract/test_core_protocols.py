from pathlib import Path
from types import SimpleNamespace

from redsentinel.attacks.engine.attack_spec import AttackSpec
from redsentinel.core.agent_security import OptimizationAction, OptimizationDirective
from redsentinel.core.converters import (
    attack_candidate_from_legacy,
    defense_candidate_from_legacy,
)
from redsentinel.core.protocols import (
    AttackGenerator,
    Profiler,
    Reporter,
    RuntimeAdapter,
)


def test_protocols_are_runtime_checkable_by_structure() -> None:
    profiler = SimpleNamespace(profile=lambda materials, manifest: None)
    attack_generator = SimpleNamespace(generate=lambda profile, state, seed: [])
    reporter = SimpleNamespace(render=lambda evaluation, state, output_dir: {})

    class Adapter:
        adapter_id = "fixture"

        def run(self, profile, attack, defense, *, experiment_id, seed):  # noqa: ANN001
            return None

    assert isinstance(profiler, Profiler)
    assert isinstance(attack_generator, AttackGenerator)
    assert isinstance(reporter, Reporter)
    assert isinstance(Adapter(), RuntimeAdapter)


def test_attack_converter_maps_legacy_contract_explicitly() -> None:
    legacy = AttackSpec(
        attack_id="attack-1",
        risk_type="prompt_injection",
        strategy="override",
        intensity="medium",
        target="input",
        label="controlled",
        goal="change the instruction",
        success_criteria=["unsafe response"],
        metadata={"source": "fixture"},
    )

    candidate = attack_candidate_from_legacy(legacy)

    assert candidate.candidate_id == "attack-1"
    assert candidate.risk_type == "prompt_injection"
    assert candidate.metadata == {"source": "fixture", "legacy_label": "controlled"}


def test_defense_converter_maps_legacy_contract_explicitly() -> None:
    legacy = OptimizationDirective(
        directive_id="directive-1",
        agent_name="fixture-agent",
        source="evaluation",
        target_node_id="input",
        risk_type="prompt_injection",
        priority="high",
        recommended_actions=[
            OptimizationAction(
                type="add_defense",
                name="input_guard",
                mode="strict",
                parameters={"threshold": 0.8},
            )
        ],
        rationale="Observed a controlled bypass.",
        evidence_refs=["artifacts/report.json"],
    )

    candidate = defense_candidate_from_legacy(legacy)

    assert candidate.candidate_id == "directive-1"
    assert candidate.target_node_ids == ["input"]
    assert candidate.actions == [
        {
            "type": "add_defense",
            "name": "input_guard",
            "mode": "strict",
            "parameters": {"threshold": 0.8},
        }
    ]
    assert candidate.evidence_refs[0].ref == "artifacts/report.json"


def test_protocol_module_does_not_require_application_dependencies() -> None:
    source = Path("src/redsentinel/core/protocols.py").read_text(encoding="utf-8")

    assert "fastapi" not in source
    assert "product_api" not in source
    assert "auto_" not in source
