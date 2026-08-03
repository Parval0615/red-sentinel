from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from redsentinel.research.catalog import (
    DEFAULT_RQ_MATRIX_PATH,
    RQConfigurationError,
    RQExperimentMatrix,
    list_rq_experiment_matrix,
    load_rq_experiment_matrix,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_rq_matrix_defines_complete_research_design() -> None:
    matrix = load_rq_experiment_matrix()

    assert matrix.schema_version == "rq-experiment-matrix-v1"
    assert [question.rq_id for question in matrix.research_questions] == [
        "RQ1",
        "RQ2",
        "RQ3",
        "RQ4",
        "RQ5",
    ]
    assert {agent.kind for agent in matrix.agents} == {"offline_fixture", "open_source_real"}
    assert matrix.p1_pilot.seeds == [101, 211, 307]
    assert matrix.p1_pilot.budget.max_cells == 72
    assert matrix.p1_pilot.budget.max_model_calls == 3000
    assert matrix.p1_pilot.budget.max_estimated_usd == 150
    assert matrix.p1_pilot.agent_slots[0].agent_id == "openmanus-real"
    assert matrix.p1_pilot.agent_slots[1].status == "pending_w3"
    assert {slot.status for slot in matrix.p1_pilot.model_slots} == {"pending_w4"}

    for question in matrix.research_questions:
        assert question.hypothesis
        assert question.independent_variables
        assert question.dependent_variables
        assert question.control_variables
        assert question.baselines
        assert question.metrics
        assert question.exit_conditions
        assert {tier.name for tier in question.tiers} == {"smoke", "formal"}

        smoke = next(tier for tier in question.tiers if tier.name == "smoke")
        formal = next(tier for tier in question.tiers if tier.name == "formal")
        assert smoke.agent_ids == ["simple-agent-offline"]
        assert smoke.cost_cap.max_model_calls == 0
        assert "openmanus-real" in formal.agent_ids
        assert formal.environment_policy == "skip_with_reason"
        assert formal.adaptation_split == "development"
        assert formal.evaluation_split == "holdout"
        assert formal.cost_cap.max_cases > smoke.cost_cap.max_cases


def test_openmanus_target_is_pinned_and_declares_environment() -> None:
    matrix = load_rq_experiment_matrix()
    target = next(agent for agent in matrix.agents if agent.agent_id == "openmanus-real")

    version = json.loads((REPO_ROOT / target.profile_ref).read_text(encoding="utf-8"))
    assert target.pinned_version == version["pinned_commit"]
    assert target.execution_mode == "real_runtime"
    assert str(target.source_url) == "https://github.com/FoundationAgents/OpenManus.git"
    assert {"OPENAI_API_KEY", "OPENAI_BASE_URL", "OPENAI_MODEL"} <= set(target.environment_requirements)


def test_loader_rejects_incomplete_matrix(tmp_path: Path) -> None:
    payload = yaml.safe_load(DEFAULT_RQ_MATRIX_PATH.read_text(encoding="utf-8"))
    payload["research_questions"] = payload["research_questions"][:-1]
    path = tmp_path / "incomplete.yaml"
    path.write_text(yaml.safe_dump(payload, allow_unicode=True, sort_keys=False), encoding="utf-8")

    with pytest.raises(RQConfigurationError, match="at least 5 items"):
        load_rq_experiment_matrix(path)


def test_loader_rejects_unknown_agent_reference(tmp_path: Path) -> None:
    payload = yaml.safe_load(DEFAULT_RQ_MATRIX_PATH.read_text(encoding="utf-8"))
    payload["research_questions"][0]["tiers"][0]["agent_ids"] = ["missing-agent"]
    path = tmp_path / "unknown-agent.yaml"
    path.write_text(yaml.safe_dump(payload, allow_unicode=True, sort_keys=False), encoding="utf-8")

    with pytest.raises(RQConfigurationError, match="unknown agents"):
        load_rq_experiment_matrix(path)


def test_schema_rejects_missing_cost_cap() -> None:
    payload = yaml.safe_load(DEFAULT_RQ_MATRIX_PATH.read_text(encoding="utf-8"))
    del payload["research_questions"][0]["tiers"][0]["cost_cap"]

    with pytest.raises(ValueError, match="cost_cap"):
        RQExperimentMatrix.model_validate(payload)


def test_schema_rejects_pilot_budget_that_does_not_match_matrix() -> None:
    payload = yaml.safe_load(DEFAULT_RQ_MATRIX_PATH.read_text(encoding="utf-8"))
    payload["p1_pilot"]["budget"]["max_cells"] = 71

    with pytest.raises(ValueError, match="declared matrix size"):
        RQExperimentMatrix.model_validate(payload)


def test_schema_rejects_pending_slots_with_unfrozen_identifiers() -> None:
    payload = yaml.safe_load(DEFAULT_RQ_MATRIX_PATH.read_text(encoding="utf-8"))
    payload["p1_pilot"]["model_slots"][0]["family_id"] = "unfrozen-family"

    with pytest.raises(ValueError, match="cannot claim model identifiers"):
        RQExperimentMatrix.model_validate(payload)


def test_python_listing_api_filters_without_execution(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    before = set(tmp_path.rglob("*"))

    payload = list_rq_experiment_matrix(rq_id="RQ3")

    assert payload["research_question"]["rq_id"] == "RQ3"
    assert {agent["agent_id"] for agent in payload["agents"]} == {
        "simple-agent-offline",
        "openmanus-real",
    }
    assert set(tmp_path.rglob("*")) == before


def test_dedicated_matrix_cli_lists_json_without_running_experiment(tmp_path: Path) -> None:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO_ROOT / "src")
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "redsentinel.research.matrix_cli",
            "list",
            "--rq",
            "RQ2",
            "--format",
            "json",
        ],
        cwd=tmp_path,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(result.stdout)
    assert payload["research_question"]["rq_id"] == "RQ2"
    assert not list(tmp_path.rglob("artifacts"))
