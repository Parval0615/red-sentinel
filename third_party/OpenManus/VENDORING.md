# OpenManus Vendoring Notes

## Source

- Upstream: `https://github.com/FoundationAgents/OpenManus.git`
- Pinned commit: `52a13f2a57d8c7f6737eefb02ccf569594d44273`
- License: MIT, see `LICENSE.upstream`.
- Vendored at: `third_party/OpenManus/upstream`.
- Vendored on: `2026-07-03`.

## Local Policy

RedSentinel keeps upstream OpenManus source as ordinary vendored files so the
competition evidence can be reproduced without cloning during the run.

Runtime integration should be implemented through RedSentinel overlay files under
`third_party/OpenManus/redsentinel_runtime/` and SDK code under `sdk/python/src`.
Avoid broad edits inside `third_party/OpenManus/upstream` unless upstream APIs
make an overlay impossible.

## Do Not Commit

Do not commit generated OpenManus runtime state:

- `third_party/OpenManus/upstream/.venv/`
- `third_party/OpenManus/upstream/workspace/`
- `third_party/OpenManus/upstream/config/config.toml`
- browser caches
- Python caches
- Docker/container logs
- real API keys or local `.env` files

Official real-runtime evidence is written under `runs/product/.../evaluations/`
or `runs/openmanus-real/`, with secrets redacted.
