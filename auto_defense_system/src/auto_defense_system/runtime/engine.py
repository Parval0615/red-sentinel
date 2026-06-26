from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from auto_defense_system.mounting import DefensePlan, GuardMount
from auto_defense_system.security.firewall.input_guard import check_malicious_input
from auto_defense_system.security.goal_guard import GoalGuardInput, evaluate_goal_guard
from auto_defense_system.security.memory_guard import MemoryGuardInput, evaluate_memory_guard
from auto_defense_system.security.output.filter import check_output_compliance, mask_sensitive_info
from auto_defense_system.security.tool_guard import ToolGuardInput, evaluate_tool_guard


RuntimeDecisionValue = Literal["allow", "block"]
RuntimeRiskLevel = Literal["normal", "low", "medium", "high", "critical"]


class RuntimeNodeInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    node_id: str = Field(min_length=1)
    content: str = ""
    evidence: list[dict[str, Any]] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    tool_name: str | None = None
    tool_arguments: dict[str, Any] = Field(default_factory=dict)
    tool_response: Any = None
    memory_namespace: str | None = None
    memory_key: str | None = None
    original_goal: str | None = None
    current_goal: str | None = None
    rag_chunks: list[Any] = Field(default_factory=list)


class RuntimeGuardDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    node_id: str = Field(min_length=1)
    guard_name: str = Field(min_length=1)
    allowed: bool
    decision: RuntimeDecisionValue
    risk_level: RuntimeRiskLevel
    reason: str = Field(min_length=1)
    attribution: list[dict[str, Any]] = Field(default_factory=list)
    sanitized_content: str | None = None
    audit_payload: dict[str, str]


class DefenseRuntime:
    def __init__(self, plan: DefensePlan) -> None:
        self.plan = plan
        self._mounts = {mount.node_id: mount for mount in plan.mounts}

    def evaluate(self, node_input: RuntimeNodeInput) -> RuntimeGuardDecision:
        mount = self._mounts.get(node_input.node_id)
        if mount is None:
            return _decision(
                node_id=node_input.node_id,
                guard_name="unmounted",
                allowed=True,
                reason="allowed_unmounted: no guard mount configured for node.",
            )

        if mount.guard_name == "input_firewall":
            return self._evaluate_input_firewall(mount, node_input)
        if mount.guard_name == "rag_chunk_scanner":
            return self._evaluate_rag_scanner(mount, node_input)
        if mount.guard_name == "tool_guard":
            return self._evaluate_tool_guard(mount, node_input)
        if mount.guard_name == "memory_guard":
            return self._evaluate_memory_guard(mount, node_input)
        if mount.guard_name == "goal_guard":
            return self._evaluate_goal_guard(mount, node_input)
        if mount.guard_name == "output_filter":
            return self._evaluate_output_filter(mount, node_input)
        raise ValueError(f"Unsupported guard mount: {mount.guard_name}")

    def _evaluate_input_firewall(
        self,
        mount: GuardMount,
        node_input: RuntimeNodeInput,
    ) -> RuntimeGuardDecision:
        blocked, message = check_malicious_input(node_input.content)
        return _decision(
            node_id=mount.node_id,
            guard_name=mount.guard_name,
            allowed=not blocked,
            reason=message,
            risk_level="high" if blocked else "normal",
            attribution=[_attribution("input_firewall", message)] if blocked else [],
        )

    def _evaluate_rag_scanner(
        self,
        mount: GuardMount,
        node_input: RuntimeNodeInput,
    ) -> RuntimeGuardDecision:
        chunks = node_input.rag_chunks or [node_input.content]
        scan_results = _scan_retrieved_chunks(chunks)
        blocked = any(item.get("should_filter") for item in scan_results)
        reason = "RAG chunks passed scan."
        if blocked:
            reason = "RAG chunk scanner filtered suspicious retrieval content."
        return _decision(
            node_id=mount.node_id,
            guard_name=mount.guard_name,
            allowed=not blocked,
            reason=reason,
            risk_level="high" if blocked else "normal",
            attribution=[dict(item) for item in scan_results if item.get("should_filter")],
        )

    def _evaluate_tool_guard(
        self,
        mount: GuardMount,
        node_input: RuntimeNodeInput,
    ) -> RuntimeGuardDecision:
        decision = evaluate_tool_guard(
            ToolGuardInput(
                tool_name=node_input.tool_name or mount.target,
                arguments=node_input.tool_arguments,
                response=node_input.tool_response,
                metadata=node_input.metadata,
                evidence=node_input.evidence,
            )
        )
        return _from_guard_decision(mount, decision)

    def _evaluate_memory_guard(
        self,
        mount: GuardMount,
        node_input: RuntimeNodeInput,
    ) -> RuntimeGuardDecision:
        decision = evaluate_memory_guard(
            MemoryGuardInput(
                namespace=node_input.memory_namespace or self.plan.agent_name,
                memory_key=node_input.memory_key or mount.node_id,
                content=node_input.content,
                metadata=node_input.metadata,
                evidence=node_input.evidence,
            )
        )
        return _from_guard_decision(mount, decision)

    def _evaluate_goal_guard(
        self,
        mount: GuardMount,
        node_input: RuntimeNodeInput,
    ) -> RuntimeGuardDecision:
        current_goal = node_input.current_goal or node_input.content
        decision = evaluate_goal_guard(
            GoalGuardInput(
                goal_id=mount.node_id,
                original_goal=node_input.original_goal or current_goal,
                current_goal=current_goal,
                metadata=node_input.metadata,
                evidence=node_input.evidence,
            )
        )
        return _from_guard_decision(mount, decision)

    def _evaluate_output_filter(
        self,
        mount: GuardMount,
        node_input: RuntimeNodeInput,
    ) -> RuntimeGuardDecision:
        compliant, message = check_output_compliance(node_input.content)
        sanitized = mask_sensitive_info(node_input.content)
        has_masking = sanitized != node_input.content
        reason = message
        if compliant and has_masking:
            reason = "Output allowed with sensitive content masked."
        return _decision(
            node_id=mount.node_id,
            guard_name=mount.guard_name,
            allowed=compliant,
            reason=reason,
            risk_level="high" if not compliant else "normal",
            attribution=[_attribution("output_masking", "Sensitive output fields were masked.")] if has_masking else [],
            sanitized_content=sanitized,
        )


def _from_guard_decision(mount: GuardMount, guard_decision: Any) -> RuntimeGuardDecision:
    return RuntimeGuardDecision(
        node_id=mount.node_id,
        guard_name=mount.guard_name,
        allowed=guard_decision.allowed,
        decision=guard_decision.decision,
        risk_level=guard_decision.risk_level,
        reason=guard_decision.reason,
        attribution=[dict(item) for item in guard_decision.attribution],
        audit_payload=dict(guard_decision.audit_payload),
    )


def _decision(
    *,
    node_id: str,
    guard_name: str,
    allowed: bool,
    reason: str,
    risk_level: RuntimeRiskLevel = "normal",
    attribution: list[dict[str, Any]] | None = None,
    sanitized_content: str | None = None,
) -> RuntimeGuardDecision:
    return RuntimeGuardDecision(
        node_id=node_id,
        guard_name=guard_name,
        allowed=allowed,
        decision="allow" if allowed else "block",
        risk_level=risk_level,
        reason=reason,
        attribution=attribution or [],
        sanitized_content=sanitized_content,
        audit_payload={
            "user_id": guard_name,
            "role": "system",
            "operation": "guard_mount_decision",
            "input_content": f"node_id={node_id}",
            "result": f"{'allowed' if allowed else 'blocked'}_{guard_name}: {reason}",
            "risk_level": risk_level,
        },
    )


def _attribution(evidence_type: str, summary: str) -> dict[str, Any]:
    return {
        "evidence_type": evidence_type,
        "summary": summary,
    }


def _scan_retrieved_chunks(chunks: list[Any]) -> list[dict[str, Any]]:
    try:
        from auto_defense_system.security.ingest.doc_scanner import scan_retrieved_chunks
    except ModuleNotFoundError as exc:
        if exc.name != "langchain_openai":
            raise
        return [_fallback_chunk_scan(chunk, index) for index, chunk in enumerate(chunks)]
    return scan_retrieved_chunks(chunks)


def _fallback_chunk_scan(chunk: Any, index: int) -> dict[str, Any]:
    text = chunk.get("text", "") if isinstance(chunk, dict) else str(chunk)
    blocked, message = check_malicious_input(text)
    return {
        "chunk_index": index,
        "text_preview": text[:200],
        "risk_score": 80 if blocked else 0,
        "category": "input_guard_fallback" if blocked else "clean",
        "should_filter": blocked,
        "reasoning": message,
        "layer": 1,
        "l1_flags": ["input_guard_fallback"] if blocked else [],
    }


__all__ = [
    "DefenseRuntime",
    "RuntimeGuardDecision",
    "RuntimeNodeInput",
]
