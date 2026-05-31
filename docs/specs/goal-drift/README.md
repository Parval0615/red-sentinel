# Goal Drift 形式化定义

**Phase 2 · Week 7–8 · 最高优先级**

本目录存放 Goal Drift Metric (GDM) 的操作性定义文档。这是整个研究的智识核心——定义错误将导致 Phase 3 全部返工。

## 待产出

- [ ] Goal Representation 结构（向量或逻辑公式编码）
- [ ] GDM 数学定义与计算流程
- [ ] 对比法基线协议（有/无注入的轨迹差异）
- [ ] 一致性检测协议（trajectory 探针问题）
- [ ] 内部 review 记录（W8 门禁）

## 门禁

W8 结束前须完成内部 review，确认：

1. 定义具有**可计算性**（能写代码实现）
2. 定义具有**可验证性**（能用受控实验检验）

未通过 review 前，不得开始 `src/arl/detection/goal_drift/` 的实现。

## 参考

- [ROADMAP Phase 2](../../ROADMAP.md#任务-1goal-drift-形式化定义)
- [Phase 2 摘要](../phases/phase-2.md)
