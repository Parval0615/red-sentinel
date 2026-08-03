from __future__ import annotations

from pathlib import Path

from redsentinel.attacks.engine.ingestion.perception import build_agent_perception_from_path


def test_deep_ingestion_source_with_static_analysis(tmp_path: Path) -> None:
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
    assert result.static_analysis_result is not None
    assert result.static_analysis_result.files_scanned >= 1
    assert result.static_analysis_result.root_path == str((tmp_path / "src").resolve())
    assert "tool_tampering" in result.static_analysis_result.risk_surfaces
    assert "knowledge_poisoning" in result.static_analysis_result.risk_surfaces


def test_deep_ingestion_docker_plan_generation(tmp_path: Path) -> None:
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

    result = build_agent_perception_from_path(material_path)

    assert result.deep_plan.docker_trace_plan is not None
    assert result.deep_plan.docker_trace_plan.docker_image == "local/redsentinel-agent:test"
    assert result.deep_plan.analysis_targets == ["adapter:normalize", "adapter:invoke"]


def test_deep_ingestion_with_docker_execution_disabled(tmp_path: Path) -> None:
    (tmp_path / "src").mkdir()
    material_path = tmp_path / "materials.yaml"
    material_path.write_text(
        """
schema_version: agent-materials-v1
agent:
  name: docker_agent
  domain: support
integration:
  type: docker
  docker_image: local/test:latest
nodes:
  - id: input
    type: input_node
    target: adapter:invoke
evaluation:
  attack_entries:
    - prompt
""".strip(),
        encoding="utf-8",
    )

    result = build_agent_perception_from_path(material_path, execute_docker=False)

    assert result.trace_artifacts is None
    assert result.deep_plan.docker_trace_plan is not None


def test_deep_ingestion_profile_from_manifest(tmp_path: Path) -> None:
    material_path = tmp_path / "materials.yaml"
    material_path.write_text(
        """
schema_version: agent-materials-v1
agent:
  name: manifest_agent
  domain: healthcare
  framework: python_function
  root_path: .
  entrypoint: app:main
integration:
  type: source
  source_path: src
nodes:
  - id: input-gateway
    type: input_node
    target: app:handle_input
    defenses:
      - input_firewall
tools:
  - name: query_patient_records
    risk_level: high
    allowed_roles:
      - doctor
    side_effect: false
business:
  sensitive_data:
    - patient_id
    - medical_record
evaluation:
  attack_entries:
    - prompt
""".strip(),
        encoding="utf-8",
    )

    result = build_agent_perception_from_path(material_path)

    assert result.standard_profile.agent_name == "manifest_agent"
    assert result.standard_profile.business_domain == "healthcare"
    assert result.standard_profile.framework == "python_function"
    assert len(result.standard_profile.nodes) == 1
    assert result.standard_profile.nodes[0].id == "input-gateway"
    assert result.standard_profile.nodes[0].type == "input_node"
    assert "input_firewall" in result.standard_profile.nodes[0].defenses
    assert len(result.standard_profile.tools) == 1
    assert result.standard_profile.tools[0].name == "query_patient_records"
    assert result.standard_profile.tools[0].risk_level == "high"
    assert "patient_id" in result.standard_profile.sensitive_data


def test_deep_ingestion_empty_source_dir(tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    material_path = tmp_path / "materials.yaml"
    material_path.write_text(
        """
schema_version: agent-materials-v1
agent:
  name: empty_agent
  domain: test
integration:
  type: source
  source_path: src
evaluation:
  attack_entries:
    - prompt
""".strip(),
        encoding="utf-8",
    )

    result = build_agent_perception_from_path(material_path)

    assert result.static_analysis_result is not None
    assert result.static_analysis_result.files_scanned == 0
    assert result.static_analysis_result.confidence == 0.4


def test_deep_ingestion_skips_static_analysis_when_flag_set(tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    (src / "app.py").write_text("def main():\n    pass", encoding="utf-8")
    material_path = tmp_path / "materials.yaml"
    material_path.write_text(
        """
schema_version: agent-materials-v1
agent:
  name: skip_analysis_agent
  domain: test
integration:
  type: source
  source_path: src
evaluation:
  attack_entries:
    - prompt
""".strip(),
        encoding="utf-8",
    )

    result = build_agent_perception_from_path(material_path)
    result.deep_plan.skip_static_analysis = True
    result2 = build_agent_perception_from_path(material_path)

    assert result2.static_analysis_result is not None
