#!/usr/bin/env sh
set -eu

mkdir -p "${OPENMANUS_WORKSPACE:-/workspace}" "${RED_SENTINEL_ARTIFACTS:-/tmp/redsentinel-artifacts}"

if [ "${RED_SENTINEL_METADATA_MOCK:-1}" = "1" ]; then
  python /opt/openmanus/redsentinel_runtime/mock_metadata_server.py >/tmp/redsentinel-metadata.log 2>&1 &
fi

exec python /opt/openmanus/redsentinel_runtime/real_runner.py "$@"
