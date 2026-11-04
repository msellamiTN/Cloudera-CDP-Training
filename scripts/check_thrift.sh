#!/usr/bin/env bash
set -euo pipefail
HOST="${HBASE_THRIFT_HOST:-localhost}"
PORT="${HBASE_THRIFT_PORT:-9090}"
echo "Checking TCP reachability: ${HOST}:${PORT}"
timeout 3 bash -c "</dev/tcp/${HOST}/${PORT}" 2>/dev/null || {
  echo "[ERROR] Thrift TCP port is unreachable"
  exit 1
}
echo "[OK] TCP port reachable (protocol handshake still needs application-level validation)"
