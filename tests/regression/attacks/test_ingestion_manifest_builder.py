from __future__ import annotations

from pathlib import Path

from redsentinel.attacks.engine.ingestion.manifest_builder import build_manifest_from_materials
from redsentinel.attacks.engine.ingestion.materials import load_agent_materials
from redsentinel.core.agent_security import AgentManifest


def test_build_manifest_infers_tools_from_openapi(tmp_path: Path) -> None:
    (tmp_path / "openapi.yaml").write_text(
        """
openapi: 3.0.0
paths:
  /orders:
    get:
      operationId: listOrders
    post:
      operationId: createOrder
  /orders/{order_id}:
    delete:
      operationId: deleteOrder
""".strip(),
        encoding="utf-8",
    )
    material_path = tmp_path / "redsentinel.materials.yaml"
    material_path.write_text(
        """
schema_version: agent-materials-v1
agent:
  name: order_api_agent
  domain: ecommerce
  entrypoint: adapter:invoke
integration:
  type: api
  openapi_path: openapi.yaml
business:
  roles:
    - buyer
    - support
  sensitive_data:
    - phone
nodes:
  - id: input
    type: input_node
    target: adapter:normalize
  - id: tool_executor
    type: tool_node
    target: adapter:invoke
  - id: output
    type: output_node
    target: adapter:format_output
evaluation:
  attack_entries:
    - prompt
""".strip(),
        encoding="utf-8",
    )

    result = build_manifest_from_materials(load_agent_materials(material_path), base_dir=tmp_path)
    payload = result.manifest.model_dump(mode="json")

    assert AgentManifest.model_validate(payload) == result.manifest
    assert result.valid is True
    assert result.completeness_score == 1.0
    assert result.missing_fields == []
    assert result.inferred_tools == ["listOrders", "createOrder", "deleteOrder"]
    assert {tool.name: tool.risk_level for tool in result.manifest.tools} == {
        "listOrders": "low",
        "createOrder": "high",
        "deleteOrder": "critical",
    }
    assert result.manifest.agent.framework == "python_function"
    assert result.manifest.business.domain == "ecommerce"
    assert result.manifest.nodes[1].id == "tool_executor"


def test_build_manifest_generates_draft_nodes_for_docker_materials(tmp_path: Path) -> None:
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
  adapter_entrypoint: docker_adapter:invoke
evaluation:
  attack_entries:
    - prompt
""".strip(),
        encoding="utf-8",
    )

    result = build_manifest_from_materials(load_agent_materials(material_path), base_dir=tmp_path)

    assert [node.id for node in result.manifest.nodes] == ["input", "docker_executor", "output"]
    assert result.valid is False
    assert "nodes" in result.missing_fields
    assert result.manifest.agent.entrypoint == "docker_adapter:invoke"
    assert "Docker runtime trajectory collection is reserved for M5" in " ".join(result.notes)


def test_build_manifest_handles_source_materials(tmp_path: Path) -> None:
    (tmp_path / "src").mkdir()
    material_path = tmp_path / "materials.yaml"
    material_path.write_text(
        """
schema_version: agent-materials-v1
agent:
  name: source_agent
  domain: support
  entrypoint: app:run
integration:
  type: source
  source_path: src
nodes:
  - id: input
    type: input_node
    target: app:normalize
evaluation:
  attack_entries:
    - prompt
""".strip(),
        encoding="utf-8",
    )

    result = build_manifest_from_materials(load_agent_materials(material_path), base_dir=tmp_path)

    assert result.valid is False
    assert result.manifest.agent.root_path == "src"
    assert result.manifest.agent.entrypoint == "app:run"
    assert "tools_or_openapi" in result.missing_fields
