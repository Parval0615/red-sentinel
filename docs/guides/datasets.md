# 数据集治理指南

## Manifest

每个正式数据集必须在 `datasets/manifests/` 中声明：

- `dataset_id`、版本和 schema version；
- 来源、许可证和用途；
- 文件列表及 SHA-256；
- 标签定义；
- 生成脚本和随机种子；
- development/holdout 或 train/dev/test 划分；
- provenance group。

Loader 会拒绝版本不匹配、哈希变化、路径越界和来源组缺失。

## 数据划分

划分单位是来源组，而不是单条文本。相同 payload 的编码、改写、语言变体和同一生成模板必须进入同一划分，避免进化过程看到 holdout 的近重复样本。

- development：实现、调参、阈值和候选选择。
- holdout：冻结后最终评估。
- fixtures：仅用于确定性测试，不作为外部效度证据。

## 标签

每条样本至少定义攻击类别、预期策略、安全成功条件和业务效用条件。`ask` 是否视为阻断必须由实验协议明确，不能在分析阶段临时改变。

## 许可证与敏感信息

- 未确认许可证的数据不得进入正式实验发布包。
- 不保存真实企业数据、原始 API key、访问令牌或个人敏感信息。
- 外部数据的清洗和派生过程必须可审计。
- 大型数据、模型权重和缓存放在外部存储或 `artifacts/`，不直接提交 Git。

## 更新流程

1. 修改或生成数据。
2. 检查来源组和划分泄漏。
3. 更新版本和 SHA-256。
4. 运行 `tests/research/test_dataset_governance.py`。
5. 记录对既有实验可比性的影响。
