from __future__ import annotations

import json
from pathlib import Path

from agent_integration_system.profiling import analyze_source_profile
from agent_integration_system.profiling.llm_client import LLMClient


def run_eval(root: str | Path = "agent_integration_system/examples/profiler_eval") -> list[dict]:
    client = LLMClient()
    root_path = Path(root)
    results: list[dict] = []
    for case_dir in sorted(item for item in root_path.iterdir() if item.is_dir()):
        expected_path = case_dir / "expected_profile.json"
        if not expected_path.exists():
            continue
        expected = json.loads(expected_path.read_text(encoding="utf-8"))
        ast_result = analyze_source_profile(case_dir, enable_llm=False)
        llm_result = analyze_source_profile(case_dir, enable_llm=True, llm_client=client)
        expected_nodes = {item["id"] for item in expected.get("expected_nodes", [])}
        expected_risks = set(expected.get("expected_risks", []))
        results.append(
            {
                "case": case_dir.name,
                "ast_node_recall": _recall({node.id for node in ast_result.candidate_profile.nodes}, expected_nodes),
                "llm_node_recall": _recall({node.id for node in llm_result.candidate_profile.nodes}, expected_nodes),
                "ast_risk_recall": _recall(_risks(ast_result), expected_risks),
                "llm_risk_recall": _recall(_risks(llm_result), expected_risks),
                "llm_used": llm_result.llm_used,
                "failed_safe": llm_result.failed_safe,
                "warnings": llm_result.notes,
            }
        )
    output = Path("runs/llm_profiler_eval.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(results, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return results


def _risks(result) -> set[str]:
    risks: set[str] = set()
    for node in result.candidate_profile.nodes:
        risks.update(node.risk_surfaces)
    return risks


def _recall(predicted: set[str], expected: set[str]) -> float:
    if not expected:
        return 1.0
    return round(len(predicted & expected) / len(expected), 4)


def main() -> int:
    print(json.dumps(run_eval(), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
