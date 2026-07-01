# A-Line T1-T3 Code Review

## Scope

Branch: `feat/A-openmanus-monitor`

Reviewed commits:

- `1d5fd9c Strictly integrate OpenManus T1`
- `4da253d Complete T3 supervisor Docker loop`

This review covers the OpenManus integration, monitor plugin, supervisor approval loop, Docker sandbox handoff, and related tests/docs.

## Verified

- T1 now has a real OpenManus integration path:
  - `install_red_sentinel_tools(agent)` installs Red Sentinel tools into `agent.available_tools.add_tools(...)`.
  - `attach_real_openmanus_monitor(agent, hooks)` wraps `agent.llm.ask_tool(...)` and `agent.execute_tool(command)`.
  - `auto_defense_system.openmanus_agent.smoke` runs a real OpenManus `Manus.run()` loop with a fake LLM and real OpenManus tool call objects.

- T3 now has a backend supervisor loop:
  - `SupervisorApprovalService` resolves pending `ask` decisions.
  - Approved `code_execution` requests are converted into a `DockerTracePlan`.
  - The plan is handed to `auto_evaluation_system.sandbox.docker.executor.execute_docker_trace(...)`.
  - A `monitor_decision` event is returned with Docker artifact references.

- Tests passed locally:

```text
python -m pytest auto_defense_system\tests auto_evaluation_system\tests\test_monitor_decision_events.py auto_evaluation_system\tests\sandbox\test_docker_backend.py -q
125 passed, 1 skipped
```

## Findings

### P1: Approval Is Recorded Before Docker Execution Is Known To Be Valid

File: `auto_defense_system/src/auto_defense_system/monitor_plugin/supervisor.py`

`SupervisorApprovalService.resolve(...)` calls `interceptor.resolve_ask(...)` before validating/building/running the Docker execution path.

Risk:

- The pending ask is removed.
- The decision is recorded as approved.
- If Docker execution fails after that, approval state and execution state diverge.

Recommendation:

- Validate and build the code execution request before resolving the ask.
- Wrap Docker execution failures and emit a failed monitor event/audit status.
- Preserve enough state to retry or inspect failed approved executions.

### P1: Submitted Payload Can Select The Docker Image

File: `auto_defense_system/src/auto_defense_system/monitor_plugin/supervisor.py`

`request.metadata["docker_image"]` can override the sandbox image.

Risk:

- The approved payload can influence the runtime image.
- This weakens reproducibility and sandbox policy control.
- It may cause unexpected image pulls or execution environments.

Recommendation:

- Move Docker image selection to supervisor-side config.
- Use an allowlist if multiple images are required.
- Do not trust request metadata for security-sensitive runtime selection.

### P2: Monitor Plugin Imports B/C-Side Modules Eagerly

Files:

- `auto_defense_system/src/auto_defense_system/monitor_plugin/__init__.py`
- `auto_defense_system/src/auto_defense_system/monitor_plugin/supervisor.py`

Importing `auto_defense_system.monitor_plugin` now imports `SupervisorApprovalService`, which imports `auto_attack_system.ingestion.deep`.

Risk:

- Lightweight T2 monitor usage now depends on B/C-side modules.
- If the defense/plugin package is used independently, imports may fail.

Recommendation:

- Keep `MonitorInterceptor` and `OpenManusMonitorHooks` lightweight.
- Lazy import supervisor/Docker dependencies only when the supervisor loop is used.

### P3: OpenManus LLM Hook Only Reads Keyword Messages

File: `auto_defense_system/src/auto_defense_system/openmanus_agent/real_openmanus.py`

`monitored_ask_tool(...)` reads `kwargs.get("messages")`.

Risk:

- Verified OpenManus `ToolCallAgent.think()` uses keyword `messages`, so the current path is covered.
- If another OpenManus path calls `ask_tool(messages)` positionally, the monitor will inspect an empty message list.

Recommendation:

- Fall back to `args[0]` when `messages` is not present in `kwargs`.

## Local Docker Note

Docker CLI was present locally:

```text
Docker version 28.0.4
```

But Docker Desktop daemon was not reachable:

```text
dockerDesktopLinuxEngine pipe not found
```

So real container execution was not claimed as locally verified. The committed tests verify the supervisor-to-Docker boundary with a fake Docker executor and verify that Docker executor command construction includes `adapter_entrypoint`.

## Overall Assessment

The branch is directionally correct and has meaningful test coverage. Before presenting T3 as a security-grade closed loop, fix the two P1 issues:

- approval/execution state divergence
- untrusted Docker image selection

