from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from redsentinel.defenses.engine.monitor_plugin import intercept
from redsentinel.defenses.engine.security.policy.engine import check_policy, reset_policy_rules
from redsentinel.attacks.engine.scripts import build_case_sets
from redsentinel.attacks.engine.threat_taxonomy import THREAT_CATEGORIES


ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "pyproject.toml").is_file())
SCENARIOS = tuple(build_case_sets.SCENARIO_DEFINITIONS)
REQUIRED_FIELDS = build_case_sets.REQUIRED_CASE_FIELDS
CONTROLLED_TOOL_NAMES = build_case_sets.CONTROLLED_TOOL_NAMES
TOOL_CASE_REQUIRED_FIELDS = set(build_case_sets.TOOL_CASE_FIELDS)
TOOL_CASE_SCENARIOS = {"tool_tampering", "goal_drift"}
BENIGN_CASE_PATH = ROOT / "docs" / "attack_scenarios" / "_benign" / "benign_cases.jsonl"
BENIGN_REQUIRED_FIELDS = {
    "id",
    "scenario",
    "canonical_category",
    "expected_block",
    "call_type",
    "payload_content",
    "success_criteria",
}
BENIGN_TOOL_NAMES = CONTROLLED_TOOL_NAMES


def test_case_sets_exist_with_required_fields_and_counts() -> None:
    seen_case_ids: set[str] = set()

    for scenario in SCENARIOS:
        definition = build_case_sets.SCENARIO_DEFINITIONS[scenario]
        path = ROOT / "docs" / "attack_scenarios" / scenario / "cases.jsonl"
        cases = _load_jsonl(path)

        assert len(cases) >= 15
        for case in cases:
            assert REQUIRED_FIELDS <= set(case)
            assert case["id"] not in seen_case_ids
            seen_case_ids.add(case["id"])
            assert case["scenario"] == scenario
            assert case["category"] == scenario
            assert case["canonical_category"] == definition.canonical_category
            assert case["canonical_category"] in THREAT_CATEGORIES
            assert case["script_entry"] == definition.script_entry
            assert case["payload_id"] == case["payload_source"]["payload_id"]
            assert str(case["attack_goal"]).strip()
            assert str(case["expected_violation"]).strip()
            assert isinstance(case["success_criteria"], list)
            assert all(str(item).strip() for item in case["success_criteria"])
            if scenario in TOOL_CASE_SCENARIOS:
                _assert_tool_call_case(case)
            _assert_payload_source_traceable(case["payload_source"])


def test_case_sets_match_generator_payload_selection() -> None:
    generated = build_case_sets.build_case_sets()
    build_case_sets.validate_case_sets(generated)

    for scenario, generated_cases in generated.items():
        path = ROOT / "docs" / "attack_scenarios" / scenario / "cases.jsonl"
        disk_cases = _load_jsonl(path)
        assert [case["payload_id"] for case in disk_cases] == [
            case["payload_id"] for case in generated_cases
        ]
        if scenario in TOOL_CASE_SCENARIOS:
            assert [_tool_call_signature(case) for case in disk_cases] == [
                _tool_call_signature(case) for case in generated_cases
            ]


def test_case_set_builder_dry_run_outputs_seven_scenarios(capsys: Any) -> None:
    assert build_case_sets.main(["--dry-run"]) == 0
    output = json.loads(capsys.readouterr().out)

    assert output["mode"] == "dry-run"
    assert output["scenario_count"] == 7
    assert {item["scenario"] for item in output["scenarios"]} == set(SCENARIOS)
    assert all(item["case_count"] >= 15 for item in output["scenarios"])


def test_attack_scenario_scripts_import_and_dry_run_without_asr(capsys: Any) -> None:
    for scenario in SCENARIOS:
        module = importlib.import_module(f"redsentinel.attacks.engine.scripts.attack_{scenario}")
        assert module.main(["--dry-run"]) == 0
        output = json.loads(capsys.readouterr().out)

        assert output["scenario"] == scenario
        assert output["mode"] == "dry-run"
        assert output["case_count"] >= 15
        assert output["metrics"]["asr"] is None
        assert output["metrics"]["status"] == "not_evaluated"


def test_benign_cases_exist_with_expected_distribution_and_tool_controls() -> None:
    cases = _load_jsonl(BENIGN_CASE_PATH)
    counts = dict.fromkeys(SCENARIOS, 0)
    seen_case_ids: set[str] = set()

    assert len(cases) == 42
    for case in cases:
        assert BENIGN_REQUIRED_FIELDS <= set(case)
        assert case["id"] not in seen_case_ids
        seen_case_ids.add(case["id"])
        assert case["scenario"] in counts
        counts[case["scenario"]] += 1
        assert (
            case["canonical_category"]
            == build_case_sets.SCENARIO_DEFINITIONS[case["scenario"]].canonical_category
        )
        assert case["expected_block"] is False
        assert str(case["payload_content"]).strip()
        assert isinstance(case["success_criteria"], list)
        assert all(str(item).strip() for item in case["success_criteria"])

        if case["call_type"] == "tool_call":
            assert case["tool_name"] in BENIGN_TOOL_NAMES
            assert isinstance(case["arguments"], dict)
            assert case["arguments"]

    assert counts == dict.fromkeys(SCENARIOS, 6)


def test_benign_tool_tampering_cases_match_monitor_policy_allowlist() -> None:
    reset_policy_rules()
    cases = _load_jsonl(BENIGN_CASE_PATH)
    tool_tampering_cases = [case for case in cases if case["scenario"] == "tool_tampering"]
    cases_by_id = {case["id"]: case for case in tool_tampering_cases}

    assert len(tool_tampering_cases) == 6

    case_004 = cases_by_id["benign_tool_tampering_004"]
    assert case_004["tool_name"] == "api_call"
    assert case_004["arguments"]["method"] == "GET"
    assert (
        case_004["arguments"]["endpoint"]
        == "https://api.internal.com/v1/support/orders/ord_1001/status-summary"
    )
    assert _is_internal_absolute_endpoint(case_004["arguments"]["endpoint"])
    assert case_004["arguments"]["params"] == {"customer_id": "cust_1001"}
    assert case_004["arguments"]["purpose"] == "read_customer_order_status_summary"

    case_006 = cases_by_id["benign_tool_tampering_006"]
    assert case_006["tool_name"] == "api_call"
    assert case_006["arguments"]["method"] == "POST"
    assert case_006["arguments"]["endpoint"] == "https://api.internal.com/v1/support/tickets"
    assert _is_internal_absolute_endpoint(case_006["arguments"]["endpoint"])
    assert case_006["arguments"]["body"]["priority"] == "normal"

    for case in tool_tampering_cases:
        decision = intercept(
            case["call_type"],
            {"tool_name": case["tool_name"], "arguments": case["arguments"]},
        )
        assert decision.decision == "allow", case["id"]


def test_tool_case_sets_cover_policy_decisions_and_required_arguments() -> None:
    reset_policy_rules()
    tool_tampering_cases = _load_jsonl(ROOT / "docs" / "attack_scenarios" / "tool_tampering" / "cases.jsonl")
    goal_drift_cases = _load_jsonl(ROOT / "docs" / "attack_scenarios" / "goal_drift" / "cases.jsonl")

    assert any(_policy_decision(case) == "deny" for case in tool_tampering_cases)
    assert any(_policy_decision(case) == "ask" for case in goal_drift_cases)
    assert any(_has_db_write(case) for case in tool_tampering_cases)
    assert any(_is_external_post(case) or _has_dangerous_file_action(case) for case in tool_tampering_cases)
    assert any(
        _is_external_post(case) and _policy_decision(case) == "deny"
        for case in goal_drift_cases
    )
    assert any(
        case["tool_name"] == "send_email" and _policy_decision(case) == "ask"
        for case in goal_drift_cases
    )
    assert any(
        case["tool_name"] == "file_operation"
        and str(case["arguments"].get("action", "")).lower() in {"write", "append"}
        and _policy_decision(case) == "ask"
        for case in goal_drift_cases
    )


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    assert path.exists()
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _assert_tool_call_case(case: dict[str, Any]) -> None:
    assert TOOL_CASE_REQUIRED_FIELDS <= set(case)
    assert case["call_type"] == "tool_call"
    assert case["tool_name"] in CONTROLLED_TOOL_NAMES
    assert isinstance(case["arguments"], dict)
    assert case["arguments"]


def _tool_call_signature(case: dict[str, Any]) -> tuple[str, str, dict[str, Any]]:
    _assert_tool_call_case(case)
    return case["call_type"], case["tool_name"], case["arguments"]


def _policy_decision(case: dict[str, Any]) -> str:
    allowed, _, detail = check_policy(case["tool_name"], case["arguments"])
    decision = detail.get("decision")
    if decision in {"allow", "deny", "ask"}:
        return str(decision)
    return "allow" if allowed else "deny"


def _has_db_write(case: dict[str, Any]) -> bool:
    if case["tool_name"] != "db_query":
        return False
    sql = str(case["arguments"].get("sql", "")).upper()
    return any(keyword in sql for keyword in ("UPDATE", "INSERT", "DELETE", "DROP", "TRUNCATE", "ALTER", "CREATE"))


def _is_external_post(case: dict[str, Any]) -> bool:
    if case["tool_name"] != "api_call":
        return False
    endpoint = str(case["arguments"].get("endpoint", "")).lower()
    method = str(case["arguments"].get("method", "")).upper()
    internal_markers = ("api.internal.com", "localhost", "127.0.0.1", "internal.", ".local", ".internal")
    return method == "POST" and not any(marker in endpoint for marker in internal_markers)


def _is_internal_absolute_endpoint(endpoint: str) -> bool:
    parsed = urlparse(endpoint)
    return parsed.scheme in {"http", "https"} and parsed.hostname == "api.internal.com"


def _has_dangerous_file_action(case: dict[str, Any]) -> bool:
    if case["tool_name"] != "file_operation":
        return False
    action = str(case["arguments"].get("action", "")).lower()
    return action in {"delete", "overwrite", "chmod", "chown"}


def _assert_payload_source_traceable(source: dict[str, Any]) -> None:
    assert (ROOT / source["path"]).exists()
    module = importlib.import_module(source["module"])
    payloads = getattr(module, source["symbol"])
    assert source["payload_id"] in {payload["id"] for payload in payloads}
