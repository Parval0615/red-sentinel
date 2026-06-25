# Agent Ingestion M1

M1 defines the first material intake layer for external Agent onboarding. It does not modify the frozen `AgentManifest`, `AgentProfile`, or `OptimizationDirective` contracts.

`auto_attack_system.ingestion` is a B-line pre-attack perception input module. It prepares material evidence for attack planning and does not replace formal onboarding under `agent_integration_system`.

## Scope

- Read `agent-materials-v1` YAML files from a file path or material directory.
- Support three declared integration types: `source`, `api`, and `docker`.
- Parse API/OpenAPI material in M1 and infer tool inventory from `paths`.
- Accept user-provided node paths and pass them through to the generated manifest draft.
- Score material completeness so later M1.5 code profiling can focus on missing fields.
- Emit an `agent-manifest-v1` draft that can be validated by the existing contract model.

Docker runtime execution and sandbox trajectory collection are reserved for M5.

## Material File

Preferred filenames inside an upload directory:

- `redsentinel.materials.yaml`
- `redsentinel.materials.yml`
- `materials.yaml`
- `materials.yml`

Example:

```yaml
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
```

## Completeness Fields

M1 scores whether the upload includes:

- `agent.name`
- `agent.domain`
- integration resource, such as `openapi_path`, `source_path`, or `docker_image`
- `nodes`
- `tools` or `openapi_path`
- `evaluation.attack_entries`

Missing fields do not block draft generation. They are reported in `MaterialInspection.missing` and should be resolved by user input or M1.5 code profiling.

The manifest builder also exposes gate fields for review:

```json
{
  "valid": true,
  "completeness_score": 1.0,
  "missing_fields": [],
  "warnings": []
}
```

## Contract Boundary

For M1, API and Docker materials are mapped into the existing `agent-manifest-v1` shape without changing shared schemas. When node paths are absent, the builder creates draft nodes using the configured adapter entrypoint and records a note that the nodes were generated.

## Docker Boundary

B-line Docker material spec only describes how an external Docker Agent should be observed. Actual sandbox execution, network isolation, runtime telemetry collection, and enforcement are owned by C-line.
