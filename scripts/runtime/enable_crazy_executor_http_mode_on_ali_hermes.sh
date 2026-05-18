#!/usr/bin/env bash
set -euo pipefail

if [ "$(id -u)" -ne 0 ]; then
  echo "enable_crazy_executor_http_mode_on_ali_hermes.sh must run as root" >&2
  exit 1
fi

CAM_SERVICE_NAME="${CAM_SERVICE_NAME:-cam.service}"
CRAZY_LOCAL_BASE_URL="${CRAZY_LOCAL_BASE_URL:-http://127.0.0.1:5002}"
EXECUTOR_API_BASE_URL="${EXECUTOR_API_BASE_URL:-http://127.0.0.1:4788}"
EXECUTOR_SCOPE_ID="${EXECUTOR_SCOPE_ID:-}"

need_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "missing required command: $1" >&2
    exit 1
  fi
}

need_cmd curl
need_cmd systemctl

DROPIN_DIR="/etc/systemd/system/${CAM_SERVICE_NAME}.d"
mkdir -p "${DROPIN_DIR}"

cat >"${DROPIN_DIR}/executor-http-mode.conf" <<EOF
[Service]
Environment=EXECUTOR_API_BASE_URL=${EXECUTOR_API_BASE_URL}
EOF

if [ -n "${EXECUTOR_SCOPE_ID}" ]; then
  printf 'Environment=EXECUTOR_SCOPE_ID=%s\n' "${EXECUTOR_SCOPE_ID}" >>"${DROPIN_DIR}/executor-http-mode.conf"
fi

systemctl daemon-reload
systemctl restart "${CAM_SERVICE_NAME}"

attempt=0
until curl -fsS "${CRAZY_LOCAL_BASE_URL}/api/operations/integrations/provider-mode" >/dev/null 2>&1; do
  attempt=$((attempt + 1))
  if [ "${attempt}" -ge 20 ]; then
    systemctl status "${CAM_SERVICE_NAME}" --no-pager || true
    echo "cam.service did not expose /api/operations/integrations/provider-mode" >&2
    exit 1
  fi
  sleep 2
done

curl -fsS "${CRAZY_LOCAL_BASE_URL}/api/operations/integrations/provider-mode"
