# B-Line Delivery README

This document summarizes the B-line implementation for perception and attack-layer evolution. It is a new handoff README and does not replace the project root `README.md` or `ROADMAP.md`.

## Scope

B-line owns:

- External Agent material intake.
- Candidate Agent profile generation.
- Profile-driven personalized attack generation.
- Attack strategy self-evolution.
- B-side Docker material planning.

B-line does not own:

- Defense runtime extraction.
- Node-level guard mounting.
- Evaluation runner orchestration.
- Docker sandbox execution.
- Changes to frozen shared contracts or schemas.

## Branches And Local Commits

The local implementation was split by milestone branches:

| Milestone | Branch | Commit | Summary |
|---|---|---:|---|
| M1 | `feat/attack/ingestion-M1` | `1cd2a03` | Add Agent material ingestion and manifest draft generation. |
| M1.5 | `feat/attack/code-profiler-M1.5` | `abef102` | Add AST candidate profile generation. |
| M2 | `feat/attack/profile-driven-M2` | `034199f` | Generate attack specs from AgentProfile risk surfaces. |
| M2.5 | `feat/attack/self-evolving-M2.5` | `822aacf` | Add attack self-evolution from reports/directives/failures. |
| M5 | `feat/attack/deep-ingestion-M5` | `9bb347f` | Add B-side deep ingestion and Docker trace planning. |
| Acceptance evidence | `feat/attack/deep-ingestion-M5` | `c0fe96c` | Add acceptance evidence, demo generation, and stronger tests. |
| LLM enhancement | `feat/attack/deep-ingestion-M5` | `f958a2c` | Add optional LLM profile enhancement. |
| LLM eval compatibility | `feat/attack/deep-ingestion-M5` | `d759dad` | Add gzip compatibility and stricter LLM prompt constraints. |

Current local branch after the full B-line implementation:

```text
feat/attack/deep-ingestion-M5
```

## End-To-End B-Line Flow

The implemented B-line path is:

```text
agent-materials-v1
-> draft AgentManifest
-> base AgentProfile
-> AST baseline code profiler
-> optional LLM candidate patch
-> candidate_profile + auditable diff
-> profile-driven AttackSpec generation
-> fallback AttackSpec generation
-> report/directive/failure-driven evolved AttackSpec generation
```

## M1: External Agent Material Intake

Implementation:

- `auto_attack_system/src/auto_attack_system/ingestion/materials.py`
- `auto_attack_system/src/auto_attack_system/ingestion/manifest_builder.py`
- `docs/product/agent-ingestion-m1.md`

M1 defines `agent-materials-v1` for external Agent upload materials. It supports:

- `source`
- `api`
- `docker`

The manifest builder maps these materials into the existing frozen `agent-manifest-v1` shape. It does not modify shared schemas.

Gate output:

```json
{
  "valid": true,
  "completeness_score": 1.0,
  "missing_fields": [],
  "warnings": []
}
```

For API/OpenAPI material, M1 can infer tools from OpenAPI `paths`.

## M1.5: AST Baseline + Optional LLM Enhancement

Implementation:

- `agent_integration_system/src/agent_integration_system/profiling/code_profiler.py`
- `agent_integration_system/src/agent_integration_system/profiling/profile_patch.py`
- `agent_integration_system/src/agent_integration_system/profiling/llm_client.py`
- `agent_integration_system/src/agent_integration_system/profiling/llm_profiler.py`
- `agent_integration_system/src/agent_integration_system/profiling/evidence_validator.py`
- `agent_integration_system/src/agent_integration_system/profiling/profile_merge.py`
- `agent_integration_system/src/agent_integration_system/profiling/prompts.py`

Design:

```text
AST baseline first, LLM enhancer second.
```

AST baseline is deterministic and always available. It scans Python functions and maps naming evidence to candidate nodes, tools, risk surfaces, and evidence refs.

LLM enhancement is optional. The LLM can only return a `CandidateProfilePatch`, not a full official profile. The patch must pass:

- Pydantic validation.
- Evidence file validation.
- Evidence line-range validation.

If the LLM output is invalid, unavailable, or cites unsupported evidence, the system falls back to AST baseline.

The output remains:

- `candidate_profile`
- `diff`
- `evidence_refs`
- `confidence`
- `notes`

It does not modify source code or the official frozen contract.

## Real LLM Evaluation

Real LLM evaluation is separated from pytest.

Script:

```text
agent_integration_system/scripts/eval_llm_profiler.py
```

Environment variables:

```powershell
$env:REDSENTINEL_LLM_API_KEY="..."
$env:REDSENTINEL_LLM_BASE_URL="https://vip.yi-zhan.top/v1"
$env:REDSENTINEL_LLM_MODEL="DeepSeek-V3.2-nothinking"
python agent_integration_system/scripts/eval_llm_profiler.py
```

The tested model that successfully passed the current eval:

```text
DeepSeek-V3.2-nothinking
```

Observed result:

```json
{
  "case": "mixed_tool_rag_agent",
  "ast_node_recall": 1.0,
  "llm_node_recall": 1.0,
  "ast_risk_recall": 1.0,
  "llm_risk_recall": 1.0,
  "llm_used": true,
  "failed_safe": false
}
```

Other observations:

- `Qwen/Qwen3-Coder-30B-A3B-Instruct` was callable, but initially returned a full profile instead of a patch and was correctly rejected.
- `chatgpt-4o-latest` returned HTTP 429 through the tested gateway.
- The gateway returned gzip-compressed responses, so `LLMClient` now supports gzip decoding.

## M2: Profile-Driven Personalized Attack Generation

Implementation:

- `auto_attack_system/src/auto_attack_system/profile_driven.py`

M2 consumes:

```text
AgentProfile.nodes[].risk_surfaces
```

It generates targeted `AttackSpec` records only for exposed risk surfaces. It also creates fallback attacks when profile information is incomplete.

M2 gate behavior:

- Only target exposed risk surfaces for targeted attacks.
- Keep fallback coverage for seven baseline risks:
  - `prompt_injection`
  - `knowledge_poisoning`
  - `unauthorized_retrieval`
  - `tool_tampering`
  - `memory_poisoning`
  - `goal_drift`
  - `pii_leakage`

## M2.5: Attack Strategy Self-Evolution

Implementation:

- `auto_attack_system/src/auto_attack_system/evolution/self_evolving.py`

M2.5 consumes:

- `AgentSecurityReport`
- `OptimizationDirective`
- failed attack attempts

It deterministically creates evolved `AttackSpec` variants. The output records why the mutation happened:

```json
{
  "source_finding": "tool_tampering",
  "trigger_reason": "Finding finding-tool-1 remained unresolved.",
  "mutation_strategy": "chain_hijack",
  "expected_effect": "increase multi-step tool misuse coverage"
}
```

The same input produces the same evolved output. This is intentional for reproducibility and competition evidence.

## M5: B-Side Docker Deep Ingestion Planning

Implementation:

- `auto_attack_system/src/auto_attack_system/ingestion/deep.py`

M5 B-side implementation defines how a Docker Agent should be described for later observation:

- `docker_image`
- `adapter_entrypoint`
- `node_targets`
- `read_only_mounts`
- `expected_artifacts`
- `network_policy`

Boundary:

```text
B-line Docker material spec only describes how an external Docker Agent should be observed.
Actual sandbox execution, network isolation, runtime telemetry collection, and enforcement are owned by C-line.
```

## Demo Evidence

Generate local B-line demo evidence:

```powershell
python -m auto_attack_system.scripts.generate_b_line_demo
```

Generated files:

```text
runs/b_line_demo/materials_input.yaml
runs/b_line_demo/draft_manifest.json
runs/b_line_demo/candidate_profile_diff.json
runs/b_line_demo/targeted_attack_specs.json
runs/b_line_demo/evolved_attack_specs.json
runs/b_line_demo/b_line_demo_summary.json
```

Example summary:

```json
{
  "valid": true,
  "completeness_score": 1.0,
  "missing_fields": [],
  "candidate_confidence": 0.85,
  "targeted_attack_count": 12,
  "fallback_attack_count": 2,
  "evolved_attack_count": 1
}
```

`runs/` is ignored by Git. The demo files are local evidence artifacts and can be regenerated.

## Verification

Default engineering regression:

```powershell
python -m pytest agent_integration_system/tests auto_attack_system/tests -q
```

Current verified result:

```text
41 passed
```

Real LLM effect evaluation:

```powershell
python agent_integration_system/scripts/eval_llm_profiler.py
```

This requires LLM environment variables and is intentionally not part of default pytest.

## Engineering Boundaries

This B-line work intentionally does not:

- Modify `auto_defense_system`.
- Modify `auto_evaluation_system/sandbox`.
- Change frozen shared contracts or JSON schemas.
- Execute Docker containers.
- Modify enterprise/source Agent code.
- Generate defense strategies.

The output is candidate evidence for attack planning and downstream C-line evaluation/defense work.

## Current Limitations

- AST code profiling is heuristic and name-based.
- Real LLM quality depends on the selected model and endpoint behavior.
- The current real LLM eval has one small labeled case; more profiler eval cases should be added for stronger competition evidence.
- Docker M5 is B-side planning only. Runtime execution belongs to C-line.
- Full automatic attack-defense-evaluation closed loop still requires C-line integration.
