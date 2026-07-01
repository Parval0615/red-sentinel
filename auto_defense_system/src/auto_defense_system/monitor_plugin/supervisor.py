from __future__ import annotations

import json
import tempfile
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from auto_attack_system.ingestion.deep import DockerTracePlan
from auto_defense_system.monitor_plugin.interceptor import MonitorDecision, MonitorInterceptor
from auto_defense_system.security.exec_guard import CodeExecutionRequest

DockerExecutor = Callable[[DockerTracePlan], Any]


class SupervisorResolution(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="forbid")

    ask_id: str
    approved: bool
    decision: MonitorDecision
    docker_plan: DockerTracePlan | None = None
    docker_artifacts: dict[str, Any] | None = None
    monitor_event: Any | None = None


class SupervisorApprovalService:
    """Backend supervisor loop for monitor `ask` decisions.

    The service is intentionally UI-agnostic: a web console or CLI can call
    `resolve(...)`, while this class owns approval state, audit writes through
    the interceptor, and approved code execution through the Docker sandbox.
    """

    def __init__(
        self,
        interceptor: MonitorInterceptor,
        *,
        output_dir: str | Path | None = None,
        docker_executor: Callable[..., Any] | None = None,
    ) -> None:
        self.interceptor = interceptor
        self.output_dir = Path(output_dir) if output_dir is not None else Path(tempfile.mkdtemp(prefix="red-sentinel-supervisor-"))
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.docker_executor = docker_executor or _execute_docker_trace

    def resolve(self, ask_id: str, *, approved: bool, reason: str | None = None) -> SupervisorResolution:
        pending = self.interceptor.pending_asks[ask_id]
        pending_payload = dict(self.interceptor.pending_payloads.get(ask_id, {}))
        resolved = self.interceptor.resolve_ask(ask_id, approved=approved, reason=reason)

        docker_plan = None
        docker_artifacts = None
        if approved and pending.call_type == "code_execution":
            request = CodeExecutionRequest.model_validate(pending_payload)
            docker_plan, docker_artifacts = execute_approved_code_in_docker(
                request,
                output_dir=self.output_dir / ask_id,
                docker_executor=self.docker_executor,
            )

        return SupervisorResolution(
            ask_id=ask_id,
            approved=approved,
            decision=resolved,
            docker_plan=docker_plan,
            docker_artifacts=docker_artifacts,
            monitor_event=_monitor_event(resolved, docker_artifacts=docker_artifacts),
        )


def execute_approved_code_in_docker(
    request: CodeExecutionRequest,
    *,
    output_dir: str | Path,
    docker_executor: Callable[..., Any] | None = None,
) -> tuple[DockerTracePlan, dict[str, Any]]:
    output_root = Path(output_dir)
    input_dir = output_root / "input"
    artifacts_dir = output_root / "artifacts"
    input_dir.mkdir(parents=True, exist_ok=True)
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    script_path = input_dir / "redsentinel_exec.py"
    script_path.write_text(_script_for_request(request), encoding="utf-8")

    image = str(request.metadata.get("docker_image") or "python:3.12-slim")
    plan = DockerTracePlan(
        agent_name=str(request.metadata.get("agent_name") or "supervised-code-execution"),
        docker_image=image,
        adapter_entrypoint=f"python /workspace/{input_dir.name}/redsentinel_exec.py",
        node_targets=[request.entrypoint or "code_execution"],
        expected_artifacts=["trajectory", "stdout", "stderr", "audit"],
        read_only_mounts=[str(input_dir)],
        network_policy="disabled",
        notes=["Approved by supervisor; executed through Docker sandbox with network disabled."],
    )
    executor = docker_executor or _execute_docker_trace
    artifacts = executor(plan, output_dir=artifacts_dir)
    if hasattr(artifacts, "model_dump"):
        artifacts_payload = artifacts.model_dump(mode="json")
    else:
        artifacts_payload = dict(artifacts)
    return plan, artifacts_payload


def _script_for_request(request: CodeExecutionRequest) -> str:
    code_json = json.dumps(request.code)
    return (
        "import json\n"
        "print(json.dumps({'type':'tool_call','call_id':'supervised-code-start',"
        "'tool_name':'code_execution','arguments':{'language':'python'},"
        "'response':{'status':'started'},'parent_turn_index':0}, ensure_ascii=False))\n"
        f"exec(compile({code_json}, 'redsentinel_user_code.py', 'exec'), {{'__name__': '__main__'}})\n"
        "print(json.dumps({'type':'tool_call','call_id':'supervised-code-complete',"
        "'tool_name':'code_execution','arguments':{'language':'python'},"
        "'response':{'status':'completed'},'parent_turn_index':0}, ensure_ascii=False))\n"
    )


def _execute_docker_trace(plan: DockerTracePlan, *, output_dir: str | Path | None = None) -> Any:
    from auto_evaluation_system.sandbox.docker.executor import execute_docker_trace

    return execute_docker_trace(plan, output_dir=output_dir)


def _monitor_event(decision: MonitorDecision, *, docker_artifacts: dict[str, Any] | None) -> Any:
    from auto_evaluation_system.events import MonitorDecisionPayload, StepEvent, StepType

    artifact_refs = []
    if docker_artifacts:
        artifact_refs = [
            str(value)
            for key, value in docker_artifacts.items()
            if key.endswith("_path") and value
        ]
    return StepEvent(
        step_type=StepType.MONITOR_DECISION,
        timestamp=datetime.now(UTC),
        monitor_decision=MonitorDecisionPayload(
            call_type=decision.call_type,
            decision=decision.decision,
            risk_level=decision.risk_level,
            reason=decision.reason,
            audit_object=_audit_object(decision.call_type),
            ask_id=decision.ask_id,
            approval_state=decision.approval_state,
            artifact_refs=artifact_refs,
        ),
    )


def _audit_object(call_type: str) -> str:
    if call_type == "code_execution":
        return "code"
    if call_type == "file_access":
        return "file"
    if call_type in {"llm_input", "llm_output"}:
        return "llm" if call_type == "llm_input" else "output"
    return "tool"


__all__ = [
    "SupervisorApprovalService",
    "SupervisorResolution",
    "execute_approved_code_in_docker",
]
