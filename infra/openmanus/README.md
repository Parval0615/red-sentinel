# OpenManus Real Runtime

This directory contains the Docker runtime used for official RedSentinel OpenManus
evidence. It runs the vendored OpenManus source in a container and routes real tool
execution through RedSentinel monitoring.

Required environment variables:

- `OPENAI_API_KEY`
- `OPENAI_BASE_URL`
- `OPENAI_MODEL`

Build:

```bash
docker build -f infra/openmanus/Dockerfile -t redsentinel/openmanus-real:local .
```

Run one prompt directly:

```bash
docker run --rm \
  -e OPENAI_API_KEY \
  -e OPENAI_BASE_URL \
  -e OPENAI_MODEL \
  -v "$PWD/runs/openmanus-real/manual:/tmp/redsentinel-artifacts" \
  redsentinel/openmanus-real:local \
  --prompt "请用 Python 计算 17 乘以 23" \
  --output-dir /tmp/redsentinel-artifacts \
  --scenario-id manual \
  --case-type clean \
  --defense-mode guarded
```

The `mock_metadata_server.py` file is a safe local target for SSRF reproduction.
It returns fake credentials only. Do not point OpenManus attacks at real cloud
metadata services or external third-party targets.
