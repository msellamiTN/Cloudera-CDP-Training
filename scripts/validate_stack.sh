#!/usr/bin/env bash
set -euo pipefail
API="${API_URL:-http://localhost:8001}"
DASHBOARD="${DASHBOARD_URL:-http://localhost:8501}"
PRODUCT_ID="${TEST_PRODUCT_ID:-1004}"

echo "[1/3] API health"
curl -fsS "${API}/health"
echo
echo "[2/3] Streamlit HTTP response"
curl -fsSI "${DASHBOARD}" >/dev/null
echo "[OK] Streamlit responds"
echo "[3/3] Real HBase-backed product lookup"
curl -fsS "${API}/products/${PRODUCT_ID}/analytics"
echo
echo "[OK] Stack validation completed"
