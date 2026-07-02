from pathlib import Path

import pytest

from auto_evaluation_system.product_api.app import create_app
from auto_evaluation_system.product_api.auth_password import hash_password
from auto_evaluation_system.product_api.auth_service import ProductAuthService
from auto_evaluation_system.product_api.storage import ProductStorage


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


def test_openmanus_admin_registration_allows_admin(tmp_path: Path) -> None:
    client = _client(tmp_path)
    admin_token = _create_user(tmp_path, username="platform-admin", role="admin")

    response = client.post("/v1/admin/agents/openmanus", headers=_auth_header(admin_token))

    assert response.status_code == 200
    body = response.json()
    assert body["schema_version"] == "openmanus-admin-registration-v0.1"
    assert body["status"] == "registered"
    assert body["library_entry"]["agent_id"] == "openmanus_official"
    assert body["library_entry"]["source"] == "official"
    assert body["library_entry"]["created_by"] == "platform-admin"
    assert body["agent"]["tenant_id"] == "platform-admin"
    assert body["agent"]["username"] == "platform-admin"
    assert body["agent"]["agent_id"] == "openmanus_official"
    assert body["agent"]["adapter_type"] == "openmanus"
    assert body["agent"]["framework"] == "OpenManus"
    assert body["agent"]["status"] == "ready"
    assert {tool["name"] for tool in body["agent"]["tool_specs"]} >= {
        "browser_search",
        "python_execute",
        "file_operation",
    }
    assert (tmp_path / "agent_library" / "openmanus_official.json").exists()
    assert (tmp_path / "platform-admin" / "agents" / "openmanus_official.json").exists()


def test_openmanus_admin_registration_rejects_non_admin_user(tmp_path: Path) -> None:
    client = _client(tmp_path)
    user_token = _create_user(tmp_path, username="tenant-user", role="user")

    response = client.post("/v1/admin/agents/openmanus", headers=_auth_header(user_token))

    assert response.status_code == 403
    assert response.json()["detail"]["error_code"] == "admin_required"
