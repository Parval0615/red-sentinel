# 重构清理与兼容层决策

## 已删除

- `optimize_frontend.py`
  - 无静态或动态入口引用；
  - 仅对 `frontend/index.html` 做一次性字符串替换；
  - dashboard 源文件和渲染测试已包含其有效结果；
  - 删除后 Product API 与 frontend 回归通过。
- 工作树开发缓存
  - 删除 111 个被 Git 忽略的 `__pycache__`、`.pytest_cache`、`.ruff_cache` 目录；
  - 删除被忽略的 `.DS_Store` 文件；
  - 明确保留 `runs/`、`attack-runs/`、`defense-runs/`、`evidence-runs/`、
    `experiments/results/`、`logs/`、`storage/` 和 third-party workspace；
  - 验证命令使用 `PYTHONDONTWRITEBYTECODE=1` 与
    `pytest -p no:cacheprovider`，未重新生成上述缓存。

## 已合并

- 根 `run.py`、`run-demo.py`、`run-comp2.py`、`run-comp3.py`、`run-comp4.py`、
  `run-openmanus-real.py` 均已变为 `redsentinel` 兼容入口的薄包装。
- JSONL 攻击 case loader 和 dry-run runner 由 `redsentinel.attacks` 提供统一入口。
- profiling 的 builder/schema/LLM evidence 路径由 `redsentinel.profiling` 公开，旧路径转发。
- monitor decision 由 `redsentinel.defenses` 公开，旧路径保持对象兼容。
- evaluation/reporting/runtime/adapters 的实际实现已迁入对应 canonical engine；
  旧 benchmark/evaluation/report runner 仅保留兼容 alias，不再维护重复实现。
- FastAPI 使用 `ProductApplicationService`，按 Agent、评测、报告和监督职责组合。

## 索引归档（原址保留）

- 当前研究路线由根 `README.md` 和 `ROADMAP.md` 定义。
- 历史比赛和本地产品路线统一索引位于
  `docs/archive/legacy-competition-product-roadmap.md`。
- `docs/competition/`、`docs/product/` 和历史报告保留原路径，避免破坏
  证据包、论文引用和外部链接；这属于索引归档，不是物理迁移。
- 原址历史文档不再作为当前研究完成状态；其“完成”仅对应当时交付口径。

## 保留的兼容入口与复现资产

- 旧 `auto_*_system`、`agent_integration_system` 与 `agent_security_sdk` 包：
  仅保留 compatibility alias/re-export，正式模块不再依赖这些命名空间。
- 根 `run*.py` 薄包装：历史复现和外部使用情况未知；计划在 1.0.0 退出条件满足后删除。
- AutoGen scaffold 与边界测试：用于保证未误宣称可运行能力。
- deterministic fixtures：是 golden 回归和论文方法正确性证据。
- `third_party/OpenManus`：真实 runtime 需要固定版本和许可证，仅从
  `redsentinel.adapters` 边界访问。

## 兼容层退出决策

本轮决定 **兼容路径保留到 1.0.0 前**。实现迁移已经完成，但删除旧 import
路径的外部退出条件尚未全部满足：

1. 历史比赛复现文档仍固定旧入口；
2. 当前环境无法完成真实 OpenManus 等价运行；
3. 外部消费者使用情况未知。

删除前必须再次执行：

- 活跃源码与文档旧路径扫描；
- 动态 import、CLI 和 artifact consumer 扫描；
- 新路径 contract/integration/regression 全量测试；
- 真实 OpenManus 等价验证；
- archived 文档固定到旧 release 或迁移到新入口。

保留兼容层不允许继续向旧包添加新研究能力。

## 配置与产物迁移

- `redsentinel.migration.legacy_config_to_manifest()` 支持：
  - `redsentinel.yaml` / `agent-manifest-v1`；
  - 旧 scenario YAML；
  - `agent_config.example.json` 形态的 Product CLI 配置。
- Product CLI 配置中的 API key、密码和凭据不会进入 `ExperimentManifest`。
- `redsentinel.migration.read_legacy_artifact()` 可无损读取旧报告、画像和
  COMP 证据 JSON。
- `redsentinel.migration.migrate_legacy_artifact()` 会生成
  `experiment-manifest-v1.json`、`raw-result-v1.json`、`provenance-v1.json`
  和 `evidence-index-v1.json`，原 payload 保存在 `legacy-artifact-envelope-v1`
  内。

示例：

```python
from redsentinel.migration import legacy_config_to_manifest, migrate_legacy_artifact

manifest = legacy_config_to_manifest(
    "examples/agents/simple_agent/redsentinel.yaml",
    seed=42,
)
migrate_legacy_artifact(
    "docs/competition/evidence-pack/convergence.json",
    "artifacts/migrated-convergence",
)
```

## Task 26 深迁移结果

- `src/redsentinel` 对 `auto_attack_system`、`auto_defense_system`、
  `auto_evaluation_system`、`agent_integration_system` 和
  `agent_security_sdk` 的直接 Python import 扫描为 0。
- profiling、attack、defense、evaluation、runtime、reporting、application 和
  SDK 实现已迁入对应 `redsentinel` 域。
- 电商 demo 与 OpenManus 集成已从通用 defense 域隔离到 adapters。
- 旧包叶子模块使用模块 alias 保持类、函数和模块级可变状态身份。
- 迁移证据见 `research/refactor/task26-verification.json`。

## 本轮明确保留

- 运行证据、实验结果、日志、存储和 third-party workspace 虽被 `.gitignore`
  排除，但可能包含用户数据或复现证据，本轮不删除。
- benchmark/evaluation/report 的旧入口已统一指向 canonical 实现；旧包不再
  保存独立 runner 逻辑。
- 历史材料保留原址是链接兼容决策，不是待完成的物理归档工作。

## Task 25 验证记录

- 本地 Markdown 链接检查：38 份文档，0 个失效本地链接。
- 正式模块导入检查：10 个模块全部通过。
- 相邻回归：229 passed。
- 完整离线回归：749 passed，3 个既有弃用 warning。
- 脚本复核：唯一低风险删除候选仍为已删除的 `optimize_frontend.py`；其余根
  `run*.py` 是有退出条件的兼容薄包装，没有发现新的可安全删除临时脚本。
