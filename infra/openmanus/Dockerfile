FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    OPENMANUS_ROOT=/opt/openmanus \
    OPENMANUS_WORKSPACE=/workspace \
    RED_SENTINEL_ARTIFACTS=/tmp/redsentinel-artifacts \
    PYTHONPATH=/opt/openmanus:/opt/openmanus/redsentinel_runtime:/opt/redsentinel/auto_defense_system/src:/opt/redsentinel/auto_evaluation_system/src:/opt/redsentinel/sdk/python/src

WORKDIR /opt/openmanus

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        git \
        ca-certificates \
        netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

COPY third_party/OpenManus/upstream/ /opt/openmanus/
COPY third_party/OpenManus/redsentinel_runtime/ /opt/openmanus/redsentinel_runtime/
COPY auto_defense_system/ /opt/redsentinel/auto_defense_system/
COPY auto_evaluation_system/ /opt/redsentinel/auto_evaluation_system/
COPY sdk/python/ /opt/redsentinel/sdk/python/

RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir -r /opt/openmanus/requirements.txt \
    && python -m playwright install --with-deps chromium || true

RUN mkdir -p /workspace /tmp/redsentinel-artifacts

COPY infra/openmanus/entrypoint.sh /entrypoint.sh
COPY infra/openmanus/mock_metadata_server.py /opt/openmanus/redsentinel_runtime/mock_metadata_server.py
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
