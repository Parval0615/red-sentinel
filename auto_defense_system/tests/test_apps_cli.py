from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _load_cli_module() -> Any:
    spec = importlib.util.spec_from_file_location("auto_defense_app_cli", PROJECT_ROOT / "auto_defense_system/apps/cli.py")
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_defense_app_cli_is_testable_with_injected_dependencies() -> None:
    cli_module = _load_cli_module()
    outputs: list[str] = []
    inputs = iter(["", "log", "3", "role", "admin", "hello", "q"])
    cleared: list[str] = []
    invocations: list[dict[str, str]] = []
    role_permissions = {
        "user": {"name": "User", "desc": "Default role"},
        "admin": {"name": "Admin", "desc": "Admin role"},
    }

    def input_func(_prompt: str) -> str:
        return next(inputs)

    def graph_invoke_func(**kwargs: str) -> str:
        invocations.append(kwargs)
        return "answer-ok"

    exit_code = cli_module.run_cli(
        input_func=input_func,
        output_func=outputs.append,
        graph_invoke_func=graph_invoke_func,
        clear_history_func=cleared.append,
        role_permissions=role_permissions,
        get_role_info_func=lambda role: role_permissions[role],
        default_role="user",
        read_audit_log_func=lambda line_count: f"audit-lines={line_count}",
    )

    joined = "\n".join(outputs)
    assert exit_code == 0
    assert "请输入有效问题" in joined
    assert "audit-lines=3" in joined
    assert "[OK] 已切换为【Admin】，记忆已清空" in joined
    assert "\n【Agent回答】： answer-ok" in joined
    assert "程序已退出" in joined
    assert cleared == ["cli_user"]
    assert invocations == [{"user_input": "hello", "role": "admin", "user_id": "cli_user"}]
