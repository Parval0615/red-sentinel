# OpenManus Agent Example

This example shows the minimal offline path for validating the RedSentinel OpenManus adapter without network access, browser automation, or LLM keys.

Run it from the repository root:

```bash
python examples/agents/openmanus_agent/run_offline_fixture.py
```

The script uses `redsentinel.adapters.engine.openmanus.OpenManusAdapter` with the bundled fixture at `third_party/OpenManus/fixtures/offline_turn.json`, sends one message, and writes exported `audit_events` to:

```text
runs/openmanus_agent/audit_events.json
```

Use `--output` to write the audit events somewhere else:

```bash
python examples/agents/openmanus_agent/run_offline_fixture.py --output /tmp/openmanus-audit-events.json
```
