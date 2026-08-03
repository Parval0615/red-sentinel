from __future__ import annotations

from pathlib import Path

from redsentinel.profiling.manifest import load_agent_config
from redsentinel.profiling.builder import build_agent_security_profile
from redsentinel.profiling import analyze_source_profile

EXAMPLE_CONFIG = next(parent for parent in Path(__file__).resolve().parents if (parent / "pyproject.toml").is_file()) / "examples" / "agents" / "simple_agent" / "redsentinel.yaml"


def test_code_profiler_generates_auditable_candidate_diff(tmp_path: Path) -> None:
    app_path = tmp_path / "app.py"
    app_path.write_text(
        """
def normalize_input(message):
    return message.strip()

def retrieve_policy(query):
    return []

def execute_refund_tool(arguments):
    return {"ok": True}

def remember_user_preference(user_id, value):
    return value
""".strip(),
        encoding="utf-8",
    )
    config = load_agent_config(EXAMPLE_CONFIG)
    base_profile = build_agent_security_profile(config)

    candidate = analyze_source_profile(tmp_path, base_profile)

    assert candidate.confidence > 0
    assert "execute_refund_tool" in candidate.diff.added_tools
    assert candidate.diff.added_nodes
    assert candidate.candidate_profile.rag_enabled is True
    assert any(str(app_path) == ref["file"] for ref in candidate.diff.evidence_refs)
    assert all({"file", "line_start", "line_end", "reason"} <= set(ref) for ref in candidate.diff.evidence_refs)
    assert any("tool_node" in str(ref["reason"]) for ref in candidate.diff.evidence_refs)


def test_code_profiler_keeps_base_profile_unchanged() -> None:
    config = load_agent_config(EXAMPLE_CONFIG)
    base_profile = build_agent_security_profile(config)

    candidate = analyze_source_profile(EXAMPLE_CONFIG.parent, base_profile)

    assert len(base_profile.nodes) == 4
    assert len(candidate.candidate_profile.nodes) >= len(base_profile.nodes)
    assert candidate.candidate_profile.agent_name == base_profile.agent_name
