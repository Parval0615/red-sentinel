from pathlib import Path

import pytest

from redsentinel.application.engine.auth_password import hash_password, verify_password
from redsentinel.application.engine.storage import ProductStorage, safe_component


def test_product_storage_paths_reject_unsafe_components(tmp_path: Path) -> None:
    storage = ProductStorage(tmp_path)

    with pytest.raises(ValueError, match="Unsafe tenant_id"):
        storage.agent_path("..", "agent_001")
    with pytest.raises(ValueError, match="Unsafe agent_id"):
        storage.agent_path("tenant_001", "../agent")
    with pytest.raises(ValueError, match="Unsafe report_id"):
        storage.find_report_path("../report")
    assert safe_component("tenant_001", "tenant_id") == "tenant_001"


def test_product_storage_writes_reads_and_finds_users(tmp_path: Path) -> None:
    storage = ProductStorage(tmp_path)
    password = "correct-horse-battery-staple"
    password_hash, password_salt = hash_password(password)
    other_hash, other_salt = hash_password(password)

    user = storage.write_user(
        "usr_001",
        {
            "username": "Demo-User",
            "email": "Demo@Example.Test",
            "password_hash": password_hash,
            "password_salt": password_salt,
        }
    )
    persisted = storage.user_path("usr_001").read_text(encoding="utf-8")

    assert user["schema_version"] == "auth-user-record-v0.1"
    assert user["user_id"] == "usr_001"
    assert user["status"] == "active"
    assert user["created_at"]
    assert user["updated_at"]
    assert "password" not in user
    assert password not in persisted
    assert password_hash != password
    assert password_salt != password
    assert other_salt != password_salt
    assert other_hash != password_hash
    assert storage.read_user("usr_001") == user
    assert storage.find_user_by_username("demo-user") == user
    assert storage.find_user_by_email("demo@example.test") == user
    assert storage.find_user_by_username("missing") is None
    assert storage.find_user_by_email("missing@example.test") is None
    assert verify_password(password, user["password_hash"], user["password_salt"]) is True
    assert verify_password("wrong-password", user["password_hash"], user["password_salt"]) is False


def test_product_storage_rejects_duplicate_usernames_and_emails(tmp_path: Path) -> None:
    storage = ProductStorage(tmp_path)
    password_hash, password_salt = hash_password("strong-password")
    duplicate_password_hash, duplicate_password_salt = hash_password("strong-password")

    storage.write_user(
        "usr_001",
        {
            "username": "demo-user",
            "email": "demo@example.test",
            "password_hash": password_hash,
            "password_salt": password_salt,
        }
    )

    with pytest.raises(ValueError, match="Username already exists"):
        storage.write_user(
            "usr_002",
            {
                "username": "Demo-User",
                "email": "other@example.test",
                "password_hash": duplicate_password_hash,
                "password_salt": duplicate_password_salt,
            }
        )

    with pytest.raises(ValueError, match="Email already exists"):
        storage.write_user(
            "usr_003",
            {
                "username": "other-user",
                "email": "Demo@Example.Test",
                "password_hash": duplicate_password_hash,
                "password_salt": duplicate_password_salt,
            }
        )


def test_product_storage_writes_and_reads_logical_documents(tmp_path: Path) -> None:
    storage = ProductStorage(tmp_path)

    agent = storage.write_agent("tenant_001", "agent_001", {"name": "Demo Agent"})
    material = storage.write_material(
        "tenant_001",
        "agent_001",
        "mat_001",
        {
            "type": "api",
            "endpoint_url": "https://example.test/v1/chat",
            "secret_ref": "local://tenant_001/agent_001/api_key",
            "has_api_key": True,
            "masked_api_key": "sk-t...cret",
        },
    )
    profile = storage.write_profile(
        "tenant_001",
        "agent_001",
        "profile_001",
        {"nodes": [{"node_id": "tool_node", "critical": True}]},
    )
    benchmark = storage.write_benchmark("bench_001", {"name": "E-commerce Security", "active_version": "v1"})
    benchmark_version = storage.write_benchmark_version(
        "bench_001",
        "v1",
        {"case_count": 1, "cases": [{"case_id": "case_001"}]},
    )
    evaluation = storage.write_evaluation(
        "tenant_001",
        "agent_001",
        "eval_001",
        {"benchmark_id": "bench_001", "benchmark_version": "v1", "status": "queued"},
    )
    result = storage.write_result(
        "tenant_001",
        "eval_001",
        "result_001",
        {"case_id": "case_001", "actual_decision": "block"},
    )
    report = storage.write_report_record(
        "tenant_001",
        "agent_001",
        "eval_001",
        "report_001",
        {"score": 90, "risk_level": "low", "asr": 0.0, "fpr": 0.0},
    )
    snapshot = storage.write_metric_snapshot(
        "tenant_001",
        "agent_001",
        "snap_001",
        {"latest_report_id": "report_001", "score": 90, "risk_level": "low", "asr": 0.0, "fpr": 0.0},
    )

    assert agent["schema_version"] == "agent-v0.1"
    assert material["schema_version"] == "agent-material-v0.1"
    assert profile["agent_id"] == "agent_001"
    assert benchmark["benchmark_id"] == "bench_001"
    assert benchmark_version["version"] == "v1"
    assert evaluation["evaluation_id"] == "eval_001"
    assert result["result_id"] == "result_001"
    assert report["report_id"] == "report_001"
    assert snapshot["snapshot_id"] == "snap_001"
    assert storage.read_agent("tenant_001", "agent_001") == agent
    assert storage.read_material("tenant_001", "mat_001") == material
    assert storage.read_profile("tenant_001", "profile_001") == profile
    assert storage.read_benchmark("bench_001") == benchmark
    assert storage.read_benchmark_version("bench_001", "v1") == benchmark_version
    assert storage.read_evaluation("tenant_001", "eval_001") == evaluation
    assert storage.read_result("tenant_001", "eval_001", "result_001") == result
    assert storage.read_report_record("tenant_001", "report_001") == report
    assert storage.read_metric_snapshot("tenant_001", "snap_001") == snapshot


def test_product_storage_does_not_persist_raw_api_keys(tmp_path: Path) -> None:
    storage = ProductStorage(tmp_path)

    material = storage.write_material(
        "tenant_001",
        "agent_001",
        "mat_001",
        {
            "api_key": "sk-raw-secret",
            "nested": {"authorization": "Bearer sk-raw-secret", "client_secret": "sk-raw-secret"},
            "secret_ref": "local://tenant_001/agent_001/api_key",
            "has_api_key": True,
            "masked_api_key": "sk-r...cret",
        },
    )
    report = storage.write_report_record(
        "tenant_001",
        "agent_001",
        "eval_001",
        "report_001",
        {
            "score": 80,
            "summary": {"api_key": "sk-raw-secret", "masked_api_key": "sk-r...cret"},
        },
    )
    persisted = "\n".join(
        [
            storage.material_path("tenant_001", "mat_001").read_text(encoding="utf-8"),
            storage.report_record_path("tenant_001", "report_001").read_text(encoding="utf-8"),
        ]
    )

    assert "sk-raw-secret" not in persisted
    assert "api_key" not in material
    assert "authorization" not in material["nested"]
    assert "client_secret" not in material["nested"]
    assert material["secret_ref"] == "local://tenant_001/agent_001/api_key"
    assert report["summary"] == {"masked_api_key": "sk-r...cret"}
