from redsentinel.application.engine.attack_pack import (
    load_ecommerce_attack_pack,
    load_openmanus_attack_pack,
)


def test_ecommerce_attack_pack_loads_required_metadata() -> None:
    pack = load_ecommerce_attack_pack()

    assert pack.schema_version == "ecommerce-attack-pack-v0.1"
    assert len(pack.scenarios) >= 16
    categories = {item.category for item in pack.scenarios}
    assert {"direct_injection", "data_exfiltration", "business_logic_abuse"} <= categories
    scenario_ids = {item.scenario_id for item in pack.scenarios}
    assert {
        "cross-user-profile-access",
        "coupon-owner-mismatch",
        "address-owner-mismatch-checkout",
        "support-ticket-cross-order",
        "excessive-cart-stock",
        "payment-replay-paid-order",
        "merchant-cross-shop-price-update",
        "role-mismatch-admin-claim",
    } <= scenario_ids
    for scenario in pack.scenarios:
        assert scenario.attack_spec_id
        assert scenario.business_impact
        assert scenario.success_criteria
        assert scenario.clean_steps
        assert scenario.controlled_steps


def test_openmanus_v02_uses_controlled_canaries_and_complete_clean_input() -> None:
    pack = load_openmanus_attack_pack()
    scenarios = {scenario.scenario_id: scenario for scenario in pack.scenarios}

    assert pack.schema_version == "openmanus-attack-pack-v0.2"
    assert scenarios["file-op-path-traversal"].baseline_success_markers == [
        "REDSENTINEL_TRAVERSAL_CANARY_7F3A"
    ]
    assert scenarios["prompt-injection-ignore"].baseline_success_markers == [
        "REDSENTINEL_INDIRECT_INJECTION_ACCEPTED"
    ]
    assert scenarios["jailbreak-roleplay"].baseline_success_markers == [
        "REDSENTINEL_JAILBREAK_ACCEPTED"
    ]
    assert "BIPIA text attack benchmark" in scenarios["prompt-injection-ignore"].source_reference
    assert "BIPIA Base Encoding attack family" in scenarios["jailbreak-roleplay"].source_reference
    prompt_clean = scenarios["prompt-injection-ignore"].clean_steps[0].message
    assert "本周需要完成 OpenManus 安全评测" in prompt_clean
