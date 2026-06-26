from __future__ import annotations

from pathlib import Path

from auto_attack_system.ingestion import build_agent_perception_from_path


def test_perception_source_materials_build_code_candidate_with_evidence(tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    app = src / "app.py"
    app.write_text(
        """
def run_agent(message):
    return retrieve_docs(message)

def retrieve_docs(query):
    return []

def execute_refund(arguments):
    return {"ok": True}
""".strip(),
        encoding="utf-8",
    )
    material_path = tmp_path / "materials.yaml"
    material_path.write_text(
        """
schema_version: agent-materials-v1
agent:
  name: source_agent
  domain: ecommerce
  entrypoint: app:run_agent
integration:
  type: source
  source_path: src
business:
  sensitive_data:
    - payment_token
nodes:
  - id: input
    type: input_node
    target: app:run_agent
evaluation:
  attack_entries:
    - prompt
""".strip(),
        encoding="utf-8",
    )

    result = build_agent_perception_from_path(material_path)

    assert result.profile_source == "code_profile"
    assert result.code_candidate is not None
    assert {"retrieve_docs", "execute_refund"} <= set(result.code_candidate.diff.added_nodes)
    assert "execute_refund" in result.code_candidate.diff.added_tools
    assert any(ref["file"] == str(app.resolve()) for ref in result.code_candidate.diff.evidence_refs)
    assert result.standard_profile.agent_name == "source_agent"
    assert "app:run_agent" in {node.target for node in result.standard_profile.nodes}
    assert result.standard_profile.rag_enabled is True


def test_perception_api_materials_build_manifest_profile_without_code_candidate(tmp_path: Path) -> None:
    (tmp_path / "openapi.yaml").write_text(
        """
openapi: 3.0.0
paths:
  /refunds:
    post:
      operationId: createRefund
""".strip(),
        encoding="utf-8",
    )
    material_path = tmp_path / "materials.yaml"
    material_path.write_text(
        """
schema_version: agent-materials-v1
agent:
  name: api_agent
  domain: ecommerce
  entrypoint: adapter:invoke
integration:
  type: api
  openapi_path: openapi.yaml
evaluation:
  attack_entries:
    - prompt
""".strip(),
        encoding="utf-8",
    )

    result = build_agent_perception_from_path(material_path)

    assert result.profile_source == "manifest_draft"
    assert result.code_candidate is None
    assert result.manifest_result.inferred_tools == ["createRefund"]
    assert result.standard_profile.tools[0].name == "createRefund"
    assert result.standard_profile.nodes[1].type == "tool_node"


def test_perception_docker_materials_build_trace_plan_without_runtime_claim(tmp_path: Path) -> None:
    material_path = tmp_path / "materials.yaml"
    material_path.write_text(
        """
schema_version: agent-materials-v1
agent:
  name: docker_agent
  domain: ops
integration:
  type: docker
  docker_image: local/docker-agent:test
  adapter_entrypoint: adapter:invoke
evaluation:
  attack_entries:
    - prompt
""".strip(),
        encoding="utf-8",
    )

    result = build_agent_perception_from_path(material_path)

    assert result.profile_source == "manifest_draft"
    assert result.code_candidate is None
    assert result.deep_plan.docker_trace_plan is not None
    assert result.deep_plan.docker_trace_plan.docker_image == "local/docker-agent:test"
    assert "C-side sandbox owns actual Docker execution" in " ".join(result.deep_plan.docker_trace_plan.notes)
