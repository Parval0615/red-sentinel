from pathlib import Path

from auto_defense_system import config
from auto_defense_system.security.output.filter import mask_sensitive_info
from auto_defense_system.security.policy.engine import check_policy


def test_config_reads_api_key_from_environment() -> None:
    assert config.LLM_API_KEY == ""
    assert "api-inference.modelscope.cn" in config.LLM_API_BASE


def test_policy_engine_blocks_dangerous_sql() -> None:
    allowed, message, detail = check_policy("db_query", {"sql": "DROP TABLE users"})

    assert allowed is False
    assert "SQL" in message
    assert detail["rule_name"] == "db_query.block_sql_keywords"


def test_output_filter_masks_sensitive_values() -> None:
    masked = mask_sensitive_info("phone=13812345678 key=sk-abcdefghijklmnopqrstuvwxyz123456")

    assert "13812345678" not in masked
    assert "sk-abcdefghijklmnopqrstuvwxyz123456" not in masked


def test_audit_hash_chain_roundtrip(tmp_path: Path) -> None:
    from auto_defense_system.security import audit

    old_log_file = audit.LOG_FILE
    audit.LOG_FILE = str(tmp_path / "audit.log")
    try:
        audit.write_audit_log(
            user_id="test",
            role="admin",
            operation="policy_check",
            input_content="db_query",
            result="blocked",
            risk_level="high",
        )
        result = audit.verify_audit_integrity()
    finally:
        audit.LOG_FILE = old_log_file

    assert result["valid"] is True
    assert result["total_entries"] == 1
