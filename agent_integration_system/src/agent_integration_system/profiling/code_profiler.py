from __future__ import annotations

import ast
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from agent_integration_system.profile.builder import RISK_SURFACES_BY_NODE_TYPE
from auto_evaluation_system.contracts.agent_security import (
    AgentProfile,
    AgentProfileNode,
    AgentProfileTool,
)

NodeTypeName = Literal["input_node", "rag_retriever", "tool_node", "memory_node", "llm_node", "output_node"]

_NODE_KEYWORDS: list[tuple[NodeTypeName, tuple[str, ...]]] = [
    ("input_node", ("input", "normalize", "parse_request")),
    ("rag_retriever", ("retrieve", "retriever", "search_docs", "rag")),
    ("tool_node", ("tool", "execute", "call_api", "action")),
    ("memory_node", ("memory", "remember", "recall", "store")),
    ("output_node", ("output", "format", "render", "respond")),
    ("llm_node", ("agent", "llm", "chat", "invoke", "run")),
]

_HIGH_RISK_TOOL_KEYWORDS = ("delete", "payment", "refund", "update", "create", "write", "send")


class CandidateProfileDiff(BaseModel):
    model_config = ConfigDict(extra="forbid")

    added_nodes: list[str] = Field(default_factory=list)
    added_tools: list[str] = Field(default_factory=list)
    changed_rag_enabled: bool = False
    evidence_refs: list[str] = Field(default_factory=list)


class CodeProfileCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    candidate_profile: AgentProfile
    diff: CandidateProfileDiff
    confidence: float
    notes: list[str] = Field(default_factory=list)


class _FunctionEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    module: str
    name: str
    node_type: NodeTypeName
    path: str

    @property
    def target(self) -> str:
        return f"{self.module}:{self.name}"


def analyze_source_profile(root_path: str | Path, base_profile: AgentProfile) -> CodeProfileCandidate:
    root = Path(root_path).resolve()
    functions = _collect_functions(root)
    existing_targets = {node.target for node in base_profile.nodes}
    existing_tool_names = {tool.name for tool in base_profile.tools}

    added_nodes: list[AgentProfileNode] = []
    added_tools: list[AgentProfileTool] = []
    evidence_refs: list[str] = []
    for item in functions:
        evidence_refs.append(item.path)
        if item.target not in existing_targets:
            added_nodes.append(
                AgentProfileNode(
                    id=_node_id(item),
                    type=item.node_type,
                    target=item.target,
                    risk_surfaces=list(RISK_SURFACES_BY_NODE_TYPE[item.node_type]),
                )
            )
        if item.node_type == "tool_node" and item.name not in existing_tool_names:
            added_tools.append(
                AgentProfileTool(
                    name=item.name,
                    risk_level=_tool_risk(item.name),
                    side_effect=_tool_risk(item.name) in {"high", "critical"},
                )
            )

    candidate = base_profile.model_copy(
        update={
            "nodes": [*base_profile.nodes, *added_nodes],
            "tools": [*base_profile.tools, *added_tools],
            "rag_enabled": base_profile.rag_enabled or any(item.node_type == "rag_retriever" for item in functions),
        }
    )
    diff = CandidateProfileDiff(
        added_nodes=[node.id for node in added_nodes],
        added_tools=[tool.name for tool in added_tools],
        changed_rag_enabled=candidate.rag_enabled != base_profile.rag_enabled,
        evidence_refs=sorted(set(evidence_refs)),
    )
    return CodeProfileCandidate(
        candidate_profile=candidate,
        diff=diff,
        confidence=_confidence(functions),
        notes=_notes(root, functions, diff),
    )


def _collect_functions(root: Path) -> list[_FunctionEvidence]:
    if not root.exists():
        return []
    files = [root] if root.is_file() else sorted(root.rglob("*.py"))
    items: list[_FunctionEvidence] = []
    for path in files:
        if "__pycache__" in path.parts:
            continue
        module = _module_name(root, path)
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                node_type = _classify_function(node.name)
                if node_type:
                    items.append(
                        _FunctionEvidence(
                            module=module,
                            name=node.name,
                            node_type=node_type,
                            path=str(path),
                        )
                    )
    return items


def _classify_function(name: str) -> NodeTypeName | None:
    lowered = name.lower()
    for node_type, keywords in _NODE_KEYWORDS:
        if any(keyword in lowered for keyword in keywords):
            return node_type
    return None


def _module_name(root: Path, path: Path) -> str:
    if root.is_file():
        return path.stem
    relative = path.relative_to(root).with_suffix("")
    return ".".join(relative.parts)


def _node_id(item: _FunctionEvidence) -> str:
    return item.name.lower().replace("__", "_")


def _tool_risk(name: str) -> str:
    lowered = name.lower()
    if "delete" in lowered or "payment" in lowered:
        return "critical"
    if any(keyword in lowered for keyword in _HIGH_RISK_TOOL_KEYWORDS):
        return "high"
    return "medium"


def _confidence(functions: list[_FunctionEvidence]) -> float:
    if not functions:
        return 0.0
    node_types = {item.node_type for item in functions}
    return round(min(0.95, 0.35 + 0.1 * len(node_types)), 4)


def _notes(root: Path, functions: list[_FunctionEvidence], diff: CandidateProfileDiff) -> list[str]:
    notes = [f"Scanned Python source under {root}."]
    if not functions:
        notes.append("No recognizable agent node functions were found.")
    if diff.added_nodes:
        notes.append("Candidate nodes were inferred from function names and should be reviewed.")
    return notes
