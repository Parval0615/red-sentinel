# RedSentinel 安全攻防产品・总体 Roadmap

## 一、当前进度基线

| 阶段               | 状态                                                | 产出                                                         |
| ------------------ | --------------------------------------------------- | ------------------------------------------------------------ |
| P0 共享契约冻结    | ✅ 已完成并提交                                      | `AgentManifest` / `AgentProfile` / `OptimizationDirective` 三件套 schema + pydantic 模型 + 契约测试，统一出口于 `auto_evaluation_system.contracts` |
| M0 Onboarding 基础 | ✅ 已完成                                            | `redsentinel.yaml` 配置契约、loader/validator、画像生成 CLI、示例 agent |
| 全量回归           | ✅ 227 passed (2 个失败为环境缺可选依赖，非代码回退) | —                                                            |

P0/M0 合入 main 后，三条工作流可并行启动。

------

## 二、工作流划分

按系统目录切分，确保文件级几乎零冲突；三流共同 import 已冻结的 `contracts`。

| 工作流              | 主责                     | 独占写目录                                                   | 职责                                              |
| ------------------- | ------------------------ | ------------------------------------------------------------ | ------------------------------------------------- |
| **A・前端可视化**   | 安全可视化报告           | `frontend/`、`auto_evaluation_system/.../dashboard/`         | 评测结果可视化：攻击用例 → 成功率 → 拦截点 → 结论 |
| **B・攻击与输入层** | 物料接入 + 画像驱动攻击  | `auto_attack_system/`(含 `ingestion/`)                       | 物料 → manifest → 画像驱动攻击                    |
| **C・评测与防御**   | 优化中枢 + 加固 + 多租户 | `auto_evaluation_system/`(除 dashboard)、`auto_defense_system/` | 双向优化指令 + 细粒度加固 + 租户隔离              |

------

## 三、各工作流里程碑

### A 工作流：安全可视化报告

数据来源已存在 ——`product_api/reports.py` 产出的 `AgentSecurityReport` 已含 `overall_score / attack_success_rate / false_positive_rate / findings`, 前端只读不写后端。

| 里程碑                  | 内容                                                         | 依赖                    |
| ----------------------- | ------------------------------------------------------------ | ----------------------- |
| FE0 设计与数据对齐      | 报告 JSON → 视图字段映射、视觉稿、`frontend/README` 数据契约 | 现有报告结构，即开      |
| FE1 概览与指标          | 总分 / ASR / 误伤率 / 风险等级仪表盘 + ASR 收敛曲线          | FE0                     |
| FE2 攻击用例 × 拦截详情 | 用例表 (场景 / 威胁类别 / 强度 / 结果)+ 节点级拦截归因 + 轨迹回放 | FE1; 节点归因依赖 C・M3 |
| FE3 结论与对比          | 结论卡 (加固前后 ASR delta、修复 / 遗留 findings)+ before/after 对比 | C·M4 retest             |

**技术约束**: 延续 "单文件零依赖 HTML artifact" 路线，可 `file://` 直接打开；图表用内联轻量库；**禁止在沙箱内起监听端口的服务**, 本地预览仅用静态 HTML。

### B 工作流：攻击与企业输入层

| 里程碑          | 内容                                                         | 门禁                              |
| --------------- | ------------------------------------------------------------ | --------------------------------- |
| M1 输入层       | `AgentManifest` 解析器 (T0 API/OpenAPI + T1 节点配置)、completeness 评分 | 能产出通过 schema 校验的 manifest |
| M2 画像驱动攻击 | 改 `AttackAgent`: 按 `AgentProfile` 暴露面生成 `AttackSpec` + 通用兜底 | 复现 "只打暴露面 + 兜底全覆盖"    |
| M5 物料深度接入 | T2 Docker 镜像隔离沙箱采轨迹 + T3 源码静态分析 (源码不出域)  | 隔离沙箱实跑产合规轨迹            |

### C 工作流：评测中枢 + 防御 + 多租户

| 里程碑          | 内容                                                         | 门禁                                           |
| --------------- | ------------------------------------------------------------ | ---------------------------------------------- |
| M3 优化指令中枢 | `OptimizationDirective` builder (读轨迹产攻防双路指令)+ append-only ledger + 节点级拦截归因 | replay 同 seed 复现同轨迹同指令，ledger 防篡改 |
| M4 细粒度加固   | `DEFENSE_PLAYBOOK` 细到 node/tool + scheme (prompt\|rag),retest before/after | 定向后 ASR 显著降、误伤率 ≤5%                  |
| M6 多租户隔离   | P0 数据 / 物料隔离 → P2 控制面，存储收敛到 `storage.py`      | 跨租户隔离测试 100%(发布门禁)                  |
| 报告数据维护    | 维护 `reports.py` 的 `AgentSecurityReport`, 按前端字段清单供数 | 前端字段不缺供                                 |

------

## 四、并行关系与依赖图

```plaintext
P0/M0 已合入 main ✅
   │
   ├─ A 线: FE0 ─→ FE1 ─→ FE2 ────→ FE3
   │        (即开)        ↑依赖C.M3  ↑依赖C.M4
   │
   ├─ B 线: M1 ─→ M2 ──────────→ M5
   │        (即开) ↑依赖profile mock
   │
   └─ C 线: M3 ─→ M4 ─→ M6
            (即开)
```

**立即并行启动 (P0 已合，无阻塞)**:A 的 FE0+FE1 (只读现有报告)、B 的 M1、C 的 M3 及 `dashboard/` 拆分重构。

**跨流依赖与解耦手段**:

| 依赖                    | 缓解方式                                                 |
| ----------------------- | -------------------------------------------------------- |
| A・FE2 ← C・M3 节点归因 | C 先供 mock 归因 JSON,A 用 mock 完成视图，真数据无缝替换 |
| A·FE3 ← C·M4 retest     | 同样用 mock 对比数据解耦                                 |
| B・M2 ← 画像生成        | 先供 mock profile,B 并行开发                             |

------

## 五、分支策略与文件归属

```plaintext
main(已含 P0/M0)
 ├─ feat/frontend/dashboard      ← A
 ├─ feat/attack/ingestion        ← B (M1)
 ├─ feat/attack/profile-driven   ← B (M2)
 ├─ feat/eval/optimizer-hub      ← C (M3)
 ├─ feat/defense/fine-grained    ← C (M4)
 └─ feat/eval/multitenant        ← C (M6)
```

文件归属矩阵 (w = 写，r = 只读):

| 目录 / 文件                                 | A     | B     | C     |
| ------------------------------------------- | ----- | ----- | ----- |
| `frontend/`(新)                             | **w** | –     | –     |
| `dashboard/`(空→A)                          | **w** | –     | r     |
| `auto_attack_system/`(含 ingestion)         | –     | **w** | r     |
| `auto_evaluation_system/.../optimizer/`(新) | r     | r     | **w** |
| `auto_defense_system/`                      | –     | –     | **w** |
| `product_api/reports.py`                    | r     | –     | **w** |
| `contracts/`、`schemas/`                    | r     | r     | r     |

**防冲突铁律**:

1. 契约已冻结，改 `contracts`/`schemas` 必走单独 contract 分支 + 三流 review。
2. `reports.py` 的 A/C 交叉点，开工前由 C 一次性把 `render_html_dashboard` 拆到 `dashboard/` 包，彻底切开数据 (C) 与渲染 (A)。
3. 每日 rebase main,PR ≤400 行，新增优先于修改。

------

## 六、阶段推进门禁

| 推进闸口     | 通过条件                                      |
| ------------ | --------------------------------------------- |
| 进入并行开发 | P0/M0 合入 main + 全量回归绿 (补齐可选依赖后) |
| FE2/FE3 启动 | C 提供对应 mock 数据契约                      |
| M2 启动      | 画像 mock 就绪                                |
| M6 发布      | 跨租户隔离测试 100%                           |
| 任意 PR 合入 | 不跌破现有测试基线                            |
