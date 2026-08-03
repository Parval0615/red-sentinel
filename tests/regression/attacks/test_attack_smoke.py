from pathlib import Path

from redsentinel.attacks.engine.indirect_injection import HTML_POISON_SCENARIOS, generate_html_poison
from redsentinel.attacks.engine.payloads import ALL_PAYLOADS, CATEGORIES
from redsentinel.attacks.engine.payloads.injection import INJECTION_PAYLOADS
from redsentinel.attacks.engine.payloads.jailbreak import JAILBREAK_PAYLOADS
from redsentinel.attacks.engine.payloads.leakage import LEAKAGE_PAYLOADS
from redsentinel.attacks.engine.payloads.obfuscation import OBFUSCATION_PAYLOADS
from redsentinel.attacks.engine.threat_taxonomy import THREAT_CATEGORIES


def test_payload_database_has_expected_categories() -> None:
    assert ALL_PAYLOADS
    assert {"direct_injection", "jailbreak", "prompt_leakage", "obfuscation"} <= set(CATEGORIES)


def test_t6_jailbreak_and_leakage_payload_metadata_is_enumerable() -> None:
    all_ids = {payload["id"] for payload in ALL_PAYLOADS}
    t6_ids = {
        "jail_t6_001",
        "jail_t6_002",
        "jail_t6_003",
        "jail_t6_004",
        "jail_t6_005",
        "leak_t6_001",
        "leak_t6_002",
        "leak_t6_003",
        "leak_t6_004",
    }
    assert t6_ids <= all_ids

    reusable_ids = {payload["id"] for payload in INJECTION_PAYLOADS + OBFUSCATION_PAYLOADS}
    jailbreak_required_fields = {
        "id",
        "category",
        "subcategory",
        "content",
        "severity",
        "expected_block",
        "bypasses_keyword_check",
        "taxonomy_category",
        "attack_goal",
        "expected_violation",
        "success_criteria",
        "defense_recommendations",
        "related_payload_ids",
    }
    leakage_required_fields = jailbreak_required_fields | {
        "sensitive_info_type",
        "leakage_success_criteria",
        "evidence_fields",
    }

    jailbreak_t6 = [payload for payload in JAILBREAK_PAYLOADS if payload["id"].startswith("jail_t6_")]
    leakage_t6 = [payload for payload in LEAKAGE_PAYLOADS if payload["id"].startswith("leak_t6_")]
    assert {
        "roleplay",
        "rule_override",
        "stepwise_induction",
        "encoded_obfuscation",
        "multi_turn_context_bypass",
    } <= {payload["subcategory"] for payload in jailbreak_t6}
    assert {
        "training_sample_regurgitation",
        "system_prompt_extraction",
        "privacy_credential_induction",
        "business_kb_extraction",
    } <= {payload["subcategory"] for payload in leakage_t6}

    related_ids = []
    for payload in JAILBREAK_PAYLOADS:
        assert jailbreak_required_fields <= set(payload), f"missing fields in {payload['id']}"
        assert payload["category"] == "jailbreak"
        assert payload["taxonomy_category"] == "prompt_injection"
        assert payload["taxonomy_category"] in THREAT_CATEGORIES
        related_ids.extend(payload["related_payload_ids"])
    for payload in LEAKAGE_PAYLOADS:
        assert leakage_required_fields <= set(payload), f"missing fields in {payload['id']}"
        assert payload["category"] == "prompt_leakage"
        assert payload["taxonomy_category"] == "sensitive_leakage"
        assert payload["taxonomy_category"] in THREAT_CATEGORIES
        assert payload["evidence_fields"]
        related_ids.extend(payload["related_payload_ids"])

    assert related_ids
    assert any(related_id.startswith("inj_") for related_id in related_ids)
    assert any(related_id.startswith("obf_") for related_id in related_ids)
    assert set(related_ids) <= reusable_ids


def test_indirect_injection_generator_writes_html(tmp_path: Path) -> None:
    output = tmp_path / "poison.html"
    html, metadata = generate_html_poison(HTML_POISON_SCENARIOS[0], str(output))

    assert output.exists()
    assert metadata["format"] == "html"
    assert metadata["scenario_id"]
    assert "<html" in html.lower()
    assert output.read_text(encoding="utf-8") == html
