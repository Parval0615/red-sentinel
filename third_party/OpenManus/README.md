# OpenManus Version Evidence

RedSentinel does not vendor the full OpenManus repository in this workspace. The adapter uses an offline fixture by default so SDK and Product API tests run without network access, browser dependencies, or LLM keys.

Pinned upstream:

```bash
git clone https://github.com/FoundationAgents/OpenManus.git third_party/OpenManus/upstream
git -C third_party/OpenManus/upstream checkout 52a13f2a57d8c7f6737eefb02ccf569594d44273
```

Version evidence is stored in `VERSION.json`.

License: MIT.

Runtime integration: `agent_security_sdk.openmanus.OpenManusAdapter` accepts an optional injected runner for a real OpenManus process. Without that runner it uses `fixtures/offline_turn.json`.
