from __future__ import annotations

import json
from pathlib import Path

from redsentinel.research.p0_demo import write_p0_demo_summary


def test_p0_summary_indexes_three_trajectory_risks_without_inventing_metrics(tmp_path: Path) -> None:
    evaluation_dir = tmp_path / "evaluations" / "run"
    evolution_dir = tmp_path / "evolution" / "run"
    evaluation_dir.mkdir(parents=True)
    evolution_dir.mkdir(parents=True)
    risks = ("memory_poisoning", "tool_tampering", "goal_perturbation")
    _write_json(
        evaluation_dir / "report.json",
        {
            "metrics": {
                "passed_pairs": 3,
                "total_attack_pairs": 3,
                "asr_before_defense": 1.0,
                "asr_after_defense": 0.0,
                "false_positive_rate": 0.0,
                "audit_chain_valid": True,
            },
            "damage_attribution": [
                {
                    "pair_id": f"pair-{risk}",
                    "risk_type": risk,
                    "detector_decision": "high",
                    "detector_score": 0.9,
                    "blocked_by_defense": True,
                    "passed": True,
                    "attribution": [{"field_path": "steps[0]"}],
                }
                for risk in risks
            ],
        },
    )
    _write_json(
        evaluation_dir / "audit_refs.json",
        {
            "references": [
                {
                    "pair_id": f"pair-{risk}",
                    "audit_log_path": str(evaluation_dir / f"{risk}.log"),
                    "integrity": {"valid": True},
                }
                for risk in risks
            ]
        },
    )
    _write_json(
        evolution_dir / "raw-result-v1.json",
        {
            "metrics": {
                "asr_initial": 0.4375,
                "asr_final": 0.0,
                "convergence_rounds": 7,
            }
        },
    )
    profile_path = tmp_path / "profiles" / "simple_agent.json"
    evaluation_index = evaluation_dir / "evidence-index-v1.json"
    evolution_index = evolution_dir / "evidence-index-v1.json"

    output = write_p0_demo_summary(
        output_root=tmp_path,
        seed=42,
        doctor_checks={"rq_matrix": True},
        profile_path=profile_path,
        evaluation_dir=evaluation_dir,
        evaluation_evidence_index=evaluation_index,
        evolution_dir=evolution_dir,
        evolution_evidence_index=evolution_index,
    )

    summary = json.loads(output.read_text(encoding="utf-8"))
    assert summary["execution_mode"] == "offline_fixture"
    assert [item["risk_type"] for item in summary["trajectory_evidence"]] == list(risks)
    assert all(len(item["evidence_refs"]) == 3 for item in summary["trajectory_evidence"])
    assert summary["metrics"]["business_success_rate"]["status"] == "not_evaluated"
    assert summary["metrics"]["overhead"]["status"] == "not_evaluated"


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")
