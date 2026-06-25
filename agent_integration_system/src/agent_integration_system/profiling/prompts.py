from __future__ import annotations

import json
from typing import Any

from agent_integration_system.profiling.profile_patch import ALLOWED_NODE_TYPES, ALLOWED_RISK_SURFACES

SYSTEM_PROMPT = """You are an Agent security profiling analyzer.

You must output valid JSON only.
You must not modify source code.
You must not modify the official AgentProfile.
You must not generate defense policies.
You may only propose a candidate AgentProfile patch based on provided evidence.

Every proposed node/tool/enabled RAG/enabled memory must include evidence.
Evidence must include file, line_start, line_end and reason.
Use only files and line ranges visible in the AST summary.
Do not include markdown.
Do not include text outside JSON.
"""


def build_llm_messages(ast_summary: dict[str, Any], base_profile: dict[str, Any], materials: dict[str, Any]) -> list[dict[str, str]]:
    payload = {
        "materials": materials,
        "base_profile": base_profile,
        "ast_summary": ast_summary,
        "allowed_node_types": sorted(ALLOWED_NODE_TYPES),
        "allowed_risk_surfaces": sorted(ALLOWED_RISK_SURFACES),
        "output_shape": {
            "nodes": [
                {
                    "id": "string",
                    "type": "one allowed node type",
                    "target": "module:function",
                    "risk_surfaces": ["allowed risk surface"],
                    "confidence": 0.0,
                    "evidence": [{"file": "path.py", "line_start": 1, "line_end": 1, "reason": "why"}],
                }
            ],
            "tools": [
                {
                    "name": "string",
                    "risk_level": "low|medium|high|critical",
                    "side_effect": False,
                    "permissions": [],
                    "evidence": [{"file": "path.py", "line_start": 1, "line_end": 1, "reason": "why"}],
                }
            ],
            "rag": None,
            "memory": None,
            "warnings": [],
        },
    }
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": json.dumps(payload, ensure_ascii=False, sort_keys=True)},
    ]
