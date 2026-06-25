# RedSentinel 安全攻防产品・总体 Roadmap

## 一、当前进度基线

| 阶段               | 状态                                                     | 产出                                                         |
| ------------------ | -------------------------------------------------------- | ------------------------------------------------------------ |
| P0 共享契约冻结    | ✅ 已完成并提交至 `feat/agent-integration-m0`，待合入 main | `AgentManifest` / `AgentProfile` / `OptimizationDirective` 三件套 schema + pydantic 模型 + 契约测试，统一出口于 `auto_evaluation_system.contracts` |
| M0 Onboarding 基础 | ✅ 已完成并提交至 `feat/agent-integration-m0`              | `redsentinel.yaml` 配置契约、loader/validator、画像生成 CLI、示例 agent |
| 聚焦回归           | ✅ 14 passed                                             | `agent_integration_system/tests` + `auto_evaluation_system/tests/contracts` |
| 全量回归           | ⏳ 待标准 Python 3.10+ 环境复跑                            | 合入 main 前必须补齐可选依赖并执行 `pytest -q`               |

P0/M0 合入 main 且全量回归通过后，三条工作流正式并行启动；合入前仅允许基于当前 feature 分支预研。

------

## 二、工作流划分

按系统目录切分，确保文件级几乎零冲突；三流共同 import 已冻结的 `contracts`。

| 工作流              | 主责                     | 独占写目录                                                     | 职责                                              |
| ------------------- | ------------------------ | -------------------------------------------------------------- | ------------------------------------------------- |
| **A・前端可视化**   | 安全可视化报告           | `frontend/`、`auto_evaluation_system/src/auto_evaluation_system/dashboard/` | 评测结果可视化：攻击用例 → 成功率 → 拦截点 → 结论 |
| **B・攻击与输入层** | 物料接入 + 画像驱动攻击  | `auto_attack_system/`、`auto_attack_system/src/auto_attack_system/ingestion/` | 物料 → manifest → profile → 画像驱动攻击          |
| **C・评测与防御**   | 优化中枢 + 加固 + 多租户 | `auto_evaluation_system/`(除 dashboard)、`auto_defense_system/` | 双向优化指令 + 细粒度加固 + 租户隔离              |

------

## 三、各工作流里程碑

### A 工作流：安全可视化报告

数据来源已存在 ——`product_api/reports.py` 产出的 `AgentSecurityReport` 已含 `overall_score / attack_success_rate / false_positive_rate / findings`, 前端只读不写后端。

| 里程碑                  | 内容                                                         | 门禁                    |
| ----------------------- | ------------------------------------------------------------ | ----------------------- |
| FE0 设计与数据对齐      | 报告 JSON → 视图字段映射、视觉稿、`frontend/README` 数据契约 | 字段清单和 mock 数据就绪 |
| FE1 概览与指标          | 总分 / ASR / 误伤率 / 风险等级仪表盘 + ASR 收敛曲线          | 静态 HTML 可本地打开     |
| FE2 攻击用例 × 拦截详情 | 用例表 (场景 / 威胁类别 / 强度 / 结果) + 节点级拦截归因 + 轨迹回放 | FE1 完成；节点归因依赖 C・M3 |
| FE3 结论与对比          | 结论卡 (加固前后 ASR delta、修复 / 遗留 findings) + before/after 对比 | C・M4 retest 数据就绪    |

**技术约束**: 延续 "单文件零依赖 HTML artifact" 路线，可 `file://` 直接打开；图表用内联轻量库；**禁止在沙箱内起监听端口的服务**，本地预览仅用静态 HTML。A 线只消费报告与 mock 数据，不反向修改评测逻辑。

### B 工作流：攻击与企业输入层

| 里程碑          | 内容                                                         | 门禁                              |
| --------------- | ------------------------------------------------------------ | --------------------------------- |
| M1 输入层       | `AgentManifest` 解析器 (T0 API/OpenAPI + T1 节点配置)、completeness 评分 | 能产出通过 schema 校验的 manifest |
| M2 画像驱动攻击 | 改 `AttackAgent`: 按 `AgentProfile` 暴露面生成 `AttackSpec` + 通用兜底 | 复现 "只打暴露面 + 兜底全覆盖"    |
| M5 物料深度接入 | T2 Docker 镜像隔离沙箱采轨迹 + T3 源码静态分析 (源码不出域)  | 隔离沙箱实跑产合规轨迹            |

**范围边界**: M1/M2/M5 主写攻击与输入层。若 M5 需要改 `auto_evaluation_system/sandbox/` 以支持 Docker 轨迹采集，必须拆单独小 PR 并让 C 线 review。

### C 工作流：评测中枢 + 防御 + 多租户

| 里程碑          | 内容                                                         | 门禁                                           |
| --------------- | ------------------------------------------------------------ | ---------------------------------------------- |
| M3 优化指令中枢 | `OptimizationDirective` builder (读轨迹产攻防双路指令) + append-only ledger + 节点级拦截归因 | replay 同 seed 复现同轨迹同指令，ledger 防篡改 |
| M4 细粒度加固   | `DEFENSE_PLAYBOOK` 细到 node/tool + scheme (prompt\|rag)，retest before/after | 定向后 ASR 显著降、误伤率 ≤5%                  |
| M6 多租户隔离   | P0 数据 / 物料隔离 → P2 控制面，存储收敛到 `storage.py`      | 跨租户隔离测试 100%(发布门禁)                  |
| 报告数据维护    | 维护 `reports.py` 的 `AgentSecurityReport`，按前端字段清单供数 | 前端字段不缺供                                 |

**范围边界**: C 线负责优化、加固、隔离和报告数据，不负责前端渲染；`contracts/` 与 `schemas/` 已冻结，M3 只能消费 `OptimizationDirective`，不能直接改契约。

------

## 四、并行关系与依赖图

```plaintext
P0/M0 合入 main + 全量回归绿
   │
   ├─ A 线: FE0 ─→ FE1 ─→ FE2 ────→ FE3
   │        (即开)        ↑依赖C.M3  ↑依赖C.M4
   │
   ├─ B 线: M1 ─→ M2 ──────────→ M5
   │        (即开) ↑依赖profile mock ↑依赖M1/M2 + C沙箱接口约定
   │
   └─ C 线: M3 ─→ M4 ─→ M6
            (即开) ↑依赖M3
```

**立即并行启动条件**: P0/M0 合入 main 且全量回归绿后，A 的 FE0+FE1、B 的 M1、C 的 M3 可同时启动；`dashboard/` 拆分重构由 A/C 先约定文件边界。

**跨流依赖与解耦手段**:

| 依赖                    | 缓解方式                                                 |
| ----------------------- | -------------------------------------------------------- |
| A・FE2 ← C・M3 节点归因 | C 先供 mock 归因 JSON，A 用 mock 完成视图，真数据无缝替换 |
| A・FE3 ← C・M4 retest   | C 先供 before/after mock 对比数据，A 先完成静态视图       |
| B・M2 ← 画像生成        | 使用 M0 example profile 和 mock profile，B 并行开发       |
| B・M5 ↔ C・sandbox      | B 定义物料输入，C 定义 sandbox 接口；跨线改动必须小 PR    |
| C・M4 ← C・M3           | M4 只消费 `OptimizationDirective`，不读取攻击侧内部状态   |

------

## 五、分支策略与文件归属

```plaintext
main(已含 P0/M0)
 ├─ feat/frontend/dashboard      ← A
 ├─ feat/attack/ingestion        ← B (M1)
 ├─ feat/attack/profile-driven   ← B (M2)
 ├─ feat/attack/deep-ingestion   ← B (M5)
 ├─ feat/eval/optimizer-hub      ← C (M3)
 ├─ feat/defense/fine-grained    ← C (M4)
 └─ feat/eval/multitenant        ← C (M6)
```

文件归属矩阵 (w = 写，r = 只读):

| 目录 / 文件                                 | A     | B     | C     |
| ------------------------------------------- | ----- | ----- | ----- |
| `frontend/`(新)                             | **w** | –     | –     |
| `auto_evaluation_system/.../dashboard/`     | **w** | –     | r     |
| `auto_attack_system/`                       | –     | **w** | r     |
| `auto_attack_system/.../ingestion/`(新)     | –     | **w** | r     |
| `auto_evaluation_system/.../optimizer/`(新) | r     | r     | **w** |
| `auto_evaluation_system/sandbox/`           | r     | r     | **w** |
| `auto_defense_system/`                      | –     | –     | **w** |
| `product_api/reports.py`                    | r     | –     | **w** |
| `agent_integration_system/`                 | r     | **w** | r     |
| `contracts/`、`schemas/`                    | r     | r     | r     |

**防冲突铁律**:

1. 契约已冻结，改 `contracts`/`schemas` 必走单独 contract 分支 + 三流 review。
2. `reports.py` 的 A/C 交叉点，开工前由 C 一次性把 `render_html_dashboard` 拆到 `dashboard/` 包，彻底切开数据 (C) 与渲染 (A)。
3. M5 若需改 sandbox，必须从 `feat/attack/deep-ingestion` 拆出跨线小 PR，并标注 C review。
4. 每日 rebase main，PR ≤400 行，新增优先于修改。

------

## 六、阶段推进门禁

| 推进闸口     | 通过条件                                      |
| ------------ | --------------------------------------------- |
| 进入并行开发 | P0/M0 合入 main + 全量回归绿 (补齐可选依赖后) |
| FE2 启动     | C 提供节点归因 mock 数据契约                  |
| FE3 启动     | C 提供 before/after retest mock 数据           |
| M2 启动      | M0 example profile + B 线 mock profile 就绪    |
| M5 启动      | M1 manifest 输入层稳定 + M2 profile-driven 攻击可复用 |
| M6 发布      | 跨租户隔离测试 100%(发布门禁)                 |
| 任意 PR 合入 | 不跌破现有测试基线；涉及契约需三流 review      |
