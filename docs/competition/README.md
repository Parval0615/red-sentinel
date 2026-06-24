# RedSentinel 竞赛提交入口

## 项目一句话

RedSentinel / 灵哨是一个面向 LLM Agent 的**红队攻击面研究与旁路行为监督系统**：它用 Attack Agent 枚举和升级攻击样本，用 guard、telemetry 和审计链监督模型响应与工具调用，再用 Evaluation / Defense Agent 量化风险并验证防御策略。

## 为什么值得看

多数安全项目只展示静态规则或单次攻击样本。RedSentinel 展示的是一条可复现的攻防监督链路：红队攻击战役能覆盖 7 类威胁，旁路监督能记录 guard decision 与 audit refs，防御策略能把 ASR 从 44% 降到 0%，且正常请求误伤率保持 0%。

## 核心结果

| 结论 | 当前结果 | 证据 |
|---|---:|---|
| 红队攻击面覆盖 | Attack reflection 后覆盖 7/7 | [`evidence-pack/ablation_table.md`](./evidence-pack/ablation_table.md) |
| 对抗可收敛 | ASR 44% → 0%，7 轮收敛 | [`evidence-pack/convergence_curve.png`](./evidence-pack/convergence_curve.png) |
| 防御策略有效 | 去掉 Defense 后 ASR 保持 44% | [`evidence-pack/ablation.json`](./evidence-pack/ablation.json) |
| 加固不伤正常请求 | 精准加固误伤率 0% | [`../product/product-readiness-audit.md`](../product/product-readiness-audit.md) |
| 工程可回归 | 215 passed, 1 skipped, 2 warnings | [`reproducibility.md`](./reproducibility.md) |

## 目录导览

| 文件 | 用途 |
|---|---|
| [`final-report.md`](./final-report.md) | 赛事三正式项目报告 |
| [`defense-script-8min.md`](./defense-script-8min.md) | 8 分钟中文讲解稿 |
| [`reproducibility.md`](./reproducibility.md) | 环境、安装、离线复现和验证命令 |
| [`submission-checklist.md`](./submission-checklist.md) | 提交前检查清单 |
| [`evidence-pack/`](./evidence-pack/) | 固化后的最终证据副本 |

## 推荐运行顺序

```powershell
python run.py --closed-loop-demo
python run.py --attack-campaign --offline
python run.py --defense-regression --offline
python run.py --evidence-pack --offline
python -m pytest -q
```

## 边界声明

- 所有攻击只作用于本地 mock 电商靶场。
- 不接真实淘宝、真实支付、真实企业数据或真实外部攻击目标。
- 无 API key 时使用 `--offline`，核心竞赛结果仍可确定性复现。