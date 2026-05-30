# Agent Runtime Security Lab — 完整研究路线图

> 从零开始构建的 Agent 运行时安全研究基础设施 · 共四个阶段 · 约 24 周

---

## 总览

| 阶段 | 名称 | 周期 | 核心目标 |
|------|------|------|----------|
| Phase 1 | Sandbox & Telemetry Foundation | Week 1–6 | 搭建可观测、可重放的实验基础设施 |
| Phase 2 | Risk Injector & Goal Formalization | Week 7–12 | 实现受控风险注入 + Goal Drift 形式化定义 |
| Phase 3 | Detection & Trajectory Modeling | Week 13–19 | 构建检测算法与轨迹风险建模系统 |
| Phase 4 | Research Output & Publication | Week 20–24 | 论文产出、Benchmark 发布、开源 |

---

## Phase 1 · Sandbox & Telemetry Foundation

**周期**：Week 1–6  
**核心目标**：搭建可观测、可重放的实验基础设施  
**关键原则**：工程底座不稳，研究结论就没有说服力

### 任务 1：Agent 沙箱环境构建

- 选定并集成多框架支持：LangGraph、AutoGen、Direct API 三轨并行
- 设计隔离执行环境，确保实验之间完全无状态污染
- 实现 deterministic seed 机制或 LLM response caching，保证可重放性
- 搭建 Mock Tool Registry，支持 real/mock 工具无缝切换
- 建立 Agent 配置管理系统（goal、system prompt、memory config）

### 任务 2：Telemetry 采集系统

- 定义标准化 Trajectory 数据结构（含推理步骤、工具调用、状态变化）
- 实现 out-of-band 观测层，与 Agent 执行层完全解耦
- 采集维度：LLM input/output、tool call 序列、memory read/write、时间戳
- 设计 session 级别快照机制，支持任意时刻的状态回溯
- 建立 telemetry overhead 监控，防止观测行为影响 Agent 决策

### 任务 3：Memory 存储架构

- 双轨存储：向量数据库（Chroma/Qdrant）+ 关系数据库（PostgreSQL）
- 设计 memory schema：short-term / long-term / episodic 三层分离
- 实现 memory CRUD 的完整 audit log
- 建立实验隔离的 memory namespace 机制

### 任务 4：实验编排系统（基础版）

- 实现场景配置的 YAML/JSON 描述格式
- 构建实验调度队列，支持串行与并行实验执行
- 实现实验结果的结构化存储与基础 diff 对比功能

### 交付物

| 交付物 | 说明 |
|--------|------|
| Sandbox SDK | 多框架 Agent 隔离执行环境 |
| Telemetry Schema v1 | 标准化轨迹数据结构定义 |
| Memory Store | 双轨存储系统（向量 + 关系） |
| Experiment Runner | 实验调度与编排工具 |
| Architecture Doc | 系统架构设计文档 |

### 周度进度

| 周期 | 重点任务 | 优先级 |
|------|----------|--------|
| W1–2 | 框架集成 + 沙箱隔离 | ⭐ 关键 |
| W3–4 | Telemetry 管道搭建 | ⭐ 关键 |
| W5 | Memory 双轨存储 | 正常 |
| W6 | 实验编排 + 集成测试 | 正常 |

> ⚠️ **注意**：可重放性（deterministic replay）是本阶段最重要的单一目标。宁可多花一周，也不能跳过。

---

## Phase 2 · Risk Injector & Goal Formalization

**周期**：Week 7–12  
**核心目标**：实现受控风险注入，完成 Goal Drift 的形式化定义  
**关键原则**：Goal 形式化是整个研究的智识核心，定义写错了后面全部返工

### 任务 1：Goal Drift 形式化定义

> 本任务是 Phase 2 的最高优先级，独立占用 W7–8 两周

- 设计 Goal Representation 结构：将 Agent 目标编码为可计算的向量或逻辑公式
- 定义 Goal Drift Metric（GDM）：量化目标在 trajectory 中的偏移程度
- 实现对比法基线：有/无风险注入的轨迹差异作为 drift ground truth
- 设计一致性检测协议：在 trajectory 不同步骤中注入探针问题
- **关键产出**：Goal Drift 的操作性定义文档（需通过内部 review 确认可操作性后再推进）

### 任务 2：Memory Poisoning 注入器

- 在向量数据库层实现精准的 embedding 投毒机制
- 设计毒素强度梯度（微量污染 → 重度污染），支持参数化注入量
- 实现三类投毒策略：语义相近替换、权威伪造注入、时序操控注入
- 建立注入后的 retrieval 验证机制，确保毒素被实际召回
- 输出：可复现的 Memory Poisoning 实验套件

### 任务 3：Tool Tampering 注入器

- 实现 tool response 劫持层：在 Tool Registry 和 Agent 之间插入代理
- 支持三类篡改：返回值替换、延迟注入、渐进式可信度降解
- 设计 tool dependency graph，追踪工具调用链上的错误传播
- 实现 tool 权限越界模拟场景

### 任务 4：Goal Perturbation 注入器

- System prompt 层扰动：目标语义的渐进式修改实验
- Context window 层扰动：在对话历史中植入目标漂移触发器
- 实现扰动强度的精细控制（0.0–1.0 连续尺度）
- 设计多轮对话场景下的目标漂移追踪协议

### 交付物

| 交付物 | 说明 |
|--------|------|
| Risk Injector Suite | 三类风险注入器的完整实现 |
| Goal Drift 定义文档 | 操作性的 GDM 形式化定义 |
| 受控实验 Baseline | 有/无注入的对比实验基线数据 |
| Poisoning 实验数据集 | 带标注的 Memory Poisoning 实验记录 |
| Tool Tamper Proxy | Tool 响应劫持与篡改代理层 |

### 周度进度

| 周期 | 重点任务 | 优先级 |
|------|----------|--------|
| W7–8 | Goal 形式化定义（两周专项） | ⭐ 关键 |
| W9–10 | Memory Poisoning 注入器 | ⭐ 关键 |
| W11 | Tool Tamper 代理层 | 正常 |
| W12 | Goal Perturbation 注入 | 正常 |

> ⚠️ **注意**：W8 结束时须完成 Goal Drift 定义的内部 review，确认定义具有可计算性与可验证性，否则不得推进 Phase 3。

---

## Phase 3 · Detection & Trajectory Modeling

**周期**：Week 13–19  
**核心目标**：构建基于轨迹数据的风险检测与建模系统  
**关键原则**：这是从工程转向真正研究的阶段，所有检测方法的有效性依赖于 Phase 1–2 的数据质量

### 任务 1：Trajectory Risk Modeling

- 将 Agent 轨迹建模为有状态的马尔可夫风险过程
- 构建 Trajectory Risk Score（TRS）：基于行为序列的实时风险估计
- 实现轨迹相似度计算（DTW / 编辑距离改造版），支持语义对齐
- 建立 risk-annotated trajectory 数据集（正常 vs. 已知风险注入）
- 实现轨迹异常的早期预警机制（步骤 N 时预测后续 K 步的风险）

### 任务 2：Goal Drift 检测器

- 实现基于 GDM 的在线检测管道，支持流式 trajectory 输入
- 构建行为签名模型：将原始目标编码为行为向量基准
- 设计滑动窗口检测算法，平衡检测延迟与准确率
- 实现多粒度检测：步骤级、对话轮级、任务级
- 构建 ROC / precision-recall 评估框架，以受控注入实验作为 ground truth

### 任务 3：Memory Poisoning 检测

- 设计 retrieval 一致性检测：同一语义查询在不同时刻的召回稳定性
- 实现 memory 溯源机制：追踪每条 memory 的注入来源与影响范围
- 构建 poisoning 影响评估模型：量化毒素 memory 对 Agent 决策的影响幅度
- 输出：Memory Integrity Score（MIS）实时指标

### 任务 4：分析引擎与可视化

- 构建 Risk Dashboard：实时显示 TRS、GDM、MIS 三大核心指标
- 实现轨迹可视化工具：时序图 + 风险热力图
- 建立实验对比视图：受控注入前后的 trajectory diff
- 实现 anomaly pattern 自动标注与聚类

### 交付物

| 交付物 | 说明 |
|--------|------|
| Goal Drift Detector | 在线 GDM 检测管道 |
| Trajectory Risk Model | TRS 计算与预警模型 |
| Memory Integrity Score | MIS 实时指标系统 |
| Risk Dashboard v1 | 三大核心指标可视化看板 |
| Annotated Dataset v1 | 带风险标注的轨迹数据集（公开） |

### 周度进度

| 周期 | 重点任务 | 优先级 |
|------|----------|--------|
| W13–14 | TRS 建模基础 | ⭐ 关键 |
| W15–16 | Goal Drift 检测器 | ⭐ 关键 |
| W17 | Memory Poisoning 检测 | 正常 |
| W18 | 分析引擎搭建 | 正常 |
| W19 | 评估 + 基准测试 | 正常 |

---

## Phase 4 · Research Output & Publication

**周期**：Week 20–24  
**核心目标**：将研究成果转化为论文、Benchmark 与开源项目

### 任务 1：论文撰写（Memory Poisoning 优先）

- **Paper #1（早期目标）**：Memory Poisoning in Agentic Systems — Taxonomy & Detection
  - 内容：注入框架、MIS 指标定义、检测实验、与现有工作对比
  - 目标投稿：CCS / IEEE S&P / USENIX Security
- **Paper #2（后续）**：Goal Drift in LLM Agents — Formalization & Runtime Detection
- **Paper #3（长期）**：Trajectory Risk Modeling for Agent Runtime Security

> Memory Poisoning 排第一的原因：已有一定学术讨论基础，更容易 position，审稿人更易接受。Goal Drift 是真正的空白，但正因为空白，审稿人判断更难，放在第二篇。

### 任务 2：Benchmark 套件构建

- 发布 AgentRiskBench：标准化风险注入场景集（≥ 200 个实验用例）
- 覆盖四大研究方向的评测维度
- 提供 Docker 一键部署的可复现实验环境
- 建立公开排行榜（Leaderboard）机制，便于后续研究者对比

### 任务 3：开源发布与社区建设

- 开源 Agent Runtime Security Lab 基础设施代码（Apache 2.0）
- 撰写详细的 CONTRIBUTING.md 和研究复现文档
- 发布技术博客系列（Medium / arXiv preprint 对应）
- 申请研究合作：与 Anthropic、DeepMind Safety 团队接触

### 任务 4：下一阶段研究规划

- Multi-Agent 系统中的风险传播研究（Phase 5 预研）
- 实时防御机制研究：从检测到 mitigation
- 与 LLM 提供商合作的 in-context 安全机制研究
- 基金申请：NSF / DARPA / 企业研究合作

### 交付物

| 交付物 | 说明 |
|--------|------|
| 论文草稿 ×2 | Paper #1 投稿版 + Paper #2 草稿 |
| AgentRiskBench | 标准化风险评测 Benchmark |
| 开源代码库 | Apache 2.0 · 含完整文档 |
| 技术博客 ×4 | 每个研究方向各一篇 |
| Conference Talk | 顶会 Talk 材料（Slides + 摘要） |

### 周度进度

| 周期 | 重点任务 | 优先级 |
|------|----------|--------|
| W20–21 | Paper #1 撰写 | ⭐ 关键 |
| W22 | Benchmark 打包发布 | ⭐ 关键 |
| W23 | 开源 + 博客发布 | 正常 |
| W24 | 投稿 + 规划 Phase 5 | 正常 |

---

## 研究方向优先级矩阵

| 研究方向 | 学术成熟度 | 工程难度 | 差异化潜力 | 建议定位 |
|----------|------------|----------|------------|----------|
| Goal Drift | 低（几乎空白） | 高 | ⭐⭐⭐⭐⭐ | 核心研究方向 |
| Trajectory Risk Modeling | 低 | 极高 | ⭐⭐⭐⭐⭐ | 核心研究方向 |
| Memory Poisoning | 中（有少量工作） | 中 | ⭐⭐⭐⭐ | 早期发表突破口 |
| Tool Security | 中（有 ToolEM 等工作） | 中 | ⭐⭐⭐ | 其他方向的技术支撑 |

---

## 关键风险与应对

**风险 1：Goal Drift 形式化失败**  
应对：预留 W7–8 两整周，阶段末做内部 review。定义不满足可操作性则回炉，不得带着错误定义进入 Phase 3。

**风险 2：测量工具影响被测对象**  
应对：设计 out-of-band 观测机制，观测层与执行层物理隔离。定期做 overhead 基准测试，量化 telemetry 对 Agent 行为的影响。

**风险 3：实验不可复现**  
应对：Phase 1 强制实现 deterministic replay。所有实验必须附带 seed + 配置文件，能一键重跑。

**风险 4：Memory Poisoning 论文无法 position**  
应对：早期（Phase 2）就开始整理 related work，在 related work 中明确区分本研究与现有工作的边界。

---

## 核心设计原则

1. **可重放性（Reproducibility）**：每次实验必须能精确重放，这是所有研究结论的可信度基础。

2. **风险注入与自然涌现分离**：明确区分主动注入风险（受控实验）和自然涌现风险（观测实验），基础设施同时支持两种模式。

3. **轨迹作为一等公民**：不只记录 input/output，把完整 trajectory 作为核心数据结构存储和处理。

4. **工程先于研究**：Phase 1–2 是偏工程的阶段，Phase 3 才开始真正的研究。工程底座不稳，研究结论没有说服力。

5. **观测层与执行层解耦**：过重的 telemetry 会通过 context window 影响 Agent 行为，必须设计 out-of-band 的观测机制。

---

*文档版本：v1.0 · 生成于 Agent Runtime Security Lab 规划阶段*
