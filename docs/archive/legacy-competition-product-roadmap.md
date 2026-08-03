# 历史比赛与产品路线索引归档

本文件归档 2026 年 6 月前 RedSentinel 以比赛交付和本地产品原型为中心的路线。它用于解释代码来源，不代表当前研究框架完成状态。

本归档采用“索引归档 + 原址保留”，不是物理搬迁。`docs/competition/`、
`docs/product/` 和历史报告继续保留原路径，以避免破坏证据包、论文引用和
外部链接；本文件是统一历史入口，并隔离历史“完成”口径与当前研究状态。

## 历史阶段

- `P0/M0`：共享契约、Agent onboarding 和画像生成。
- `A 线 FE0-FE3`：单文件 dashboard、ASR 曲线、节点归因和对比报告。
- `B 线 M1-M5`：物料感知、静态/LLM 画像、画像驱动攻击、攻击自进化和 Docker 轨迹。
- `C 线 M3-M6`：评测报告、反馈路由、防御挂载、防火墙优化和本地租户隔离。
- `COMP1-COMP4`：闭环 demo、攻击覆盖、防御回归和证据包。

这些编号描述历史交付顺序，不再作为长期模块边界。对应能力已映射到：

| 历史路线 | 当前研究模块 |
|---|---|
| M0/M1/M1.5 | `redsentinel.profiling` |
| COMP2/M2/M2.5 | `redsentinel.attacks`、`redsentinel.research.evolution` |
| COMP3/M4/M4.5 | `redsentinel.defenses` |
| M3/M3.5/COMP4 | `redsentinel.evaluation`、`redsentinel.reporting` |
| M5 | `redsentinel.runtime`、`redsentinel.adapters` |
| FE0-FE3 | 可选 `frontend/` 研究 dashboard |

## 历史证据入口

- 比赛报告与复现：[`../competition/README.md`](../competition/README.md)
- 固定证据包：[`../competition/evidence-pack/README.md`](../competition/evidence-pack/README.md)
- 产品交付文档：[`../product/final-handoff.md`](../product/final-handoff.md)
- 安全风险报告：[`../security-risk-report.md`](../security-risk-report.md)

历史文档中的“完成”只表示当时比赛或本地试点验收通过，不等价于生产级、跨 Agent 泛化或论文假设已验证。
