from __future__ import annotations

from pathlib import Path

from redsentinel.profiling import analyze_source_profile


class FakeValidLLMClient:
    model = "fake-valid-model"

    def complete_json(self, messages):
        return {
            "nodes": [
                {
                    "id": "refund_tool_llm",
                    "type": "tool_node",
                    "target": "app:refund_tool_llm",
                    "risk_surfaces": ["tool_abuse", "parameter_tampering"],
                    "confidence": 0.82,
                    "evidence": [
                        {
                            "file": "app.py",
                            "line_start": 1,
                            "line_end": 3,
                            "reason": "function executes refund-like side effect",
                        }
                    ],
                }
            ],
            "tools": [
                {
                    "name": "execute_refund",
                    "risk_level": "high",
                    "side_effect": True,
                    "permissions": ["refund:write"],
                    "evidence": [
                        {
                            "file": "app.py",
                            "line_start": 1,
                            "line_end": 3,
                            "reason": "refund function likely modifies order state",
                        }
                    ],
                }
            ],
            "warnings": [],
        }


class FakeInvalidLLMClient:
    model = "fake-invalid-model"

    def complete_json(self, messages):
        return {
            "nodes": [
                {
                    "id": "bad_node",
                    "type": "unknown_node_type",
                    "target": "app:bad",
                    "risk_surfaces": ["not_allowed_risk"],
                    "confidence": 1.2,
                    "evidence": [],
                }
            ],
            "tools": [],
            "warnings": [],
        }


def test_ast_baseline_runs_without_llm(tmp_path: Path) -> None:
    app = tmp_path / "app.py"
    app.write_text(
        "def retrieve_docs(q):\n"
        "    return []\n\n"
        "def execute_refund(order_id):\n"
        "    return True\n",
        encoding="utf-8",
    )

    result = analyze_source_profile(tmp_path, enable_llm=False)

    assert result.source == "ast_baseline"
    assert result.llm_used is False
    assert result.candidate_profile.nodes
    assert result.diff.added_nodes
    assert result.ast_summary["files"]


def test_ast_plus_llm_merges_valid_patch(tmp_path: Path) -> None:
    app = tmp_path / "app.py"
    app.write_text(
        "def execute_refund(order_id):\n"
        "    charged = True\n"
        "    return charged\n",
        encoding="utf-8",
    )

    result = analyze_source_profile(tmp_path, enable_llm=True, llm_client=FakeValidLLMClient())

    assert result.source == "ast_plus_llm"
    assert result.llm_used is True
    assert result.failed_safe is False
    assert result.llm_model == "fake-valid-model"
    assert "refund_tool_llm" in {node.id for node in result.candidate_profile.nodes}
    assert "execute_refund" in {tool.name for tool in result.candidate_profile.tools}


def test_invalid_llm_patch_fallback_to_ast(tmp_path: Path) -> None:
    app = tmp_path / "app.py"
    app.write_text(
        "def execute_refund(order_id):\n"
        "    return True\n",
        encoding="utf-8",
    )

    result = analyze_source_profile(tmp_path, enable_llm=True, llm_client=FakeInvalidLLMClient())

    assert result.source == "ast_baseline_fallback"
    assert result.llm_used is False
    assert result.failed_safe is True
    assert result.candidate_profile.nodes
    assert any("LLM profiling failed" in item for item in result.notes)


def test_llm_evidence_must_reference_ast_summary_file_and_lines(tmp_path: Path) -> None:
    app = tmp_path / "app.py"
    app.write_text(
        "def execute_refund(order_id):\n"
        "    return True\n",
        encoding="utf-8",
    )

    class FakeBadEvidenceClient:
        model = "fake-bad-evidence"

        def complete_json(self, messages):
            return {
                "nodes": [
                    {
                        "id": "fake_node",
                        "type": "tool_node",
                        "target": "missing:fake",
                        "risk_surfaces": ["tool_abuse"],
                        "confidence": 0.8,
                        "evidence": [
                            {
                                "file": "missing.py",
                                "line_start": 1,
                                "line_end": 2,
                                "reason": "fake evidence",
                            }
                        ],
                    }
                ],
                "tools": [],
                "warnings": [],
            }

    result = analyze_source_profile(tmp_path, enable_llm=True, llm_client=FakeBadEvidenceClient())

    assert result.source == "ast_baseline_fallback"
    assert result.failed_safe is True
