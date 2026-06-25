from __future__ import annotations

from pathlib import Path

from auto_attack_system.ingestion.materials import inspect_materials, load_agent_materials


def test_load_agent_materials_from_directory_and_score_api_completeness(tmp_path: Path) -> None:
    openapi_path = tmp_path / "openapi.yaml"
    openapi_path.write_text("openapi: 3.0.0\npaths: {}\n", encoding="utf-8")
    material_path = tmp_path / "redsentinel.materials.yaml"
    material_path.write_text(
        """
schema_version: agent-materials-v1
agent:
  name: support_agent
  domain: customer_support
integration:
  type: api
  openapi_path: openapi.yaml
nodes:
  - id: input
    type: input_node
    target: adapter:normalize
evaluation:
  attack_entries:
    - prompt
""".strip(),
        encoding="utf-8",
    )

    materials = load_agent_materials(tmp_path)
    inspection = inspect_materials(materials, base_dir=tmp_path)

    assert materials.agent.name == "support_agent"
    assert inspection.integration_type == "api"
    assert inspection.completeness_score == 1.0
    assert inspection.missing == []
    assert inspection.resource_paths["openapi_path"] == str(openapi_path.resolve())


def test_inspect_materials_reports_missing_api_materials(tmp_path: Path) -> None:
    material_path = tmp_path / "materials.yaml"
    material_path.write_text(
        """
schema_version: agent-materials-v1
agent:
  name: thin_api_agent
integration:
  type: api
""".strip(),
        encoding="utf-8",
    )

    materials = load_agent_materials(material_path)
    inspection = inspect_materials(materials, base_dir=tmp_path)

    assert inspection.completeness_score < 1.0
    assert set(inspection.missing) >= {"agent.domain", "nodes", "tools_or_openapi", "openapi_path"}
