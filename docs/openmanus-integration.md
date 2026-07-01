# OpenManus Integration Notes

## Scope

Branch A uses OpenManus as the supervised application surface. The upstream project is external and should be cloned separately from this repository:

```bash
git clone https://github.com/FoundationAgents/OpenManus.git
```

This repository does not vendor OpenManus source code. Instead, `auto_defense_system.openmanus_agent` provides a narrow adapter that can bind Red Sentinel tools to an OpenManus-style tool registry.

## T1 Entry Points

Files:

- `auto_defense_system/src/auto_defense_system/openmanus_agent/adapter.py`
- `auto_defense_system/src/auto_defense_system/openmanus_agent/runner.py`

The adapter registers the existing simulated business tools:

- `db_query`
- `file_operation`
- `api_call`
- `send_email`

The local no-defense demo can run without OpenManus installed:

```bash
python -m auto_defense_system.openmanus_agent.runner
```

This proves the Red Sentinel side of the OpenManus tool bridge: tool registration, invocation, and call history capture. When OpenManus is installed, call `OpenManusAdapter.bind_to_openmanus_registry(registry)` against its tool registry.

## T2 Monitor Plugin

Files:

- `auto_defense_system/src/auto_defense_system/monitor_plugin/interceptor.py`
- `auto_defense_system/src/auto_defense_system/monitor_plugin/hooks.py`

Unified call surface:

```python
intercept(call_type, payload) -> MonitorDecision
```

Supported call types:

- `llm_input`
- `llm_output`
- `tool_call`
- `tool_result`
- `code_execution`
- `file_access`

OpenManus hooks map to the same interceptor:

- `before_llm_call`
- `after_llm_call`
- `before_tool_call`
- `after_tool_call`

The interceptor always returns a structured `audit_payload`. To persist decisions into the existing tamper-evident audit chain, pass the current writer explicitly:

```python
from auto_defense_system.monitor_plugin import MonitorInterceptor
from auto_defense_system.security.audit import write_audit_log

interceptor = MonitorInterceptor(audit_writer=write_audit_log)
```

The default constructor does not write files, which keeps dry runs and unit tests isolated unless audit persistence is requested.

## T3 Decision And Audit Model

Decision values:

- `allow`
- `deny`
- `ask`

Audit objects:

- tool calls
- code execution
- file access

`ask` decisions include deterministic `ask_id` values and are reflected in `auto_evaluation_system.events.MonitorDecisionPayload`. C-line should use these fields for the supervisor panel:

- `decision`
- `ask_id`
- `approval_state`
- `audit_object`
- `artifact_refs`

## Boundary

The code execution guard creates a Docker sandbox artifact plan and audit payload. It does not execute arbitrary code in-process. Actual Docker execution remains owned by `auto_evaluation_system.sandbox`.
