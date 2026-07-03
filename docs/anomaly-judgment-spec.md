# Anomaly Judgment Oracle

T5 adds a lightweight anomaly oracle for platform and monitor-plugin events. The oracle does not replace the monitor plugin policy decision. It adds a normalized verdict for audit, reporting, and later T7 reproducibility work.

## Inputs

- Monitor decision: `MonitorDecision` from `auto_defense_system.monitor_plugin.interceptor`.
- Detector output: `DetectorOutput` from MIS, GDM, and TRS baselines.

The first T5 version does not auto-infer arbitrary trajectory type. Trajectory baselines remain explicit through `DetectorInput`.

## Verdict Contract

`OracleVerdict` uses:

- `status`: `normal`, `review`, or `abnormal`.
- `confidence`: normalized `0.0-1.0`.
- `findings`: normalized evidence rows with `risk_type`, `severity`, `summary`, and `recommended_action`.
- `rationale`: short explanation of the aggregate result.

## Rule Layer

Monitor decisions map as follows:

| Monitor signal | Oracle status | Confidence | Notes |
| --- | --- | --- | --- |
| `decision=deny` | `abnormal` | `0.9` | Policy already blocked the action. |
| `decision=ask` | `review` | `0.65` | Human confirmation is required. |
| `risk_level=high/critical` | `abnormal` | `0.82` | High-risk allowed event still needs audit attention. |
| `decision=allow` and normal risk | `normal` | `0.2` | No finding emitted. |

Risk type is inferred from monitor call type and audit context:

- sensitive output or PII signals -> `data_leakage`
- file/path/workspace signals -> `unauthorized_file_access`
- code/sandbox signals -> `unsafe_code_execution`
- policy/tool signals -> `policy_violation`

## Detector Layer

Detector outputs map as follows:

| Detector decision | Oracle status | Risk type |
| --- | --- | --- |
| `poisoned` | `abnormal` | `memory_poisoning` |
| `drifted` | `abnormal` | `goal_perturbation` |
| `high` | `abnormal` | `tool_tampering` |
| `ambiguous` | `review` | metric-specific risk |
| `medium` | `review` | `tool_tampering` |
| `clean`, `aligned`, `low` | `normal` | none |

Detector confidence is the detector score. Aggregation chooses `abnormal` over `review` over `normal`, and keeps the maximum confidence.

## Monitor Plugin Integration

`MonitorInterceptor` adds the oracle verdict to:

```json
{
  "audit_payload": {
    "oracle": {
      "schema_version": "anomaly-oracle-verdict-v0.1",
      "status": "abnormal",
      "confidence": 0.9
    }
  }
}
```

This annotation is best-effort. If the oracle import or verdict generation fails, the monitor decision still completes and audit payload records a `review` fallback with the error type.
