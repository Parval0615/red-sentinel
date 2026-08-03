# Research Application API

## Python 入口

稳定领域对象和协议从 `redsentinel.core` 导入。研究执行从 `redsentinel.research` 导入；具体 Agent 通过 `redsentinel.adapters` 接入。

Product API 从 `redsentinel.application` 导入 `ProductApplicationService`，其职责门面为：

- `agents`：注册、onboarding、画像和 session；
- `evaluations`：benchmark、评测、next round 和轨迹上传；
- `reporting`：报告、日志、dashboard summary 和对比；
- `supervision`：三态监督事件。

迁移期 `ProductEvaluationService` 仍是兼容实现。新 HTTP 路由不应直接访问其私有方法。

## CLI

```text
redsentinel profile
redsentinel evaluate
redsentinel evolve
redsentinel experiment
redsentinel report
redsentinel doctor
```

所有执行命令统一支持 `--output-dir`、`--seed`、`--dry-run` 和 `--log-level`。

退出码：

- `0`：成功；
- `2`：输入或配置错误；
- `3`：环境/可选依赖不可用；
- `4`：执行失败。

## REST 研究配置

- `GET /v1/research/experiments`
- `GET /v1/research/experiments/{rq_id}`

这些接口只读取并校验实验矩阵，不触发实验执行。

## 稳定性

`redsentinel.*` 是新公开路径。旧包路径在 1.0 前保留兼容，但会发出弃用警告；结构化 stdout 不包含警告文本。
