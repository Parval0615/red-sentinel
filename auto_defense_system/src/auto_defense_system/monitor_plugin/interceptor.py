from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from auto_defense_system.security.exec_guard import CodeExecutionRequest, evaluate_code_execution
from auto_defense_system.security.firewall.input_guard import check_malicious_input
from auto_defense_system.security.output.filter import check_output_compliance, mask_sensitive_info
from auto_defense_system.security.policy.engine import evaluate_policy

CallType = Literal["llm_input", "llm_output", "tool_call", "tool_result", "code_execution", "file_access"]
DecisionValue = Literal["allow", "deny", "ask"]
AuditWriter = Callable[..., None]


class MonitorDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    call_type: CallType
    decision: DecisionValue
    allowed: bool
    reason: str = Field(min_length=1)
    risk_level: str = "normal"
    sanitized_payload: dict[str, Any] | None = None
    audit_payload: dict[str, Any] = Field(default_factory=dict)
    ask_id: str | None = None
    approval_state: Literal["not_required", "pending", "approved", "rejected"] = "not_required"


class MonitorInterceptor:
    def __init__(self, *, workspace_root: str | None = None, audit_writer: AuditWriter | None = None) -> None:
        self.workspace_root = workspace_root
        self.audit_writer = audit_writer
        self.decisions: list[MonitorDecision] = []
        self.pending_asks: dict[str, MonitorDecision] = {}

    def intercept(self, call_type: CallType, payload: dict[str, Any]) -> MonitorDecision:
        if call_type == "tool_call":
            decision = self._tool_call(payload)
        elif call_type == "file_access":
            file_payload = {"tool_name": "file_operation", "arguments": dict(payload)}
            decision = self._tool_call(file_payload, call_type="file_access")
        elif call_type == "llm_input":
            decision = self._llm_input(payload)
        elif call_type == "llm_output":
            decision = self._llm_output(payload)
        elif call_type == "tool_result":
            decision = self._tool_result(payload)
        elif call_type == "code_execution":
            decision = self._code_execution(payload)
        else:
            raise ValueError(f"Unsupported call_type: {call_type}")
        self.decisions.append(decision)
        if decision.decision == "ask" and decision.ask_id:
            self.pending_asks[decision.ask_id] = decision
        self._write_audit(decision)
        return decision

    def resolve_ask(self, ask_id: str, *, approved: bool, reason: str | None = None) -> MonitorDecision:
        pending = self.pending_asks.pop(ask_id)
        resolved = pending.model_copy(
            update={
                "decision": "allow" if approved else "deny",
                "allowed": approved,
                "reason": reason or ("approved by supervisor" if approved else "rejected by supervisor"),
                "approval_state": "approved" if approved else "rejected",
                "audit_payload": {
                    **pending.audit_payload,
                    "decision": "allow" if approved else "deny",
                    "approval_state": "approved" if approved else "rejected",
                    "result": reason or ("approved by supervisor" if approved else "rejected by supervisor"),
                },
            }
        )
        self.decisions.append(resolved)
        self._write_audit(resolved)
        return resolved

    def _write_audit(self, decision: MonitorDecision) -> None:
        if self.audit_writer is None:
            return
        payload = decision.audit_payload
        self.audit_writer(
            user_id=str(payload.get("user_id", "monitor_plugin")),
            role=str(payload.get("role", "system")),
            operation=str(payload.get("operation", f"monitor_{decision.call_type}")),
            input_content=str(payload.get("input_content", "")),
            result=str(payload.get("result", decision.reason)),
            risk_level=str(payload.get("risk_level", decision.risk_level)),
        )

    def _tool_call(self, payload: dict[str, Any], *, call_type: CallType = "tool_call") -> MonitorDecision:
        tool_name = str(payload.get("tool_name") or payload.get("name") or "")
        arguments = dict(payload.get("arguments") or payload.get("tool_arguments") or {})
        policy = evaluate_policy(
            tool_name,
            arguments,
            state=payload.get("state"),
            workspace_root=self.workspace_root,
        )
        return self._decision(
            call_type,
            policy.decision,
            policy.reason or ("allowed" if policy.decision == "allow" else "requires review"),
            policy.risk_level,
            payload,
            extra={
                "tool_name": tool_name,
                "rule_name": policy.detail.get("rule_name"),
                "blocked_reason": policy.detail.get("blocked_reason"),
            },
        )

    def _llm_input(self, payload: dict[str, Any]) -> MonitorDecision:
        text = _payload_text(payload)
        blocked, message = check_malicious_input(text)
        return self._decision(
            "llm_input",
            "deny" if blocked else "allow",
            message,
            "high" if blocked else "normal",
            payload,
        )

    def _llm_output(self, payload: dict[str, Any]) -> MonitorDecision:
        text = _payload_text(payload)
        compliant, message = check_output_compliance(text)
        sanitized = mask_sensitive_info(text)
        sanitized_payload = dict(payload)
        sanitized_payload["content"] = sanitized
        return self._decision(
            "llm_output",
            "allow" if compliant else "deny",
            message or "output checked",
            "high" if not compliant else "normal",
            payload,
            sanitized_payload=sanitized_payload,
        )

    def _tool_result(self, payload: dict[str, Any]) -> MonitorDecision:
        text = _payload_text(payload)
        sanitized = mask_sensitive_info(text)
        sanitized_payload = dict(payload)
        sanitized_payload["content"] = sanitized
        return self._decision("tool_result", "allow", "tool result audited", "normal", payload, sanitized_payload=sanitized_payload)

    def _code_execution(self, payload: dict[str, Any]) -> MonitorDecision:
        request = CodeExecutionRequest.model_validate(payload)
        guarded = evaluate_code_execution(request, workspace_root=self.workspace_root)
        return self._decision(
            "code_execution",
            guarded.decision,
            guarded.reason,
            guarded.risk_level,
            payload,
            extra={
                "sandbox_required": guarded.sandbox_required,
                "artifact_plan": guarded.artifact_plan,
            },
        )

    def _decision(
        self,
        call_type: CallType,
        decision: DecisionValue,
        reason: str,
        risk_level: str,
        payload: dict[str, Any],
        *,
        sanitized_payload: dict[str, Any] | None = None,
        extra: dict[str, Any] | None = None,
    ) -> MonitorDecision:
        ask_id = _ask_id(call_type, payload) if decision == "ask" else None
        audit_payload = {
            "user_id": "monitor_plugin",
            "role": "system",
            "operation": f"monitor_{call_type}",
            "input_content": json.dumps(_safe_payload(payload), ensure_ascii=False, sort_keys=True)[:500],
            "result": f"{decision}: {reason}",
            "risk_level": risk_level,
            "decision": decision,
            "ask_id": ask_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        if extra:
            audit_payload.update(extra)
        return MonitorDecision(
            call_type=call_type,
            decision=decision,
            allowed=decision == "allow",
            reason=reason,
            risk_level=risk_level,
            sanitized_payload=sanitized_payload,
            audit_payload=audit_payload,
            ask_id=ask_id,
            approval_state="pending" if decision == "ask" else "not_required",
        )


def _payload_text(payload: dict[str, Any]) -> str:
    for key in ("content", "text", "prompt", "output"):
        if key in payload:
            return str(payload[key])
    return json.dumps(_safe_payload(payload), ensure_ascii=False, sort_keys=True)


def _safe_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return {str(k): v for k, v in payload.items() if k not in {"state"}}


def _ask_id(call_type: str, payload: dict[str, Any]) -> str:
    raw = json.dumps({"call_type": call_type, "payload": _safe_payload(payload)}, ensure_ascii=False, sort_keys=True)
    return "ask-" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
