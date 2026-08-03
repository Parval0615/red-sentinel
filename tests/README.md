# 测试分层与执行边界

项目采用五层测试模型，并在迁移期保留历史测试目录，避免为目录整齐而进行高风险批量移动。

| 层级 | 目标 | 当前位置 |
|---|---|---|
| `unit` | 单函数、类或模块的隔离行为 | `tests/unit/` |
| `contract` | schema、协议、兼容和架构边界 | `tests/contract/`、历史 `tests/contracts/` |
| `integration` | 不依赖外部基础设施的跨模块链路 | `tests/integration/`、各包的 `tests/integration/` |
| `research` | 实验、基线、消融、统计和 provenance | `tests/research/`、`experiments/tests/` |
| `regression` | 历史公开行为、SDK、前端和产品流程 | `tests/regression/` 与保留原位的历史测试 |

根 `conftest.py` 在收集阶段为保留原位的测试补充分层 marker。没有
`docker`、`external_model` 或 `research_full` 标记的测试会自动获得 `fast`
标记，因此默认测试不需要 Docker daemon、网络或 API key。

## 命令

```bash
# 默认：确定性离线 fast suite
python -m pytest

# 完整离线 suite，包括扩展研究测试
python -m pytest -m "not docker and not external_model"

# 真实 Docker 集成；当前没有必须连接 daemon 的测试时会收集 0 项
python -m pytest -m docker

# 外部模型集成；必须显式准备网络和凭据
python -m pytest -m external_model

# 扩展研究实验
python -m pytest -m research_full
```

`docker` marker 只用于真实容器执行，而不是所有包含 Docker 配置或 mock
executor 的测试；`external_model` 同理。这样默认 suite 仍覆盖适配器和错误
边界，同时不会意外访问外部环境。
