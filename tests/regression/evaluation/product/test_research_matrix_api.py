from pathlib import Path

import pytest

from redsentinel.application.engine.app import create_app


def _client(tmp_path: Path):
    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient

    return TestClient(create_app(storage_root=tmp_path))


def test_research_matrix_api_lists_without_authentication_or_execution(tmp_path: Path) -> None:
    client = _client(tmp_path)

    response = client.get("/v1/research/experiments")

    assert response.status_code == 200
    payload = response.json()
    assert payload["schema_version"] == "rq-experiment-matrix-v1"
    assert [item["rq_id"] for item in payload["research_questions"]] == [
        "RQ1",
        "RQ2",
        "RQ3",
        "RQ4",
        "RQ5",
    ]
    assert not list(tmp_path.rglob("comparison.json"))
    assert not list(tmp_path.rglob("evolution-state.json"))


def test_research_matrix_api_returns_one_question_and_rejects_unknown(tmp_path: Path) -> None:
    client = _client(tmp_path)

    response = client.get("/v1/research/experiments/RQ4")
    missing = client.get("/v1/research/experiments/RQ9")

    assert response.status_code == 200
    assert response.json()["research_question"]["rq_id"] == "RQ4"
    assert missing.status_code == 404
    assert missing.json()["detail"]["error_code"] == "research_question_not_found"
