# P1 实施日志

## 阶段状态

- 状态：`in_progress`
- 当前工作包：`P1-W1`
- 启动日期：2026-08-01
- 输入总结：`docs/research/stages/p0-summary.md`
- 执行计划：`docs/research/stages/p1-plan.md`

## 记录 001：P1 启动

### 输入

- P0 离线门禁：752 passed，Ruff passed；
- OpenManus source/commit/benchmark 已固定；
- OpenManus real runtime：`not_evaluated`；
- 四类核心 arm 和五类消融已有离线实现；
- RQ1–RQ5 矩阵已有 formal tier。

### 本次完成

- 将 P1 拆分为 W0–W6；
- 设置 OpenManus 1-seed real gate；
- 设置第二 Agent 选择门禁；
- 定义 2 Agents × 2 Models × 4 Arms × 3 Seeds 核心 pilot；
- 增加 random mutation 与 no-evidence-feedback 诊断对照；
- 定义成本、失败率、pair completeness 和 Formal Go/No-Go；
- 明确环境与凭据属于人工输入，不允许 fixture 替代。

### 发现的协议缺口

1. `benchmarks-v1.json` 当前按 `benchmark_id` 分组，不能在单个 OpenManus benchmark 内可靠隔离 development/holdout。
2. `rq-matrix-v1.yaml` 尚未包含第二真实 Agent 和模型家族维度。
3. OpenManus monitor 只从 keyword `messages` 取值，位置参数路径需修复与测试。
4. OpenManus Product 入口的 baseline/guarded 配对尚未直接覆盖四类研究 arm。
5. P0 未正式测量 clean utility、token/cost 和受控 overhead。

### 当前允许结论

- P1 已进入协议冻结阶段；
- 真实实验矩阵、门禁和预算已定义；
- 尚无新增真实 Agent 效果数字。

### 当前禁止结论

- OpenManus 已验证；
- 两个 Agent 或两个模型已完成；
- 协同进化优于基线；
- pilot 或正式实验已经开始。

### 下一启动条件

- 创建并审查 `p1-experiment-protocol-v1.md`；
- 冻结 split schema 和 failure taxonomy；
- 为 positional messages 增加失败复现测试。

## 记录 002：Docker、镜像与 W0 协议落地

### 环境与镜像

- Docker Desktop server：`29.6.1`；
- 架构：`aarch64/arm64`；
- storage driver：`overlayfs`；
- image：`redsentinel/openmanus-real:local`；
- image digest：`sha256:a9957e037041a6c39e42e767e1f3015ce78303847ab42fad6b0375cdc9c1a377`；
- Dockerfile SHA-256：`686a9bf3b25baaf4431d9bdb5cddc056de3408c6eff89380a7694a80da20f4e6`；
- image 构建基线：`python:3.12-slim-bookworm`；
- Chromium 实际 headless launch：passed；
- `BrowserUseTool` import/instantiate：passed；
- runtime `config.toml` 未烘焙进镜像：passed。

Dockerfile 修复：

1. 从不受 Playwright 支持的 trixie 切换到 bookworm；
2. 不再过滤 `browser-use`；
3. 移除 Chromium 安装的 `|| true`；
4. 增加 BrowserUseTool 和 Chromium executable 强制健康检查；
5. runner 注册真实 `BrowserUseTool`。

### W0 完成内容

- 冻结 `research/protocols/p1-experiment-protocol-v1.md`；
- 新增 `datasets/splits/p1-split-v1.json`；
- protocol SHA-256：`473bd8ad1818855d69f1028c22848a6232134548c0ff988be79c8dd7c29664cd`；
- split SHA-256：`46e67a361998a2ffce6166dcbea569586cc917a334215e75317bc206ff47962c`；
- development 4 pair、holdout 2 pair；
- split 按 `pair_id + payload_lineage` 隔离；
- 新增 benchmark hash、场景全集和 lineage validator；
- benchmark manifest 不再只按 `benchmark_id` 分组；
- 新增结构化 P1 failure taxonomy 和指标聚合；
- invalid runtime 不进入 ASR/DSR/FPR/utility 分母，但保留实际成本；
- `model_refusal` 分母策略必须显式选择。

### OpenManus 正确性修复

- 修复 monitor 只读取 keyword `messages` 的盲点；
- 覆盖 keyword、positional、空消息和非列表消息；
- 修复 adapter 内指向不存在包的迁移遗留 import；
- 新增 `redsentinel doctor --real-openmanus`。

### 验证

- P1 split/dataset tests：20 passed；
- P1 protocol 定向 tests：23 passed；
- OpenManus/CLI/P1 综合定向 tests：38 passed；
- Ruff 指定规则：passed；
- `doctor --real-openmanus`：
  Docker、image、vendor source 均通过，模型环境缺失，按设计退出 3。

### 当前阻塞

- `OPENAI_API_KEY` 未设置；
- `OPENAI_BASE_URL` 未设置；
- `OPENAI_MODEL` 未设置；
- 模型 B 及第二 Agent 尚未冻结；
- OpenManus 上游没有原生 `send_email` 工具，邮件外传 case 需要受控工具映射或标记 `not_applicable`。

### 下一启动条件

- 用户提供模型 A 的 endpoint/model id/测试 key；
- 完成 W1 剩余 runtime/refusal/secret scan 测试；
- 执行 OpenManus 1-seed connectivity，再决定是否进入全 case。

## 工作包进度

| 工作包 | 状态 | 证据 |
|---|---|---|
| W0 协议、数据与指标冻结 | completed | protocol/split/metrics/RQ pilot matrix 已冻结 |
| W1 OpenManus 正确性 | in_progress | positional/import/doctor/browser 完成 |
| W2 OpenManus 1-seed real gate | blocked_model_config | Docker/image ready |
| W3 第二 Agent | pending | - |
| W4 双模型与预算 | blocked_input | model/provider selection |
| W5 3-seed pilot | pending | - |
| W6 分析与总结 | pending | - |

## 记录 003：P1-W0 收口

### RQ pilot matrix

- 在 `rq-matrix-v1.yaml` 中增加受 schema 校验的 P1 pilot 设计；
- 固定核心矩阵：2 Agents × 2 Models × 4 Arms × 3 Seeds = 48 cells；
- 固定诊断矩阵：2 Agents × 2 Models × 2 Controls × 3 Seeds = 24 cells；
- 固定总上限 72 cells、3,000 model calls、24 小时和 150 USD；
- Agent A 固定为 `openmanus-real`；
- Agent B 保持 `pending_w3`，不得在选择门禁前声称已接入；
- Model A/B 保持 `pending_w4`，不得在元数据冻结前写入 family/model id；
- matrix SHA-256：
  `2324a9901b0714e0ca2137f77dfc710b8b32e07553860fcbacb92fccd1ad2511`。

### Schema 门禁

- 冻结槽位必须包含可追溯标识；
- 待决槽位不得携带未冻结标识；
- core arms、diagnostic controls 和 seeds 必须完整且唯一；
- `max_cells` 必须等于所有矩阵轴的笛卡尔积。

### 验证

- RQ matrix、P1 split 和 P1 metrics 定向测试：16 passed；
- 全量回归：766 passed，3 个既有弃用告警；
- Ruff：passed；
- read-only matrix CLI：passed；
- Docker image digest 复核：
  `sha256:a9957e037041a6c39e42e767e1f3015ce78303847ab42fad6b0375cdc9c1a377`。

### 结论

- P1-W0 已完成；
- P1-W1 继续处理 runtime/refusal/secret scan 正确性；
- P1-W2 仍只被模型 endpoint、精确 model id 和测试 key 阻塞。
