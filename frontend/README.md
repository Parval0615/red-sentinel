# RedSentinel Frontend Dashboard

## Overview

单文件零依赖的安全评测可视化报告，数据来自 `auto_evaluation_system.product_api.reports` 产出的 `AgentSecurityReport`。

## Data Contract

### AgentSecurityReport → View Mapping

| Report Field | View Component |
|---|---|
| `tenant_id` | Header |
| `agent_id` | Header |
| `benchmark` | Header |
| `overall_score` | Metric Card |
| `risk_level` | Metric Card (color) |
| `attack_success_rate` | Metric Card |
| `false_positive_rate` | Metric Card |
| `findings[]` | Findings Table + Conclusion Card |
| `scenario_results[]` | Scenario Table |
| `guard_effectiveness` | Node Attribution |
| `business_impact` | Impact Section |
| `artifacts` | Evidence Section |

### ScenarioResult → Table Mapping

| Field | Column |
|---|---|
| `scenario_id` | Scenario ID |
| `category` | Category |
| `severity` | Severity |
| `expected_decision` | Expected |
| `actual_decision` | Actual |
| `passed` | Status |
| `business_impact` | Impact |
| `trajectory_ref` | Evidence |

### Finding → Table Mapping

| Field | Column |
|---|---|
| `severity` | Severity |
| `scenario_id` | Scenario |
| `title` | Title |
| `business_impact` | Impact |
| `recommendation` | Recommendation |

### Node Attribution (Extended)

每个 `ScenarioResult` 可扩展包含节点归因数据：

```json
{
  "node_attribution": {
    "intercepted_node": "input_node",
    "intercepted_at_step": 2,
    "defense_type": "input_firewall",
    "attack_path": ["input_node", "llm_node", "tool_node"],
    "node_status": {
      "input_node": {"defense": "input_firewall", "status": "mounted"},
      "rag_retriever": {"defense": "doc_scanner", "status": "mounted"},
      "tool_node": {"defense": "tool_guard", "status": "mounted"},
      "memory_node": {"defense": "memory_guard", "status": "mounted"},
      "llm_node": {"defense": "goal_guard", "status": "mounted"},
      "output_node": {"defense": "output_filter", "status": "mounted"}
    }
  }
}
```

### Trajectory Data (Extended)

轨迹数据格式：

```json
{
  "trajectory": [
    {
      "step_index": 0,
      "timestamp": "2026-06-26T10:00:00Z",
      "step_type": "llm_inference",
      "model": "gpt-4",
      "input_messages": [...],
      "output_content": "...",
      "tool_call_intents": [...]
    },
    {
      "step_index": 1,
      "timestamp": "2026-06-26T10:00:05Z",
      "step_type": "tool_call",
      "call_id": "call_1",
      "name": "query_order",
      "arguments": {...},
      "response": {...}
    }
  ]
}
```

### ASR Convergence Data

多轮攻击收敛数据：

```json
{
  "asr_convergence": [
    {"round": 1, "asr": 0.44, "blocked": 4, "total": 9},
    {"round": 2, "asr": 0.33, "blocked": 6, "total": 9},
    {"round": 3, "asr": 0.22, "blocked": 7, "total": 9},
    {"round": 4, "asr": 0.11, "blocked": 8, "total": 9},
    {"round": 5, "asr": 0.0, "blocked": 9, "total": 9}
  ]
}
```

## Files

```
frontend/
├── data/
│   ├── mock_report.json          # Mock AgentSecurityReport
│   └── mock_comparison.json      # Mock AgentSecurityComparisonReport
├── tests/
│   └── test_report_rendering.py  # HTML generation tests
├── generator.py                  # Python HTML generator
├── index.html                    # Main dashboard template
└── README.md                     # This file
```

## Usage

```bash
# Generate report from JSON
python -m frontend.generator --input data/mock_report.json --output report.html

# Open in browser
open report.html
```

## Technical Constraints

- **Single file**: All CSS/JS embedded in HTML
- **Zero dependencies**: No external libraries required
- **file:// protocol**: Must work when opened directly from filesystem