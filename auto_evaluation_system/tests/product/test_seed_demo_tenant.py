from pathlib import Path

import pytest

from auto_evaluation_system.product_api.app import create_app
from auto_evaluation_system.product_api.auth_password import hash_password
from auto_evaluation_system.product_api.auth_service import ProductAuthService
from auto_evaluation_system.product_api.seed import DEMO_AGENT_ID
from auto_evaluation_system.product_api.storage import ProductStorage


def _client(tmp_path: Path, *, seed_demo: bool = False):
    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient

    app = create_app(storage_root=tmp_path, seed_demo=seed_demo)
    return TestClient(app, raise_server_exceptions=False), app


def _auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _create_admin_token(tmp_path: Path) -> str:
    storage = ProductStorage(tmp_path)
    password_hash, password_salt = hash_password("correct-horse-battery-staple")
    user = storage.write_user(
        "usr_platform_admin",
        {
            "username": "platform-admin",
            "email": "platform-admin@example.test",
            "password_hash": password_hash,
            "password_salt": password_salt,
            "status": "active",
            "role": "admin",
        },
    )
    return ProductAuthService(storage=storage).issue_access_token(user, expires_in_seconds=3600)


def test_create_app_does_not_seed_demo_tenant_by_default(tmp_path: Path) -> None:
    _client(tmp_path)

    assert ProductStorage(tmp_path).user_paths() == []
    assert not list(tmp_path.glob("demo_shopper_*/agents/*.json"))


def test_seed_demo_creates_random_user_and_ecommerce_agent(tmp_path: Path) -> None:
    client, app = _client(tmp_path, seed_demo=True)
    seed = app.state.demo_seed

    assert seed["username"].startswith("demo_shopper_")
    assert len(seed["username"].removeprefix("demo_shopper_")) == 6
    assert seed["platform_role"] == "user"
    assert seed["agent_id"] == DEMO_AGENT_ID

    storage = ProductStorage(tmp_path)
    user = storage.find_user_by_username(seed["username"])
    assert user is not None
    assert user["role"] == "user"

    agent = storage.read_agent(seed["username"], DEMO_AGENT_ID)
    assert agent["tenant_id"] == seed["username"]
    assert agent["username"] == seed["username"]
    assert agent["adapter_type"] == "ecommerce_demo"

    login = client.post(
        "/v1/auth/login",
        json={"account": seed["username"], "password": seed["password"]},
    )
    assert login.status_code == 200
    visible = client.get(f"/v1/agents/{DEMO_AGENT_ID}", headers=_auth_header(login.json()["access_token"]))
    assert visible.status_code == 200
    assert visible.json()["tenant_id"] == seed["username"]


def test_admin_cannot_read_demo_user_agent_through_tenant_view(tmp_path: Path) -> None:
    client, _app = _client(tmp_path, seed_demo=True)
    admin_token = _create_admin_token(tmp_path)

    response = client.get(f"/v1/agents/{DEMO_AGENT_ID}", headers=_auth_header(admin_token))

    assert response.status_code == 404
    assert response.json()["detail"]["error_code"] == "agent_not_found"
