from auto_defense_system.security.policy.engine import check_policy, reset_policy_rules


def test_policy_engine_returns_allow_ask_and_deny_states() -> None:
    reset_policy_rules()

    allowed, message, detail = check_policy("db_query", {"sql": "SELECT * FROM users"})

    assert allowed is True
    assert message == ""
    assert detail["decision"] == "allow"
    assert detail["pending"] is False
    assert detail["rule_name"] == "db_query.passed"

    allowed, message, detail = check_policy(
        "file_operation",
        {"path": "/tmp/red-sentinel-report.txt", "action": "write"},
    )

    assert allowed is False
<<<<<<< HEAD
    assert "人工确认" in message
    assert detail["decision"] == "ask"
    assert detail["pending"] is True
    assert detail["rule_name"] == "file_operation.ask_actions"
=======
    assert "确认" in message
    assert detail["decision"] == "ask"
    assert detail["pending"] is True
    assert detail["rule_name"] == "file_operation.ask_write"
>>>>>>> origin/main

    allowed, message, detail = check_policy("db_query", {"sql": "DROP TABLE users"})

    assert allowed is False
    assert "SQL" in message
    assert detail["decision"] == "deny"
    assert detail["pending"] is False
    assert detail["rule_name"] == "db_query.block_sql_keywords"
