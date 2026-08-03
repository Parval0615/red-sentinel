from pathlib import Path

import pytest

from redsentinel.application.engine.app import create_app
from redsentinel.application.engine.agent_library import AgentLibraryService
from redsentinel.application.engine.auth_password import hash_password
from redsentinel.application.engine.auth_service import ProductAuthService
from redsentinel.application.contracts import AuthUserRecord, AuthUserSummary
from redsentinel.application.engine.storage import ProductStorage


def _client(tmp_path: Path):
    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient

    return TestClient(create_app(storage_root=tmp_path), raise_server_exceptions=False)


def _auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _create_user(tmp_path: Path, *, username: str, role: str) -> str:
    storage = ProductStorage(tmp_path)
    password_hash, password_salt = hash_password("correct-horse-battery-staple")
    user = storage.write_user(
        f"usr_{username}",
        {
            "username": username,
            "email": f"{username}@example.test",
            "password_hash": password_hash,
            "password_salt": password_salt,
            "status": "active",
            "role": role,
        },
    )
    return ProductAuthService(storage=storage).issue_access_token(user, expires_in_seconds=3600)


def test_registered_users_default_to_user_role(tmp_path: Path) -> None:
    client = _client(tmp_path)

    response = client.post(
        "/v1/auth/register",
        json={"username": "demo-user", "email": "demo@example.test", "password": "strong-password"},
    )

    assert response.status_code == 200
    assert response.json()["user"]["role"] == "user"
    assert ProductStorage(tmp_path).find_user_by_username("demo-user")["role"] == "user"


def test_auth_user_contracts_include_platform_role() -> None:
    summary = AuthUserSummary(user_id="usr_1", username="alice", email="alice@example.test")
    record = AuthUserRecord(
        user_id="usr_1",
        username="alice",
        email="alice@example.test",
        password_hash="hash",
        password_salt="salt",
        role="admin",
    )

    assert summary.role == "user"
    assert record.role == "admin"


def test_admin_only_agent_library_rejects_user_and_allows_admin(tmp_path: Path) -> None:
    client = _client(tmp_path)
    user_token = _create_user(tmp_path, username="tenant-user", role="user")
    admin_token = _create_user(tmp_path, username="platform-admin", role="admin")

    user_response = client.get("/v1/admin/agent-library", headers=_auth_header(user_token))
    admin_response = client.get("/v1/admin/agent-library", headers=_auth_header(admin_token))

    assert user_response.status_code == 403
    assert user_response.json()["detail"]["error_code"] == "admin_required"
    assert admin_response.status_code == 200
    assert any(item["agent_id"] == "openmanus_official" for item in admin_response.json())


def test_admin_can_manage_agent_library_entries(tmp_path: Path) -> None:
    client = _client(tmp_path)
    admin_token = _create_user(tmp_path, username="platform-admin", role="admin")

    create_response = client.post(
        "/v1/admin/agent-library",
        headers=_auth_header(admin_token),
        json={
            "agent_id": "custom_openmanus",
            "name": "Custom OpenManus",
            "framework": "OpenManus",
            "description": "Team maintained OpenManus adapter.",
            "default_benchmark_id": "ecommerce-security-v0.1",
            "tags": ["official", "openmanus"],
        },
    )
    lookup_response = client.get("/v1/admin/agent-library/custom_openmanus", headers=_auth_header(admin_token))

    assert create_response.status_code == 200
    assert create_response.json()["created_by"] == "platform-admin"
    assert lookup_response.status_code == 200
    assert lookup_response.json()["name"] == "Custom OpenManus"


def test_agent_library_service_seeds_and_persists_openmanus_entries(tmp_path: Path) -> None:
    service = AgentLibraryService(storage_root=tmp_path)

    entries = service.list_entries()
    saved = service.upsert_entry(
        entries[0].model_copy(update={"agent_id": "openmanus_team", "name": "Team OpenManus", "source": "custom"}),
        created_by="platform-admin",
    )

    assert entries[0].agent_id == "openmanus_official"
    assert saved.created_by == "platform-admin"
    assert service.get_entry("openmanus_team").name == "Team OpenManus"


def test_admin_role_is_separate_from_defense_role_permissions() -> None:
    product_api_root = Path("src/redsentinel/application")
    product_sources = "\n".join(path.read_text(encoding="utf-8") for path in product_api_root.glob("*.py"))

    assert "ROLE_PERMISSIONS" not in product_sources
    assert "redsentinel.defenses.engine.security.permission" not in product_sources
