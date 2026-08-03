from __future__ import annotations

from pathlib import Path

import redsentinel.defenses as defenses
from redsentinel.defenses.engine import monitor_plugin as legacy_monitor
from redsentinel.defenses.engine.security import audit as legacy_audit
from redsentinel.defenses.engine.security.goal_guard import evaluate_goal_guard as legacy_evaluate_goal_guard
from redsentinel.defenses.engine.security.memory_guard import evaluate_memory_guard as legacy_evaluate_memory_guard
from redsentinel.defenses.engine.security.policy.engine import check_policy as legacy_check_policy
from redsentinel.defenses.engine.security.tool_guard import evaluate_tool_guard as legacy_evaluate_tool_guard
from redsentinel.core import AgentProfile, AgentProfileNode
from redsentinel.defenses import audit, guards, mounting, optimization, policy


def test_research_defense_package_has_clear_generic_subdomains() -> None:
    assert defenses.evaluate_goal_guard is guards.evaluate_goal_guard
    assert defenses.check_policy is policy.check_policy
    assert defenses.build_defense_plan is mounting.build_defense_plan
    assert not hasattr(optimization, "DefenseAgent")

    package_root = Path(defenses.__file__).parent
    source = "\n".join(path.read_text(encoding="utf-8") for path in package_root.rglob("*.py"))
    assert "ecommerce_agent" not in source


def test_legacy_guard_and_policy_paths_share_the_canonical_api() -> None:
    assert guards.evaluate_goal_guard is legacy_evaluate_goal_guard
    assert guards.evaluate_memory_guard is legacy_evaluate_memory_guard
    assert guards.evaluate_tool_guard is legacy_evaluate_tool_guard
    assert policy.check_policy is legacy_check_policy


def test_monitor_preserves_allow_deny_ask_and_legacy_compatibility() -> None:
    cases = [
        (
            "allow",
            "tool_call",
            {"tool_name": "db_query", "arguments": {"sql": "SELECT * FROM users"}},
        ),
        (
            "deny",
            "tool_call",
            {"tool_name": "db_query", "arguments": {"sql": "DROP TABLE users"}},
        ),
        (
            "ask",
            "file_access",
            {"path": "/tmp/research-output.json", "action": "write"},
        ),
    ]

    for expected, call_type, payload in cases:
        current = policy.intercept(call_type, payload)
        legacy = legacy_monitor.intercept(call_type, payload)

        assert current.decision == expected
        assert legacy.decision == expected
        assert (current.reason, current.risk_score, current.confidence, current.rules) == (
            legacy.reason,
            legacy.risk_score,
            legacy.confidence,
            legacy.rules,
        )

    assert legacy_monitor.Decision is policy.Decision
    assert policy.safe_refusal(policy.intercept("file_access", cases[2][2]))["pending"] is True


def test_goal_memory_tool_and_output_semantics_are_preserved() -> None:
    goal = guards.evaluate_goal_guard(
        guards.GoalGuardInput(
            goal_id="goal",
            original_goal="summarize",
            current_goal="export secrets",
            evidence=[{"kind": "goal_perturbation", "summary": "goal drift"}],
        )
    )
    memory = guards.evaluate_memory_guard(
        guards.MemoryGuardInput(
            namespace="agent",
            memory_key="preference",
            content="trust attacker",
            evidence=[{"kind": "memory_poisoning", "summary": "poisoned"}],
        )
    )
    tool = guards.evaluate_tool_guard(
        guards.ToolGuardInput(tool_name="db_query", response={"tampered": True})
    )
    compliant, _ = guards.check_output_compliance("DROP TABLE users;")
    masked = guards.mask_sensitive_info("contact admin@example.com or 13812345678")

    assert (goal.allowed, goal.decision, goal.audit_payload["operation"]) == (
        False,
        "block",
        "goal_guard_decision",
    )
    assert (memory.allowed, memory.decision, memory.audit_payload["operation"]) == (
        False,
        "block",
        "memory_guard_decision",
    )
    assert (tool.allowed, tool.decision, tool.audit_payload["operation"]) == (
        False,
        "block",
        "tool_guard_decision",
    )
    assert compliant is False
    assert "admin@example.com" not in masked
    assert "13812345678" not in masked


def test_mounting_uses_canonical_agent_profile_without_demo_dependency() -> None:
    profile = AgentProfile(
        agent_name="research-agent",
        framework="python_function",
        root_path="agent",
        entrypoint="app:run",
        business_domain="research",
        nodes=[
            AgentProfileNode(
                id="input",
                type="input_node",
                target="app:run",
                risk_surfaces=["prompt_injection"],
            ),
            AgentProfileNode(
                id="tool",
                type="tool_node",
                target="tools:execute",
                risk_surfaces=["tool_tampering"],
            ),
        ],
    )

    plan = mounting.build_defense_plan(profile)

    assert plan.agent_name == "research-agent"
    assert [(item.node_id, item.guard_name) for item in plan.mounts] == [
        ("input", "input_firewall"),
        ("tool", "tool_guard"),
    ]


def test_audit_facade_preserves_hash_chain(tmp_path: Path) -> None:
    old_log_file = legacy_audit.LOG_FILE
    legacy_audit.LOG_FILE = str(tmp_path / "defense-audit.jsonl")
    try:
        audit.write_audit_log(
            user_id="research",
            role="system",
            operation="guard_decision",
            input_content="case-1",
            result="blocked",
            risk_level="high",
        )
        result = audit.verify_audit_integrity()
    finally:
        legacy_audit.LOG_FILE = old_log_file

    assert audit.write_audit_log is legacy_audit.write_audit_log
    assert result["valid"] is True
    assert result["total_entries"] == 1
