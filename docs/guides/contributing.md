# 贡献指南

## 开发原则

- Python 实现统一进入 `src/redsentinel/`，不得重新创建旧命名空间。
- 保持 core -> domain -> application -> apps 的依赖方向。
- 小步迁移；功能移动和算法创新分开提交。
- 只为非显然约束、研究口径和副作用写注释。
- 不提交密钥、真实敏感数据、缓存、大型模型或运行产物。

## 变更流程

1. 明确研究问题或缺陷及验收标准。
2. 为行为变化先补复现测试。
3. 选择 unit、contract、integration、research 或 regression 层。
4. 运行默认 fast suite。
5. 按需运行 Docker、external model 或 research full suite。
6. 更新 manifest、provenance 和文档。

工程迁移与创新实验必须使用独立提交：迁移提交只证明行为等价，创新提交单独引入算法、假设和结果变化。不要在同一提交中同时搬目录并宣称指标提升。

## 测试

```bash
python -m pytest -q
python -m pytest -q -o addopts=''
python -m ruff check . --select F401,F841,F821,F811
```

Markers：

- `fast`：默认确定性离线测试；
- `docker`：需要可达 Docker daemon；
- `external_model`：需要网络和模型凭据；
- `research_full`：耗时正式实验；
- `unit/contract/integration/research/regression`：测试层。

## 研究结果

新增指标或结论必须：

- 定义分子、分母和零分母行为；
- 定义环境失败处理；
- 使用冻结数据划分；
- 输出原始结果和聚合结果；
- 报告不确定性和效应量；
- 能从图表追溯到原始 JSON。

## 历史资产

历史规范和报告只在 `docs/archive/` 维护。当前代码、测试、配置和复现命令
不得依赖归档路径。
