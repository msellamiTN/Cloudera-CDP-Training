#!/usr/bin/env bash
set -euo pipefail
echo "=== DataCo environment ==="
for cmd in docker curl python3; do
  command -v "$cmd" >/dev/null 2>&1 || { echo "[ERROR] Missing $cmd"; exit 1; }
  echo "[OK] $cmd"
done
docker compose version
docker compose ps
echo "API health (if already started):"
curl -fsS http://localhost:8001/health || true
echo
echo "Streamlit (if already started):"
curl -fsSI http://localhost:8501 || true
