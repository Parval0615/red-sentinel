from __future__ import annotations

from pathlib import Path

from redsentinel.attacks.engine.attack_agent import AttackAgent as LegacyAttackAgent
from redsentinel.attacks.engine.attack_spec import AttackSpec
from redsentinel.attacks.engine.evolution import evolve_attack_specs as legacy_evolve_attack_specs
from redsentinel.attacks.engine.scripts._scenario_dry_run import (
    load_cases as legacy_load_cases,
    run_scenario_cli as legacy_run_scenario_cli,
)
from redsentinel.attacks.engine.threat_taxonomy import THREAT_CATEGORIES as LEGACY_THREAT_CATEGORIES
from redsentinel.core.agent_security import AgentProfile, AgentProfileNode
from redsentinel.attacks import (
    THREAT_CATEGORIES,
    AttackAgent,
    build_profile_driven_attack_plan,
    evolve_attack_specs,
    load_attack_cases,
    run_scenario_cli,
    select_unique,
)


ROOT = Path(__file__).resolve().parents[2]
SCENARIOS = (
    "environment_awareness_pollution",
    "goal_drift",
    "jailbreak",
    "memory_poisoning",
    "prompt_injection",
    "tool_tampering",
    "training_data_leakage",
)


def _base_spec() -> AttackSpec:
    return AttackSpec(
        attack_id="agent:tool:tool_tampering:baseline",
        risk_type="tool_tampering",
        strategy="baseline_probe",
        intensity="light",
        target="adapter:invoke",
        label="controlled",
        goal="Probe tool node.",
        success_criteria=["baseline measured"],
        metadata={"node_id": "tool"},
    )


def test_attack_namespace_preserves_legacy_public_objects() -> None:
    assert AttackAgent is LegacyAttackAgent
    assert evolve_attack_specs is legacy_evolve_attack_specs
    assert run_scenario_cli is legacy_run_scenario_cli
    assert THREAT_CATEGORIES is LEGACY_THREAT_CATEGORIES
    assert len(THREAT_CATEGORIES) == 7


def test_all_seven_case_sets_use_one_traceable_loader() -> None:
    seen_payload_ids: set[str] = set()
    for scenario in SCENARIOS:
        path = ROOT / "docs" / "attack_scenarios" / scenario / "cases.jsonl"
        cases = load_attack_cases(path, repository_root=ROOT)

        assert len(cases) >= 15
        assert legacy_load_cases(path) == cases
        for case in cases:
            assert case["payload_id"] == case["payload_source"]["payload_id"]
            seen_payload_ids.add(case["payload_id"])

    assert len(seen_payload_ids) >= 7 * 15


def test_profile_driven_generation_remains_node_specific() -> None:
    profile = AgentProfile(
        agent_name="tool_agent",
        framework="python_function",
        root_path=".",
        entrypoint="app:run",
        business_domain="ecommerce",
        nodes=[
            AgentProfileNode(
                id="checkout",
                type="tool_node",
                target="app:checkout",
                risk_surfaces=["tool_abuse", "parameter_tampering"],
            )
        ],
    )

    plan = build_profile_driven_attack_plan(profile)

    assert {spec.risk_type for spec in plan.targeted_specs} == {"tool_abuse", "parameter_tampering"}
    assert all(spec.metadata["node_id"] == "checkout" for spec in plan.targeted_specs)


def test_mutation_keeps_seed_semantics_and_is_reproducible() -> None:
    kwargs = {
        "failed_attempts": [
            {
                "risk_type": "tool_tampering",
                "node_id": "tool",
                "attempt_id": "attempt-1",
            }
        ]
    }

    first = evolve_attack_specs([_base_spec()], seed=23, **kwargs)
    replay = evolve_attack_specs([_base_spec()], seed=23, **kwargs)
    different_seed = evolve_attack_specs([_base_spec()], seed=24, **kwargs)

    assert first.model_dump(mode="json") == replay.model_dump(mode="json")
    assert first.evolution_records[0]["seed"] == 23
    assert first.evolved_specs[0].metadata["seed"] == 23
    assert (
        first.evolution_records[0]["mutation_strategy"]
        != different_seed.evolution_records[0]["mutation_strategy"]
    )


def test_selection_is_stable_deduplicated_and_budgeted() -> None:
    candidates = [
        {"id": "a", "value": 1},
        {"id": "a", "value": 2},
        {"id": "b", "value": 3},
    ]

    assert select_unique(candidates, key=lambda item: item["id"]) == [candidates[0], candidates[2]]
    assert select_unique(candidates, key=lambda item: item["id"], limit=1) == [candidates[0]]
    assert select_unique(candidates, key=lambda item: item["id"], limit=0) == []
