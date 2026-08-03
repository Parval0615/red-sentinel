# Agent 与 Runtime Adapter 指南

Adapter 把具体 Agent 框架或服务转换为统一执行协议。新增 adapter 不应修改攻击、评测或协同进化算法。

## 支持边界

| Adapter | 状态 | 用途 |
|---|---|---|
| Direct API | 稳定 fixture | 确定性重放 |
| LangGraph | 稳定 fixture | 图式轨迹重放 |
| Docker | 实验性 | 隔离执行和 bounded capture |
| OpenManus | fixture 稳定、真实运行环境依赖 | 开源 Agent 验证 |
| HTTP/OpenAI-compatible | 实验性 | 黑盒 Agent |
| SDK | 实验性 | 进程内接入 |
| AutoGen | scaffold | 不可运行 |

## 实现要求

Adapter 应：

- 实现 `RuntimeAdapter` 或相应公开协议；
- 输出版本化 `Trajectory`；
- 标注 `offline_fixture`、`simulated_runtime` 或 `real_runtime`；
- 区分 timeout、runtime error、policy block 和业务结果；
- 对 stdout/stderr、步骤数和执行时间设置边界；
- 不记录原始密钥；
- 提供最小 fixture 和契约测试。

## 新增流程

1. 在 `src/redsentinel/adapters/` 新增薄适配，不复制研究算法。
2. 在 registry 声明能力与运行模式。
3. 增加 schema-valid fixture trajectory。
4. 增加 contract 和 integration 测试。
5. 记录第三方版本、许可证和环境依赖。
6. 在 RQ 配置中明确该 adapter 是否可用于正式证据。

真实运行失败不得回退为模拟成功。若缺少 Docker 或凭据，应返回明确环境错误或跳过原因。
