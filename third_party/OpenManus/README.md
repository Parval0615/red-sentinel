# OpenManus Version Evidence

<<<<<<< HEAD
RedSentinel vendors the pinned OpenManus source under `third_party/OpenManus/upstream`
for real-runtime evaluation. The offline fixture remains only for lightweight SDK
unit tests and must not be used as official competition evidence.
=======
RedSentinel does not vendor the full OpenManus repository in this workspace. The adapter uses an offline fixture by default so SDK and Product API tests run without network access, browser dependencies, or LLM keys.
>>>>>>> origin/main

Pinned upstream:

```bash
git clone https://github.com/FoundationAgents/OpenManus.git third_party/OpenManus/upstream
git -C third_party/OpenManus/upstream checkout 52a13f2a57d8c7f6737eefb02ccf569594d44273
```

Version evidence is stored in `VERSION.json`.

License: MIT.

<<<<<<< HEAD
Runtime integration:

- Official evidence path: Dockerized real runtime via `run-openmanus-real.py`.
- Development fallback only: `agent_security_sdk.openmanus.OpenManusAdapter` can still
  use `fixtures/offline_turn.json` when no real runner is configured.
- Any report containing `offline fixture result` or `OpenManus simulated` is not valid
  real OpenManus evidence.
=======
Runtime integration: `agent_security_sdk.openmanus.OpenManusAdapter` accepts an optional injected runner for a real OpenManus process. Without that runner it uses `fixtures/offline_turn.json`.
>>>>>>> origin/main
