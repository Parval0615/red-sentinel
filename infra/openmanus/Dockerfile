FROM python:3.12-slim-bookworm

ARG APT_MIRROR=
ARG PIP_INDEX_URL=

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    OPENMANUS_ROOT=/opt/openmanus \
    OPENMANUS_WORKSPACE=/workspace \
    RED_SENTINEL_ARTIFACTS=/tmp/redsentinel-artifacts \
    PYTHONPATH=/opt/openmanus:/opt/openmanus/redsentinel_runtime:/opt/redsentinel/src

WORKDIR /opt/openmanus

RUN if [ -n "$APT_MIRROR" ]; then \
        sed -i "s|URIs: http://deb.debian.org/debian-security|URIs: $APT_MIRROR-security|g; s|URIs: http://deb.debian.org/debian|URIs: $APT_MIRROR|g" /etc/apt/sources.list.d/debian.sources; \
    fi \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        git \
        ca-certificates \
        netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

COPY third_party/OpenManus/upstream/requirements.txt /tmp/openmanus-upstream-requirements.txt

RUN python -m pip install --no-cache-dir --upgrade pip \
    && grep -Ev '^(crawl4ai|browsergym)' /tmp/openmanus-upstream-requirements.txt > /tmp/openmanus-real-requirements.txt \
    && if [ -n "$PIP_INDEX_URL" ]; then \
        python -m pip install --no-cache-dir -i "$PIP_INDEX_URL" -r /tmp/openmanus-real-requirements.txt; \
    else \
        python -m pip install --no-cache-dir -r /tmp/openmanus-real-requirements.txt; \
    fi \
    && if [ -n "$PIP_INDEX_URL" ]; then \
        python -m pip install --no-cache-dir -i "$PIP_INDEX_URL" structlog; \
    else \
        python -m pip install --no-cache-dir structlog; \
    fi \
    && python -m playwright install --with-deps chromium

COPY third_party/OpenManus/upstream/ /opt/openmanus/
COPY third_party/OpenManus/redsentinel_runtime/ /opt/openmanus/redsentinel_runtime/
RUN printf '%s\n' \
        '[llm]' \
        'model = "redsentinel-build-healthcheck"' \
        'base_url = "https://example.invalid/v1"' \
        'api_key = "build-healthcheck-not-a-runtime-secret"' \
        '[daytona]' \
        'daytona_api_key = "redsentinel-disabled"' \
        > /opt/openmanus/config/config.toml \
    && python -c "from app.tool.browser_use_tool import BrowserUseTool; BrowserUseTool()" \
    && python -c "from pathlib import Path; from playwright.sync_api import sync_playwright; p = sync_playwright().start(); executable = Path(p.chromium.executable_path); p.stop(); assert executable.is_file(), executable" \
    && rm /opt/openmanus/config/config.toml
COPY src/ /opt/redsentinel/src/
COPY configs/ /opt/redsentinel/configs/
COPY datasets/ /opt/redsentinel/datasets/
COPY schemas/ /opt/redsentinel/schemas/

RUN mkdir -p /workspace /tmp/redsentinel-artifacts

COPY infra/openmanus/entrypoint.sh /entrypoint.sh
COPY infra/openmanus/mock_metadata_server.py /opt/openmanus/redsentinel_runtime/mock_metadata_server.py
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
