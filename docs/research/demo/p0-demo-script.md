# P0 五分钟离线演示讲稿

## 运行前

```bash
python -m pip install -e ".[all,dev]"
redsentinel demo --dry-run --output-dir artifacts --seed 42
redsentinel demo --output-dir artifacts --seed 42
```

主命令不需要网络、Docker 或 API key。建议从空的 `artifacts/p0-demo/` 开始；已有目录不会被删除，新一轮评测写入带时间戳的子目录。

## 0:00-0:40：问题与定位

讲述：

> RedSentinel 研究 Agent 的轨迹级安全评测。普通 LLM 评测只看输入和最终输出，但 Agent 风险还发生在检索、工具、记忆和状态变化中。项目用画像和历史失败证据驱动攻击与防御协同进化，同时约束误伤、业务效用和成本。

展示 README 首屏和主循环，不进入 Product API。

## 0:40-1:20：环境与画像

展示终端输出：

```text
COMMAND=demo
EXECUTION_MODE=offline_fixture
PROFILE=artifacts/p0-demo/profiles/simple_agent.json
```

说明：

- `doctor` 只报告可选环境，不因缺少 Docker/API key 阻塞离线 demo；
- Agent manifest 被校验后生成带节点、工具和风险面的 profile；
- `offline_fixture` 是工程 smoke，不是真实 Agent 结论。

## 1:20-2:30：单轮轨迹评测

展示：

```text
PAIRED_CASES=3/3
FPR=0.000000
EVALUATION_EVIDENCE=.../evidence-index-v1.json
```

打开 `artifacts/p0-demo/p0-demo-summary-v1.json` 的 `trajectory_evidence`：

1. `memory_poisoning`：定位 `memory_ops` 和 state delta，Memory Guard 拦截；
2. `tool_tampering`：定位异常 tool response，Tool Guard 拦截；
3. `goal_perturbation`：定位 prompt perturbation 和目标变化，Goal Guard 拦截。

每条记录都回指 `report.json`、`audit_refs.json` 和 hash-chain 审计日志。强调确定性规则负责主判定，语义 Judge 只能作为补充信号。

## 2:30-3:40：协同进化

展示：

```text
ASR_INITIAL=0.437500
ASR_FINAL=0.000000
EVOLUTION_EVIDENCE=.../evidence-index-v1.json
```

打开 evolution 目录中的：

- `convergence.json` / `convergence_curve.png`；
- `ablation.json` / `ablation_table.md`；
- `raw-result-v1.json`；
- `provenance-v1.json`。

说明四类基线和五类消融已经进入统一实验设计；本次 `43.75% -> 0%` 只验证确定性链路和产物完整性，不证明真实 OpenManus 上的效果。

## 3:40-4:30：可信证据与边界

展示 summary 的：

```json
{
  "execution_mode": "offline_fixture",
  "business_success_rate": {"status": "not_evaluated"},
  "overhead": {"status": "not_evaluated"}
}
```

讲述：

> 我没有用 `1-FPR` 冒充业务成功率，也没有用一次运行耗时冒充受控 overhead。每轮实验保存 manifest、raw result、provenance 和 evidence index；哈希链能提供篡改证据，但不能保证输入源天然真实。

## 4:30-5:00：下一阶段

讲述：

> 当前最薄弱的是外部有效性。P1 优先跑固定 commit 的 OpenManus 和第二个 Agent，在两个模型家族上做同预算 3-seed pilot；通过门禁后再扩到 5-10 seed 正式实验。真实报告必须同时满足 `real_runtime=true` 和 `simulated=false`。

## 预期输出

```text
COMMAND=demo
EXECUTION_MODE=offline_fixture
PAIRED_CASES=3/3
FPR=0.000000
ASR_INITIAL=0.437500
ASR_FINAL=0.000000
BUSINESS_SUCCESS_RATE=not_evaluated
OVERHEAD=not_evaluated
SUMMARY=artifacts/p0-demo/p0-demo-summary-v1.json
```

## 降级与故障处理

| 故障 | 处理 |
|---|---|
| 未安装 console script | 使用 `python -m redsentinel.cli demo ...` |
| profile 校验失败 | 先运行 `redsentinel profile <config> --dry-run` |
| Matplotlib 不可用 | 安装 `.[all,dev]`；不删除图表生成步骤 |
| 输出目录已有文件 | 保留旧证据，新运行写入时间戳目录 |
| Docker/API key 缺失 | 继续离线 demo；OpenManus 保持 `not_evaluated` |
| 时间不足 | 直接打开 summary 和两个 evidence index，不展示 dashboard |

任何失败都保留原始 stderr 和产物；环境失败不得计为防御成功。
