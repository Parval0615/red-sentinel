# P0 证据卡

验证日期：2026-08-01
阶段状态：`completed_with_real_runtime_deferred`

## 1. 工程门禁

| 门禁 | 命令 | 结果 | 证据等级 |
|---|---|---|---|
| 默认离线测试 | `python -m pytest -q` | 752 passed，3 warnings | E2 |
| 静态检查 | `python -m ruff check . --select F401,F841,F821,F811` | passed | E2 |
| CLI 定向测试 | `python -m pytest -q tests/unit/test_unified_cli.py tests/unit/test_p0_demo.py` | passed | E2 |
| Diff whitespace | `git diff --check -- <P0 files>` | passed | E1 |

3 条 warning 来自旧兼容 API、`langchain-community` 和 FastAPI TestClient 的依赖弃用提示，不是本阶段测试失败；P1/P2 应评估依赖迁移。

## 2. 一键离线演示

命令：

```bash
redsentinel demo --output-dir artifacts --seed 42
```

稳定索引：

```text
artifacts/p0-demo/p0-demo-summary-v1.json
```

结果：

| 指标 | 数值 | 模式 | 解释 |
|---|---:|---|---|
| 配对场景 | 3/3 passed | `offline_fixture` | memory/tool/goal |
| 单轮加固前 ASR | 1.0 | `offline_fixture` | 固定 3-case smoke |
| 单轮加固后 ASR | 0.0 | `offline_fixture` | 固定 3-case smoke |
| FPR | 0.0 | `offline_fixture` | 配对良性 case |
| 审计链 | valid | `offline_fixture` | 未配置签名的 hash-chain |
| 协同进化初始 ASR | 0.4375 | `offline_fixture` | 7 类威胁确定性 smoke |
| 协同进化最终 ASR | 0.0 | `offline_fixture` | 7 轮收敛 smoke |
| Business success rate | `not_evaluated` | 无 | 不用 `1-FPR` 代替 |
| Overhead | `not_evaluated` | 无 | 无受控 latency/token 对照 |

## 3. 三条轨迹证据

`p0-demo-summary-v1.json#/trajectory_evidence` 为每条记录提供：

| 风险 | 主要归因字段 | Guard | Evidence ref |
|---|---|---|---|
| `memory_poisoning` | `metadata.injections`、`memory_ops`、state delta | Memory Guard | report + audit refs + audit log |
| `tool_tampering` | `metadata.injections`、tool response、state delta | Tool Guard | report + audit refs + audit log |
| `goal_perturbation` | original goal、prompt perturbation、state delta | Goal Guard | report + audit refs + audit log |

每条证据均包含 detector decision、score、blocked node、attribution、audit integrity 和三个原始引用。三条记录不能外推为提示注入等全部 7 类威胁的真实运行效果。

## 4. 基线与消融

| 能力 | 状态 | 代码/测试证据 |
|---|---|---|
| 固定攻防 | 可运行 | `src/redsentinel/research/baselines.py`、`tests/research/test_baseline_matrix.py` |
| 仅攻击进化 | 可运行 | 同上，`attack_only` |
| 仅防御优化 | 可运行 | 同上，`defense_only` |
| 双边协同进化 | 可运行 | 同上，`coevolution` |
| 去 AgentProfile | 可运行 | `AblationConfig.profile` |
| 去轨迹异常 | 可运行 | `AblationConfig.trajectory_anomaly` |
| 去节点归因 | 可运行 | `AblationConfig.node_attribution` |
| 去失败反思 | 可运行 | `AblationConfig.reflection` |
| 去效用约束 | 可运行 | `AblationConfig.utility_constraints` |

这里的“可运行”表示离线协议、产物和测试已通过，不表示任一研究假设已获得统计支持。

## 5. Provenance 与完整性

单轮和协同进化目录均包含：

- `experiment-manifest-v1.json`
- `provenance-v1.json`
- `raw-result-v1.json`
- `evidence-index-v1.json`

Provenance 记录 Git commit/dirty、配置哈希、数据哈希、依赖版本和模型元数据。Hash-chain 可发现已记录日志的删除、插入、重排或修改，但不能证明输入数据源天然真实，也不能替代可信时间戳或签名根。

## 6. OpenManus

状态：`not_evaluated`

已完成：

- vendored source 与 commit 固定；
- Dockerfile 和 runtime overlay 检查；
- benchmark/version 固定；
- baseline/guarded 配对入口；
- 失败分类和报告模板。

阻塞：

- Docker daemon 不可用；
- `redsentinel/openmanus-real:local` 镜像不存在；
- `OPENAI_API_KEY`、`OPENAI_BASE_URL`、`OPENAI_MODEL` 缺失。

详细记录：`docs/research/demo/openmanus-preflight.md`。

## 7. 对外使用边界

可用于简历/面试：

- 752 项离线测试；
- 轨迹级评测、四类基线、五类消融和证据链设计；
- 3/3 配对 smoke 和 7 轮协同进化 smoke，必须标注离线；
- provenance、精准失败归因和 OpenManus 预演能力。

不可使用：

- 将 `43.75% -> 0%` 表述为真实 Agent 提升；
- OpenManus 防御效果；
- 跨 Agent/模型泛化；
- 论文显著性或生产级结论；
- 未测量的 business success rate 和 overhead。
