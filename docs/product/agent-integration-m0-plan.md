# Agent Integration M0 Plan

## Goal

M0 turns RedSentinel from a fixed local demo into a configurable agent onboarding foundation. An enterprise should be able to provide a `redsentinel.yaml` file, then RedSentinel can validate the integration surface and generate a deterministic `AgentProfile`.

## Scope

- Define the M0 onboarding contract in `redsentinel.yaml`.
- Freeze shared Phase 0 contracts: `agent-manifest-v1`, `agent-profile-v1`, and `optimization-directive-v1`.
- Validate agent metadata, node targets, defenses, tools, RAG settings, and evaluation scope.
- Generate `agent-profile-v1` from validated config.
- Provide a minimal example Python function agent.
- Provide tests for config loading, validation, and profile generation.

## Non-Goals

- No automatic LLM architecture discovery.
- No source-code rewriting.
- No runtime guard injection.
- No production gateway or sidecar.
- No generated attack execution.

## Architecture

```text
redsentinel.yaml
-> config loader
-> config validator
-> AgentProfile builder
-> agent_profile.json
```

The generated profile is the future shared contract for:

- Attack system: choose personalized prompt and RAG attacks.
- Defense system: choose node-level guards.
- Evaluation system: run clean / controlled comparisons and report attribution.

## M0 Config Contract

The first version supports:

- `schema_version`: `agent-manifest-v1`.
- `agent`: name, framework, root path, entrypoint.
- `nodes`: typed node targets and requested defenses.
- `tools`: tool risk level, allowed roles, side-effect flag.
- `business`: domain, roles, sensitive data.
- `rag`: optional document paths and test-injection flag.
- `evaluation`: allowed attack entries and intensity.

## Validation Rules

- `agent.root_path` must exist.
- `agent.framework` must be `python_function` or `langgraph`.
- `agent.entrypoint` and every `nodes[].target` must use `module:callable`.
- Node IDs must be unique.
- Node types must be supported.
- Defenses must be compatible with the node type.
- Tool risk levels must be `low`, `medium`, `high`, or `critical`.
- M0 attack entries are limited to `prompt` and `rag_text`.
- If RAG is enabled, at least one document path or retriever target must be present.

## Supported Node Types

| Node type | Default risk surfaces |
|---|---|
| `input_node` | `prompt_injection`, `jailbreak` |
| `rag_retriever` | `indirect_prompt_injection`, `knowledge_poisoning`, `unauthorized_retrieval` |
| `tool_node` | `tool_abuse`, `privilege_escalation`, `parameter_tampering` |
| `memory_node` | `memory_poisoning`, `cross_session_leakage` |
| `llm_node` | `goal_drift`, `instruction_hijacking` |
| `output_node` | `pii_leakage`, `unsafe_output` |

## Acceptance Criteria

- The example `redsentinel.yaml` validates successfully.
- The CLI can write an `agent_profile.json`.
- `AgentManifest`, `AgentProfile`, and `OptimizationDirective` have JSON Schema files under `auto_evaluation_system/schemas/`.
- Cross-system contract tests validate examples against those JSON Schema files.
- Invalid configs return clear validation errors.
- Tests cover loader, validator, and profile builder.
- Existing attack, defense, evaluation packages are not changed beyond package discovery and test path configuration.
