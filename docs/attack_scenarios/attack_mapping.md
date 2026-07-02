# Attack Scenario Mapping to MITRE ATLAS and ATT&CK

本文把 RedSentinel 的 7 类攻击场景映射到 MITRE ATLAS 和 MITRE ATT&CK。
映射目标不是把内部 taxonomy 生硬改名，而是让每类样本在外部威胁框架中有可解释的技术编号。

## 映射原则

1. Agent/LLM 特有行为优先映射到 MITRE ATLAS。
2. 传统系统侧行为只在语义明确时补充 MITRE ATT&CK。
3. 若 ATLAS 没有完全同名技术，使用主技术加说明的组合映射。
4. 每个场景保留 RedSentinel 内部 `scenario` 名称，避免破坏 case、脚本和 ASR 结果的追溯。
5. ASR 和 FPR 数字不在本文维护，统一来自 `asr_before_after.json` 和渲染表格。
6. `tool_tampering` 与 `goal_drift` 的工具型 case 在 ASR Runner v0.2 中走真实 `tool_call` 路由，
   使用 case 内的 `tool_name` 和 `arguments` 进入 `monitor_plugin.intercept`。

## 总览

| RedSentinel scenario | Primary MITRE ATLAS mapping | Supporting ATLAS mapping | Supporting ATT&CK mapping | 映射说明 |
|---|---|---|---|---|
| `jailbreak` | [AML.T0054 LLM Jailbreak](https://atlas.mitre.org/techniques/AML.T0054) | [AML.T0051 Direct LLM Prompt Injection](https://atlas.mitre.org/techniques/AML.T0051.000), [AML.T0068 LLM Prompt Obfuscation](https://atlas.mitre.org/techniques/AML.T0068) | 无直接 ATT&CK 等价 | 样本通过角色扮演、规则覆盖、编码混淆和多轮升级让模型绕过 guardrail。 |
| `training_data_leakage` | [AML.T0057 LLM Data Leakage](https://atlas.mitre.org/techniques/AML.T0057) | [AML.T0069 Discover LLM System Information](https://atlas.mitre.org/techniques/AML.T0069), [AML.T0085 Data from AI Services](https://atlas.mitre.org/techniques/AML.T0085) | [T1213 Data from Information Repositories](https://attack.mitre.org/techniques/T1213/), [T1213.006 Databases](https://attack.mitre.org/techniques/T1213/006/), [T1552 Unsecured Credentials](https://attack.mitre.org/techniques/T1552/) | 训练语料、系统提示、工具契约、PII、凭据和业务 KB 泄露均落在数据泄露与信息收集语义下。 |
| `environment_awareness_pollution` | [AML.T0080 AI Agent Context Poisoning](https://atlas.mitre.org/techniques/AML.T0080) | [AML.T0051.001 Indirect LLM Prompt Injection](https://atlas.mitre.org/techniques/AML.T0051.001), [AML.T0093 Prompt Infiltration via Public-Facing Application](https://atlas.mitre.org/techniques/AML.T0093) | [T1036 Masquerading](https://attack.mitre.org/techniques/T1036/) only as an analogy | 场景伪造“沙箱、租户、预授权、工具可用性”等环境事实，核心是污染 Agent 上下文。 |
| `prompt_injection` | [AML.T0051 LLM Prompt Injection](https://atlas.mitre.org/techniques/AML.T0051) | [AML.T0051.000 Direct](https://atlas.mitre.org/techniques/AML.T0051.000), [AML.T0051.001 Indirect](https://atlas.mitre.org/techniques/AML.T0051.001), [AML.T0068 LLM Prompt Obfuscation](https://atlas.mitre.org/techniques/AML.T0068), [AML.T0094 Delay Execution of LLM Instructions](https://atlas.mitre.org/techniques/AML.T0094) | 无直接 ATT&CK 等价 | 用户输入、检索内容、格式块或延迟指令试图覆盖系统/开发者约束。 |
| `tool_tampering` | [AML.T0053 AI Agent Tool Invocation](https://atlas.mitre.org/techniques/AML.T0053) | [AML.T0086 Exfiltration via AI Agent Tool Invocation](https://atlas.mitre.org/techniques/AML.T0086), [AML.T0081 Modify AI Agent Configuration](https://atlas.mitre.org/techniques/AML.T0081) | [T1565 Data Manipulation](https://attack.mitre.org/techniques/T1565/), [T1565.001 Stored Data Manipulation](https://attack.mitre.org/techniques/T1565/001/) | 工具参数、工具返回、价格、地址、库存或调用链被篡改时，对应 Agent 工具调用滥用和数据完整性破坏。 |
| `memory_poisoning` | [AML.T0080 AI Agent Context Poisoning](https://atlas.mitre.org/techniques/AML.T0080) | [AML.T0092 Manipulate User LLM Chat History](https://atlas.mitre.org/techniques/AML.T0092), [AML.T0093 Prompt Infiltration via Public-Facing Application](https://atlas.mitre.org/techniques/AML.T0093), [AML.T0020 Poison Training Data](https://atlas.mitre.org/techniques/AML.T0020) only for model-training datasets | [T1565.001 Stored Data Manipulation](https://attack.mitre.org/techniques/T1565/001/) only if memory is stored data at rest | 长期记忆被写入虚假事实时，本质是对 Agent 运行上下文和用户历史的污染；只有进入训练集才映射为训练数据投毒。 |
| `goal_drift` | [AML.T0051 LLM Prompt Injection](https://atlas.mitre.org/techniques/AML.T0051) as the entry technique | [AML.T0054 LLM Jailbreak](https://atlas.mitre.org/techniques/AML.T0054), [AML.T0053 AI Agent Tool Invocation](https://atlas.mitre.org/techniques/AML.T0053), [AML.T0048 External Harms](https://atlas.mitre.org/techniques/AML.T0048) for realized impact | 无直接 ATT&CK 等价 | ATLAS 没有“goal drift”单一技术。RedSentinel 将其解释为通过提示注入或越狱改变 Agent 任务目标，并可能落到工具滥用或外部影响。 |

## 场景细化

### 1. `jailbreak`

Primary: `AML.T0054 LLM Jailbreak`.

Supporting:

- `AML.T0051.000 Direct`，因为样本直接通过用户消息提交越狱指令。
- `AML.T0068 LLM Prompt Obfuscation`，因为部分样本使用编码、分隔符或格式混淆绕过规则。
- `AML.T0053 AI Agent Tool Invocation`，仅当越狱结果进一步调用 Agent 工具时使用。

可解释边界：

- Jailbreak 不是传统主机入侵技术，因此不强行映射 ATT&CK。
- 若 jailbreak 后触发 shell、文件、数据库或网络动作，后续动作再映射到对应 ATT&CK 技术。

### 2. `training_data_leakage`

Primary: `AML.T0057 LLM Data Leakage`.

Supporting:

- `AML.T0069 Discover LLM System Information`，用于系统提示、开发者消息、工具 schema 或特殊分隔符泄露。
- `AML.T0085 Data from AI Services`，用于从 AI 服务连接的数据面读取受保护内容。
- `T1213 Data from Information Repositories`，用于 KB、CRM、知识库、工单库或文档库内容泄露。
- `T1213.006 Databases`，用于订单、用户、审批规则等数据库来源资料泄露。
- `T1552 Unsecured Credentials`，用于密钥、token、连接串、密码等凭据泄露。

可解释边界：

- “训练数据泄露”在本项目中包含训练语料复述和敏感上下文泄露。
- 如果样本只诱导模型输出系统提示，则优先落到 `AML.T0069`。
- 如果样本诱导输出 PII、订单、业务规则或 KB 原文，则优先落到 `AML.T0057`，并补充 `T1213`。

### 3. `environment_awareness_pollution`

Primary: `AML.T0080 AI Agent Context Poisoning`.

Supporting:

- `AML.T0051.001 Indirect`，用于伪环境事实来自外部内容、检索文档或上下文片段的情况。
- `AML.T0093 Prompt Infiltration via Public-Facing Application`，用于污染内容通过公开入口进入后续会话或共享上下文的情况。
- `T1036 Masquerading` 仅作类比，因为攻击者伪装“内部沙箱、管理员、预授权环境”，但没有直接执行传统二进制伪装。

可解释边界：

- 该类不是普通 prompt injection 的同义词。
- 它关注的是 Agent 对运行环境、租户、工具状态、审批状态的错误信任。
- 若污染内容被写入长期记忆，则同时适用 `memory_poisoning` 的映射。

### 4. `prompt_injection`

Primary: `AML.T0051 LLM Prompt Injection`.

Supporting:

- `AML.T0051.000 Direct`，用于用户消息中的直接规则覆盖。
- `AML.T0051.001 Indirect`，用于网页、邮件、PDF、RAG 文档或工具返回中的隐藏指令。
- `AML.T0068 LLM Prompt Obfuscation`，用于 Base64、rot13、分隔符、低可见文本等混淆。
- `AML.T0094 Delay Execution of LLM Instructions`，用于“之后再执行”“下一轮再忽略规则”等延迟触发样本。

可解释边界：

- Prompt injection 是入口技术，不一定等于最终影响。
- 最终如果泄露数据，叠加 `AML.T0057`。
- 最终如果调用工具，叠加 `AML.T0053` 或 `AML.T0086`。
- 最终如果污染记忆，叠加 `AML.T0080` 或 `AML.T0092`。

### 5. `tool_tampering`

Primary: `AML.T0053 AI Agent Tool Invocation`.

Supporting:

- `AML.T0086 Exfiltration via AI Agent Tool Invocation`，用于工具写操作或外发工具被滥用导出数据。
- `AML.T0081 Modify AI Agent Configuration`，用于工具配置、能力声明、权限描述或 MCP/插件配置被修改。
- `T1565 Data Manipulation`，用于业务数据被篡改以影响决策或交易结果。
- `T1565.001 Stored Data Manipulation`，用于订单、库存、地址、价格、审批记录等持久化数据被修改。

可解释边界：

- 仅改变 LLM 文本输出不构成工具篡改。
- 必须出现工具参数、工具返回、工具链状态、工具配置或下游业务数据的可观测变化。
- 本项目 v0.2 case 使用 `call_type=tool_call`、`tool_name` 和 `arguments` 表达真实工具调用，
  不再只把工具篡改当作自然语言 prompt 文本。
- 若攻击只是诱导调用工具但未篡改参数，可只映射 `AML.T0053`。

### 6. `memory_poisoning`

Primary: `AML.T0080 AI Agent Context Poisoning`.

Supporting:

- `AML.T0092 Manipulate User LLM Chat History`，用于对用户历史、会话记录或可恢复上下文的操纵。
- `AML.T0093 Prompt Infiltration via Public-Facing Application`，用于污染内容通过共享入口持久传播。
- `AML.T0020 Poison Training Data`，仅当污染对象进入训练数据或微调数据集时使用。
- `T1565.001 Stored Data Manipulation`，仅当长期记忆落盘后被未授权修改时使用。

可解释边界：

- 本项目的 memory poisoning 是运行期/会话期记忆污染，不默认等同于训练数据投毒。
- 只有模型训练集、微调集或评测数据集被修改时，才使用 `AML.T0020`。
- 若污染来自普通用户输入并影响后续回合，`AML.T0080` 是更准确的主映射。

### 7. `goal_drift`

Primary: `AML.T0051 LLM Prompt Injection` as the entry technique.

Supporting:

- `AML.T0054 LLM Jailbreak`，用于通过越狱或角色重设软化原始任务边界。
- `AML.T0053 AI Agent Tool Invocation`，用于漂移后的新目标触发未授权工具调用。
- `AML.T0048 External Harms`，用于漂移目标造成财务、声誉或业务流程损害。

可解释边界：

- ATLAS 当前没有单独名为“Goal Drift”的技术。
- RedSentinel 将它定义为 Agent 任务契约被逐步替换或重排优先级。
- 映射时应记录入口、执行和影响三段，而不是只保留一个标签。
- 本项目 v0.2 中部分 goal drift 样本会落到真实 `tool_call`，用 `tool_name` 和 `arguments`
  表达漂移后的写入、外发或 API 调用动作，因此同时保留 `AML.T0053` 执行阶段映射。

## STRIDE 对齐

| Scenario | Spoofing | Tampering | Repudiation | Information Disclosure | Denial of Service | Elevation of Privilege |
|---|---:|---:|---:|---:|---:|---:|
| `jailbreak` | medium | medium | low | high | low | high |
| `training_data_leakage` | low | low | low | critical | low | medium |
| `environment_awareness_pollution` | high | high | medium | high | low | high |
| `prompt_injection` | medium | high | medium | high | low | high |
| `tool_tampering` | medium | critical | medium | high | medium | high |
| `memory_poisoning` | high | critical | high | high | low | high |
| `goal_drift` | medium | high | medium | high | medium | high |

## 引用路径

- Cases: `docs/attack_scenarios/<scenario>/cases.jsonl`
- Scripts: `auto_attack_system/src/auto_attack_system/scripts/attack_<scenario>.py`
- ASR runner: `experiments/run_asr_experiment.py`
- Table and figure renderer: `experiments/render_report_tables.py`
- Report: `docs/security-risk-report.md`
