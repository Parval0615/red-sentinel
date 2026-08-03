# P0 阶段总结

## 1. 阶段结论

状态：`completed_with_real_runtime_deferred`

P0 已将研究框架整理为可投递、可演示、可追问的简历项目版本。离线主链路、证据边界、求职材料和阶段制度均已完成；真实 OpenManus 因 Docker daemon 和模型配置缺失保持 `not_evaluated`，符合 P0 降级规则，不影响阶段完成，但不产生任何真实运行效果结论。

## 2. 完成交付

| 工作包 | 结果 | 主要交付物 |
|---|---|---|
| W1 定位 | 完成 | `docs/research/career/project-positioning.md` |
| W2 简历材料 | 完成 | `resume-project.md`、`project-one-pager.md` |
| W3 五分钟演示 | 完成 | `redsentinel demo`、P0 summary、演示讲稿 |
| W4 OpenManus 预演 | 准备完成，真实运行 deferred | `openmanus-preflight.md` |
| W5 README/证据卡 | 完成 | `README.md`、`p0-evidence-card.md` |
| W6 面试准备 | 完成 | `interview-guide.md` |
| W7 验证与总结 | 完成 | 本文及 P1 handoff |

## 3. 代码与配置变更

- 在 `src/redsentinel/cli.py` 新增确定性 `demo` 子命令；
- 复用正式 evaluate/evolve 路径，不复制评测或进化算法；
- 在 `src/redsentinel/research/p0_demo.py` 建立机器可读汇总；
- 为 memory poisoning、tool tampering、goal perturbation 建立 report/audit/log 三层 evidence ref；
- 将相对输出目录标准化为绝对路径，修复跨包工作目录误解析；
- 新增 CLI、汇总结构和相对路径回归测试。

## 4. 验证证据

| 验证 | 结果 |
|---|---|
| `python -m pytest -q` | 752 passed，3 warnings |
| Ruff 指定规则 | passed |
| 全新临时目录 demo | passed |
| 仓库 `artifacts/p0-demo/` demo | passed |
| Summary 结构检查 | 3 risks、每条 3 refs、未测指标保持 `not_evaluated` |
| OpenManus preflight | source/Dockerfile ready；daemon/image/model env blocked |

离线 demo 固定结果：

```text
PAIRED_CASES=3/3
FPR=0.000000
ASR_INITIAL=0.437500
ASR_FINAL=0.000000
BUSINESS_SUCCESS_RATE=not_evaluated
OVERHEAD=not_evaluated
```

上述数字仅用于 `offline_fixture` 工程和算法 smoke。

## 5. 决策与边界

1. 项目唯一主贡献保持为“证据约束、效用感知的 Agent 攻防协同进化框架”。
2. 演示优先展示轨迹、归因和 provenance，不展示注册、租户或管理后台。
3. 不从 FPR 推导 business success rate，不把一次运行耗时当作 overhead。
4. OpenManus 报告只有同时满足 `real_runtime=true`、`simulated=false` 才能进入真实证据。
5. 749 是研究重构完成时的历史测试基线；P0 对外工程数字固定为 752。
6. 哈希链表述限定为篡改证据，不声称源真实性、不可抵赖或可信时间。

## 6. 遗留问题

- OpenManus 真实运行尚未执行；
- 第二个真实 Agent 尚未选择和接入；
- business success rate、latency、token/cost overhead 尚未正式测量；
- 当前 smoke 不是 holdout、多模型、多 seed 论文实验；
- 3 条依赖弃用 warning 需要在后续依赖治理中处理；
- OpenManus monitor 对位置参数消息的兼容风险应在真实运行前增加验证。

## 7. P1 Handoff

### P1 目标

建立第一批可用于真实 Agent 外部有效性分析的配对实验，不追求一次性形成论文结论。

### 启动输入

- P0 一键 demo 和证据卡；
- 固定 OpenManus commit `52a13f2a57d8c7f6737eefb02ccf569594d44273`；
- `openmanus-security-v0.1` benchmark；
- RQ1-RQ5 矩阵和四类基线；
- OpenManus preflight、失败分类和报告模板。

### P1 优先级

1. 修复/验证 OpenManus monitor 的 positional messages 路径；
2. 启动 Docker daemon，构建镜像并记录 digest；
3. 固定模型 A 的 provider、精确版本、temperature、token limit 和成本口径；
4. 执行 OpenManus 1-seed 全 case baseline/guarded smoke；
5. 审查环境、runtime、模型拒答、安全拦截和 evaluator failure 的归因；
6. 选择第二个 Agent，完成同一 trajectory contract 的最小 adapter；
7. 增加模型 B，执行两个 Agent × 两模型 × 3 seeds pilot；
8. 评估方差、预算和失败率后决定是否进入 5-10 seeds formal。

### P1 Go/No-Go

Go：

- 每个 arm 的完整 case 数一致；
- 环境失败不进入 DSR；
- baseline/guarded 使用相同模型、seed、预算和数据；
- 原始响应、trajectory、manifest、provenance、evidence index 完整；
- business success 和 overhead 有明确定义与测量入口。

No-Go：

- 真实运行标记缺失或出现 simulated fallback；
- 只保留最佳 seed；
- evaluator 无法区分拒答、超时和 Guard 拦截；
- benchmark 在 baseline/guarded 之间发生变化；
- 凭据、原始敏感数据或未授权目标进入产物。

## 8. Roadmap 调整建议

P1 不应同时追求第二 Agent、大规模 seed 和算法重写。先完成 OpenManus 1-seed 归因门禁，再接第二 Agent；算法深化继续留在 P2。若真实运行环境一周内仍不可用，应优先解决环境和预算，不以新增离线功能替代真实证据。
