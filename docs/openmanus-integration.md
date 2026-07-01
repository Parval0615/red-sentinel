# OpenManus Integration Notes

## Scope

Branch A uses OpenManus as the supervised application surface. The upstream project is external and should be cloned separately from this repository:

```bash
git clone https://github.com/FoundationAgents/OpenManus.git
```

This repository does not vendor OpenManus source code. Instead, `auto_defense_system.openmanus_agent` provides a narrow adapter that can bind Red Sentinel tools to the real OpenManus runtime surfaces.

The T1 strict integration is based on these upstream OpenManus files:

- `main.py`: creates `agent = await Manus.create()` and calls `await agent.run(prompt)`.
- `app/agent/manus.py`: `Manus` extends `ToolCallAgent` and owns `available_tools: ToolCollection`.
- `app/agent/toolcall.py`: `ToolCallAgent.think()` calls `self.llm.ask_tool(...)`; `ToolCallAgent.act()` calls `self.execute_tool(command)` for each tool call.
- `app/tool/tool_collection.py`: `ToolCollection.add_tools(*tools)` registers tools and `ToolCollection.execute(name=..., tool_input=...)` executes them.
- `app/tool/base.py`: tools extend `BaseTool` and implement async `execute(**kwargs)`.

Local verification used an external checkout at `D:\openmanus-t1-inspection\OpenManus-main`. The checkout was downloaded outside this repository and was not committed.

## T1 Entry Points

Files:

- `auto_defense_system/src/auto_defense_system/openmanus_agent/adapter.py`
- `auto_defense_system/src/auto_defense_system/openmanus_agent/real_openmanus.py`
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

This proves the Red Sentinel side of the OpenManus tool bridge: tool registration, invocation, and call history capture.

When OpenManus is installed and importable, patch a real `Manus` instance after `await Manus.create()`:

```python
from app.agent.manus import Manus
from auto_defense_system.monitor_plugin import MonitorInterceptor, OpenManusMonitorHooks
from auto_defense_system.openmanus_agent import (
    attach_real_openmanus_monitor,
    install_red_sentinel_tools,
)

agent = await Manus.create()
install_red_sentinel_tools(agent)
attach_real_openmanus_monitor(agent, OpenManusMonitorHooks(MonitorInterceptor()))
await agent.run(prompt)
```

`install_red_sentinel_tools(agent)` uses the real `agent.available_tools.add_tools(*tools)` surface. `attach_real_openmanus_monitor(agent, hooks)` wraps the real `agent.llm.ask_tool(...)` and `agent.execute_tool(command)` entry points.

## T1 Strict Smoke

`auto_defense_system.openmanus_agent.smoke` runs a real OpenManus `Manus` loop with a deterministic fake LLM. This avoids external model credentials while still exercising:

- `Manus.create()`
- `BaseAgent.run()`
- `ToolCallAgent.think()`
- `ToolCallAgent.act()`
- `ToolCallAgent.execute_tool()`
- `ToolCollection.execute(...)`

External setup used for local verification:

```powershell
python -m venv D:\openmanus-t1-inspection\.venv
D:\openmanus-t1-inspection\.venv\Scripts\python.exe -m pip install -e D:\openmanus-t1-inspection\OpenManus-main
D:\openmanus-t1-inspection\.venv\Scripts\python.exe -m pip install boto3~=1.37.18 docker~=7.1.0 structlog baidusearch~=1.0.3 duckduckgo_search~=7.5.3 daytona==0.21.8 mcp~=1.5.0
$env:PYTHONPATH='D:\red-sentinel-main\auto_defense_system\src;D:\openmanus-t1-inspection\OpenManus-main'
D:\openmanus-t1-inspection\.venv\Scripts\python.exe -m auto_defense_system.openmanus_agent.smoke
```

Verified output summary:

```text
agent: Manus
mode: real_openmanus_fake_llm_no_defense_smoke
installed_tools: db_query, file_operation, api_call, send_email
result: Step 1 executed send_email through OpenManus ToolCallAgent.execute_tool(...)
```

Notes:

- `requirements.txt` had a Windows resolver conflict between `pillow~=11.1.0` and `crawl4ai==0.6.3` requiring `pillow~=10.4`, so the verification used OpenManus `setup.py` plus the missing runtime imports reported by the actual run.
- The smoke does not call a live LLM API. It injects a fake LLM response containing a real OpenManus `ToolCall`, so the verification remains deterministic and credential-free.

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
