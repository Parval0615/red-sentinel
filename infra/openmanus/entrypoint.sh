#!/usr/bin/env sh
set -eu

mkdir -p "${OPENMANUS_WORKSPACE:-/workspace}" "${RED_SENTINEL_ARTIFACTS:-/tmp/redsentinel-artifacts}"

if [ "${RED_SENTINEL_METADATA_MOCK:-1}" = "1" ]; then
  python /opt/openmanus/redsentinel_runtime/mock_metadata_server.py >/tmp/redsentinel-metadata.log 2>&1 &
  attempts=0
  until nc -z 127.0.0.1 "${RED_SENTINEL_METADATA_PORT:-80}"; do
    attempts=$((attempts + 1))
    if [ "$attempts" -ge 20 ]; then
      echo "metadata mock failed to start" >&2
      exit 1
    fi
    sleep 0.1
  done
fi

exec python /opt/openmanus/redsentinel_runtime/real_runner.py "$@"
