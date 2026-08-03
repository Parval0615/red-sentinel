# P0 简历可投版本执行计划

## 1. 阶段目标

P0 将现有研究框架整理为适合 AI 安全实习投递的可信项目：

- 面试官 30 秒理解定位；
- 5 分钟理解方法和个人贡献；
- 10 分钟在无网络环境完成离线演示；
- 每个简历数字都有证据等级和路径；
- 真实 OpenManus 未运行时明确标记，不用模拟数据替代。

## 2. 输入基线

- 统一命名空间：`redsentinel.*`；
- 统一 CLI：`profile/evaluate/evolve/demo/experiment/report/doctor`；
- 单轮离线评测、九阶段协同进化、四类基线和五类消融；
- 数据 manifest、provenance、evidence index 和论文图表；
- 重构完成时默认离线测试基线：749 passed；P0 完成门禁：752 passed；
- 当前环境限制：Docker daemon 不可用，外部模型凭据缺失，真实 OpenManus 未重跑。

## 3. 非目标

- 不完成正式多 seed 论文实验；
- 不新增攻击类别；
- 不扩展 SaaS、租户或管理后台；
- 不把离线 smoke 结果写成真实 Agent 结果；
- 不在 P0 完成第二个真实 Agent 接入；
- 不对三个创新候选做最终论文结论。

## 4. 工作包与任务

### P0-W1：项目定位和个人贡献

- [x] P0-1.1：确定一句话中文/英文定位。
- [x] P0-1.2：编写 30 秒、2 分钟、5 分钟项目介绍。
- [x] P0-1.3：说明与企业知识引擎质量保障实习的能力衔接。
- [x] P0-1.4：说明密码学背景在完整性、威胁模型和可信证据中的作用。
- [x] P0-1.5：列出个人实现、第三方依赖和历史已有能力边界。

验证：介绍材料不含“生产级”“支持任意 Agent”等无证据表述。

### P0-W2：简历和项目一页说明

- [x] P0-2.1：编写中文项目标题和三条简历 bullet。
- [x] P0-2.2：编写英文项目标题和三条简历 bullet。
- [x] P0-2.3：编写一页项目说明，包含问题、方法、结果、边界和代码入口。
- [x] P0-2.4：建立数字证据清单，标记运行模式、证据等级和路径。
- [x] P0-2.5：区分“面试可讲、论文可用、暂不可使用”三类结论。

验证：每条含数字的表述均可追溯到 evidence index 或测试记录。

### P0-W3：五分钟离线演示

- [x] P0-3.1：建立统一的一键 P0 demo 入口。
- [x] P0-3.2：演示 `doctor -> profile -> evaluate -> evolve -> evidence`。
- [x] P0-3.3：准备提示注入、工具滥用、记忆/目标风险三条典型轨迹。
- [x] P0-3.4：输出 ASR、FPR、business success、overhead 和运行模式。
- [x] P0-3.5：为命令失败、目录污染和缺少可选依赖设计降级路径。
- [x] P0-3.6：编写逐分钟演示讲稿和预期输出。

验证：干净临时输出目录、无网络、无 Docker、无 API key 条件下完成。

### P0-W4：真实 OpenManus 预演

- [x] P0-4.1：建立 Docker、vendored source、模型环境和镜像 preflight。
- [x] P0-4.2：冻结 OpenManus commit、镜像、benchmark 和模型参数。
- [x] P0-4.3：准备 baseline/guarded 双跑命令。
- [x] P0-4.4：验证 runtime error、timeout、拒答和安全拦截的归因。
- [x] P0-4.5：建立真实运行报告模板。
- [x] P0-4.6：有环境时运行；无环境时记录 `not_evaluated` 和缺失项。

验证：没有 `real_runtime=true` 且 `simulated=false` 的产物时，简历材料不得引用真实 OpenManus 数字。

### P0-W5：README 首屏和证据卡

- [x] P0-5.1：README 首屏突出求职定位、主贡献和核心链路。
- [x] P0-5.2：加入当前证据卡和运行模式边界。
- [x] P0-5.3：将 5 分钟演示命令放到快速开始前部。
- [x] P0-5.4：保留详细研究、Product API 和历史文档导航。
- [x] P0-5.5：确保 README 不把 R1 smoke 描述为正式论文实验。

验证：新读者只看 README 前两屏可回答“做什么、为什么、结果是什么、怎么运行”。

### P0-W6：面试准备

- [x] P0-6.1：整理至少 10 个核心面试问题。
- [x] P0-6.2：每个问题准备结论、证据、局限和追问。
- [x] P0-6.3：准备系统设计、算法、实验可信度和密码学四类问题。
- [x] P0-6.4：准备“最失败的一次设计”和“如果重做会删除什么”。
- [x] P0-6.5：准备个人贡献和第三方边界说明。

验证：答案与代码和证据一致，不依赖夸大描述。

### P0-W7：阶段验证和总结

- [x] P0-7.1：运行默认离线测试和静态检查。
- [x] P0-7.2：在临时目录运行完整 P0 demo。
- [x] P0-7.3：检查所有文档链接和证据路径。
- [x] P0-7.4：人工审查简历数字和真实/模拟边界。
- [x] P0-7.5：创建 `p0-summary.md`。
- [x] P0-7.6：记录 P1 输入、阻塞、成本和优先级。

## 5. 任务依赖

```text
W1 定位
 ├─> W2 简历材料
 ├─> W5 README
 └─> W6 面试题

W3 离线演示 ─> W2 数字证据 ─> W5 README
W4 OpenManus 预演 ───────────> W2 真实结果边界

W1-W6 ─> W7 阶段验证与总结
```

可并行：

- W1 与 W3；
- W2 与 W4；
- W5 与 W6。

## 6. 交付物路径

| 交付物 | 路径 |
|---|---|
| Roadmap | `ROADMAP.md` |
| P0 计划 | `docs/research/stages/p0-plan.md` |
| 项目定位与介绍 | `docs/research/career/project-positioning.md` |
| 简历材料 | `docs/research/career/resume-project.md` |
| 项目一页说明 | `docs/research/career/project-one-pager.md` |
| 面试问题 | `docs/research/career/interview-guide.md` |
| 演示讲稿 | `docs/research/demo/p0-demo-script.md` |
| OpenManus 预演记录 | `docs/research/demo/openmanus-preflight.md` |
| P0 证据卡 | `docs/research/stages/p0-evidence-card.md` |
| P0 总结 | `docs/research/stages/p0-summary.md` |
| 演示产物 | `artifacts/p0-demo/` |

## 7. 验收门禁

- [x] 默认离线测试通过。
- [x] Ruff 指定规则通过。
- [x] P0 demo 无网络可运行。
- [x] 三条典型轨迹有 evidence ref。
- [x] 四类基线和五类消融状态可展示。
- [x] 所有简历数字完成证据分级。
- [x] README 首屏完成求职向收敛。
- [x] 中文/英文简历 bullet 完成。
- [x] 面试题库完成。
- [x] OpenManus 真实运行已完成，或明确 `not_evaluated`。
- [x] P0 阶段总结和 P1 handoff 完成。

## 8. 风险和处理

| 风险 | 处理 |
|---|---|
| 材料过多，主线不清 | 所有材料围绕“证据约束、效用感知的协同进化” |
| 离线结果被误用 | 每个数字强制附运行模式和证据等级 |
| OpenManus 环境不可用 | preflight 和报告模板先完成，结果保持 not_evaluated |
| Demo 时间超限 | 固定小样本和输出目录，不删除 provenance |
| 简历像论文摘要 | bullet 强调工程动作、规模、结果和验证 |
| 简历像产品宣传 | 删除企业级、生产级、全自动等无证据词 |

## 9. 阶段状态

当前状态：`已完成（真实 OpenManus 延后至 P1）`

完成定义：第 7 节全部通过；环境缺失可使 OpenManus 保持 `not_evaluated`，但必须从简历真实结果中排除。
