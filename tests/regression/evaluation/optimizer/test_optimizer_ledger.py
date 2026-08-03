from redsentinel.evaluation.engine.optimizer.ledger import build_ledger_entry, verify_ledger_entries


def test_ledger_entries_chain_hashes_and_verify() -> None:
    first = build_ledger_entry(
        artifact_type="agent_security_report",
        artifact_id="report-001",
        payload={"score": 95},
        previous_hash=None,
        sequence=0,
    )
    second = build_ledger_entry(
        artifact_type="optimization_directive",
        artifact_id="directive-001",
        payload={"risk_type": "prompt_injection"},
        previous_hash=first.entry_hash,
        sequence=1,
    )

    verification = verify_ledger_entries([first, second])

    assert first.previous_hash is None
    assert second.previous_hash == first.entry_hash
    assert verification.valid is True
    assert verification.total_entries == 2
    assert verification.first_invalid_sequence is None


def test_ledger_verification_detects_payload_tampering() -> None:
    entry = build_ledger_entry(
        artifact_type="agent_security_report",
        artifact_id="report-001",
        payload={"score": 95},
        previous_hash=None,
        sequence=0,
    )
    tampered = entry.model_copy(update={"payload_hash": "sha256:tampered"})

    verification = verify_ledger_entries([tampered])

    assert verification.valid is False
    assert verification.first_invalid_sequence == 0
    assert verification.errors == ["sequence 0 payload hash mismatch"]


def test_ledger_verification_detects_broken_previous_hash() -> None:
    first = build_ledger_entry(
        artifact_type="agent_security_report",
        artifact_id="report-001",
        payload={"score": 95},
        previous_hash=None,
        sequence=0,
    )
    second = build_ledger_entry(
        artifact_type="optimization_directive",
        artifact_id="directive-001",
        payload={"risk_type": "prompt_injection"},
        previous_hash="sha256:wrong",
        sequence=1,
    )

    verification = verify_ledger_entries([first, second])

    assert verification.valid is False
    assert verification.first_invalid_sequence == 1
    assert verification.errors == ["sequence 1 previous hash mismatch"]
