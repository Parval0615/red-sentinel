# Tests

测试目录结构与 `src/arl/` 包结构镜像。

```
tests/
├── sandbox/
├── telemetry/
├── memory/
├── runner/
├── injectors/
├── detection/
└── integration/    # 跨模块集成测试（Phase 1 W6 重点）
```

## 原则

- Phase 1 结束时应具备 integration 测试，验证 sandbox → telemetry → runner 全链路
- 所有测试须使用固定 seed，保证 CI 可重放
- 检测模块测试以 Phase 2 受控注入数据为 fixture
