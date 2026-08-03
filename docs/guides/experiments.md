# 实验与复现指南

## 1. 选择实验

RQ1-RQ5 的假设、基线、指标和成本上限位于：

```bash
redsentinel experiment
redsentinel experiment --rq RQ2
```

正式配置源为 `configs/experiments/rq-matrix-v1.yaml`。

## 2. 验证环境

```bash
redsentinel doctor --dry-run
python -m pytest -q
```

默认测试不访问网络。真实 OpenManus 需要 Docker daemon、固定源码和 OpenAI-compatible 凭据。

## 3. 数据与划分

实验启动前校验 `datasets/manifests/`。development 可用于规则、阈值和进化选择；holdout 只用于最终评估。同源 payload 和变体不得跨划分。

## 4. 运行

最小离线评测：

```bash
redsentinel evaluate --seed 42 --output-dir artifacts
```

协同进化 smoke：

```bash
redsentinel evolve --seed 42 --output-dir artifacts
```

正式实验必须显式记录：

- RQ 和 arm；
- Agent/runtime/model；
- 数据版本与划分；
- seed 和重复次数；
- 查询、执行、时间或 token 预算；
- 停止条件；
- defense/attack 版本。

## 5. 失败处理

- `environment_error`：依赖、Docker、网络、凭据或外部服务失败。
- `business_failure`：Agent 未完成正常任务。
- `security_failure`：攻击满足成功判定。
- `not_evaluated`：缺少必要环境或证据。

环境错误不得计入分母，除非实验协议预先规定并单独报告。

## 6. 分析

```bash
redsentinel report artifacts/results/*.json --output-dir artifacts/paper
```

分析至少报告单次原始结果、均值、标准差、95% CI 和效应量。显著性检验必须说明配对关系和前提；样本不足时输出 `not_applicable`。

## 7. 复现

每个证据产物应关联：

- ExperimentManifest；
- Git commit 和 dirty 状态；
- 配置/数据 SHA-256；
- Python 与依赖版本；
- 模型 provider/name/temperature；
- 原始结果 JSON；
- 生成图表的脚本与 JSON Pointer。

禁止修改聚合表格替代重新运行分析。

## 8. 中断与恢复

当前 `evolution-run-v1` 会持久化状态转换和 hash-chain ledger，但不支持从中间轮次自动恢复执行。中断后应使用相同 manifest、seed、代码和数据版本重新运行；已有 ledger 用于审计，不得直接拼接成新的成功运行。可恢复执行是后续能力，启用前必须补充状态一致性和重复副作用测试。

## 9. 旧配置与旧产物迁移

迁移旧 Agent manifest、scenario YAML 或 Product CLI JSON：

```python
from redsentinel.migration import legacy_config_to_manifest

manifest = legacy_config_to_manifest("path/to/legacy-config.yaml", seed=42)
```

Product CLI 配置中的凭据不会复制到 `ExperimentManifest`。旧 JSON 报告可直接
读取，也可迁移为完整研究证据包：

```python
from redsentinel.migration import migrate_legacy_artifact, read_legacy_artifact

legacy = read_legacy_artifact("path/to/report.json")
evidence = migrate_legacy_artifact(
    "path/to/report.json",
    "artifacts/migrated-report",
    seed=42,
)
```

迁移是无损包裹，不会把历史 demo 自动升级为真实 runtime 证据。证据等级仍按
原始运行模式判定。
