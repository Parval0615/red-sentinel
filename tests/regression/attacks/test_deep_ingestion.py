from __future__ import annotations

from pathlib import Path

from redsentinel.attacks.engine.ingestion import build_deep_ingestion_plan, load_agent_materials


def test_build_deep_ingestion_plan_for_docker_materials(tmp_path: Path) -> None:
    (tmp_path / "src").mkdir()
    material_path = tmp_path / "materials.yaml"
    material_path.write_text(
        """
schema_version: agent-materials-v1
agent:
  name: docker_agent
  domain: support
  root_path: src
integration:
  type: docker
  docker_image: local/redsentinel-agent:test
  adapter_entrypoint: adapter:invoke
nodes:
  - id: input
    type: input_node
    target: adapter:normalize
  - id: tool_executor
    type: tool_node
    target: adapter:invoke
evaluation:
  attack_entries:
    - prompt
""".strip(),
        encoding="utf-8",
    )

    plan = build_deep_ingestion_plan(load_agent_materials(material_path), base_dir=tmp_path)

    assert plan.docker_trace_plan is not None
    assert plan.docker_trace_plan.docker_image == "local/redsentinel-agent:test"
    assert plan.docker_trace_plan.node_targets == ["adapter:normalize", "adapter:invoke"]
    assert plan.docker_trace_plan.network_policy == "disabled"
    assert plan.source_roots == [str((tmp_path / "src").resolve())]


def test_build_deep_ingestion_plan_without_docker_keeps_source_roots(tmp_path: Path) -> None:
    (tmp_path / "agent_src").mkdir()
    material_path = tmp_path / "materials.yaml"
    material_path.write_text(
        """
schema_version: agent-materials-v1
agent:
  name: source_agent
  domain: support
integration:
  type: source
  source_path: agent_src
evaluation:
  attack_entries:
    - prompt
""".strip(),
        encoding="utf-8",
    )

    plan = build_deep_ingestion_plan(load_agent_materials(material_path), base_dir=tmp_path)

    assert plan.docker_trace_plan is None
    assert plan.source_roots == [str((tmp_path / "agent_src").resolve())]
