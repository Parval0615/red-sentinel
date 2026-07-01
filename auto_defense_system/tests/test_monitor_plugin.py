from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from auto_defense_system.monitor_plugin import MonitorInterceptor, OpenManusMonitorHooks, SupervisorApprovalService
from auto_defense_system.openmanus_agent import build_default_adapter
from auto_defense_system.security import audit


def test_monitor_plugin_denies_dangerous_tool_call() -> None:
    interceptor = MonitorInterceptor()

    decision = interceptor.intercept("tool_call", {"tool_name": "db_query", "arguments": {"sql": "DROP TABLE users"}})

    assert decision.decision == "deny"
    assert decision.allowed is False
    assert decision.audit_payload["operation"] == "monitor_tool_call"
    assert decision.audit_payload["rule_name"] == "db_query.block_sql_keywords"


def test_monitor_plugin_allows_readonly_tool_call() -> None:
    interceptor = MonitorInterceptor()

    decision = interceptor.intercept("tool_call", {"tool_name": "db_query", "arguments": {"sql": "SELECT * FROM users"}})

    assert decision.decision == "allow"
    assert decision.allowed is True


def test_monitor_plugin_asks_for_workspace_file_write(tmp_path: Path) -> None:
    interceptor = MonitorInterceptor(workspace_root=str(tmp_path))

    decision = interceptor.intercept("file_access", {"path": "notes.txt", "action": "write"})

    assert decision.decision == "ask"
    assert decision.ask_id is not None
    assert decision.approval_state == "pending"
    assert decision.ask_id in interceptor.pending_asks
    assert decision.audit_payload["rule_name"] == "file_operation.ask_write"


def test_monitor_plugin_resolves_ask_decision(tmp_path: Path) -> None:
    interceptor = MonitorInterceptor(workspace_root=str(tmp_path))
    pending = interceptor.intercept("file_access", {"path": "notes.txt", "action": "write"})

    resolved = interceptor.resolve_ask(pending.ask_id or "", approved=True, reason="operator approved demo write")

    assert resolved.decision == "allow"
    assert resolved.allowed is True
    assert resolved.approval_state == "approved"
    assert resolved.audit_payload["approval_state"] == "approved"
    assert interceptor.pending_asks == {}


def test_monitor_plugin_denies_outside_workspace_file_write(tmp_path: Path) -> None:
    interceptor = MonitorInterceptor(workspace_root=str(tmp_path))

    decision = interceptor.intercept("file_access", {"path": str(tmp_path.parent / "outside.txt"), "action": "write"})

    assert decision.decision == "deny"
    assert decision.audit_payload["rule_name"] == "file_operation.workspace_boundary"


def test_monitor_plugin_asks_for_code_execution_with_artifact_plan(tmp_path: Path) -> None:
    interceptor = MonitorInterceptor(workspace_root=str(tmp_path))

    decision = interceptor.intercept("code_execution", {"code": "print('hello')", "language": "python", "working_dir": "."})

    assert decision.decision == "ask"
    assert decision.ask_id is not None
    assert decision.audit_payload["sandbox_required"] is True
    assert decision.audit_payload["artifact_plan"]["sandbox"] == "docker"


def test_monitor_plugin_can_write_hash_chain_audit(tmp_path: Path) -> None:
    old_log_file = audit.LOG_FILE
    audit.LOG_FILE = str(tmp_path / "monitor-audit.log")
    try:
        interceptor = MonitorInterceptor(audit_writer=audit.write_audit_log)

        interceptor.intercept("tool_call", {"tool_name": "db_query", "arguments": {"sql": "SELECT 1"}})

        integrity = audit.verify_audit_integrity()
        assert integrity["valid"] is True
        assert integrity["total_entries"] == 1
    finally:
        audit.LOG_FILE = old_log_file


def test_supervisor_approval_executes_code_in_docker_sandbox(tmp_path: Path) -> None:
    calls = []

    def fake_docker_executor(plan, *, output_dir=None):
        calls.append((plan, output_dir))
        return SimpleNamespace(
            model_dump=lambda mode="json": {
                "trajectory_path": str(Path(output_dir or tmp_path) / "trajectory.jsonl"),
                "stdout_path": str(Path(output_dir or tmp_path) / "stdout.log"),
                "stderr_path": str(Path(output_dir or tmp_path) / "stderr.log"),
                "audit_path": str(Path(output_dir or tmp_path) / "audit.log"),
                "exit_code": 0,
                "error": None,
            }
        )

    interceptor = MonitorInterceptor(workspace_root=str(tmp_path))
    pending = interceptor.intercept("code_execution", {"code": "print('hello')", "language": "python"})
    supervisor = SupervisorApprovalService(interceptor, output_dir=tmp_path, docker_executor=fake_docker_executor)

    resolution = supervisor.resolve(pending.ask_id or "", approved=True, reason="approved for sandbox")

    assert resolution.approved is True
    assert resolution.decision.approval_state == "approved"
    assert len(calls) == 1
    plan, output_dir = calls[0]
    assert plan.docker_image == "python:3.12-slim"
    assert plan.network_policy == "disabled"
    assert plan.adapter_entrypoint.endswith("redsentinel_exec.py")
    assert output_dir == tmp_path / (pending.ask_id or "") / "artifacts"
    assert resolution.monitor_event.monitor_decision.audit_object == "code"
    assert resolution.monitor_event.monitor_decision.artifact_refs


def test_supervisor_rejection_does_not_execute_docker(tmp_path: Path) -> None:
    calls = []
    interceptor = MonitorInterceptor(workspace_root=str(tmp_path))
    pending = interceptor.intercept("code_execution", {"code": "print('hello')", "language": "python"})
    supervisor = SupervisorApprovalService(
        interceptor,
        output_dir=tmp_path,
        docker_executor=lambda plan, *, output_dir=None: calls.append((plan, output_dir)),
    )

    resolution = supervisor.resolve(pending.ask_id or "", approved=False, reason="not allowed")

    assert resolution.approved is False
    assert resolution.decision.decision == "deny"
    assert resolution.docker_artifacts is None
    assert calls == []


def test_monitor_hooks_wrap_openmanus_adapter() -> None:
    adapter = build_default_adapter()
    hooks = OpenManusMonitorHooks(MonitorInterceptor())
    hooks.wrap_adapter(adapter)

    result = adapter.call_tool("db_query", {"sql": "DROP TABLE users"})

    assert result.startswith("[MONITOR_DENY]")
