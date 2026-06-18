#!/usr/bin/env bash
set -euo pipefail

if [ "$(id -u)" -ne 0 ]; then
  echo "install_executor_sidecar_on_ali_hermes.sh must run as root" >&2
  exit 1
fi

EXECUTOR_PORT="${EXECUTOR_PORT:-4788}"
EXECUTOR_SERVICE_NAME="${EXECUTOR_SERVICE_NAME:-executor-sidecar.service}"
EXECUTOR_STATE_DIR="${EXECUTOR_STATE_DIR:-/var/lib/executor-sidecar}"

need_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "missing required command: $1" >&2
    exit 1
  fi
}

need_cmd curl
need_cmd npm
need_cmd systemctl

resolve_executor_bin() {
  if command -v executor >/dev/null 2>&1; then
    command -v executor
    return 0
  fi

  if command -v npm >/dev/null 2>&1; then
    local npm_prefix
    npm_prefix="$(npm prefix -g 2>/dev/null || true)"
    if [ -n "${npm_prefix}" ] && [ -x "${npm_prefix}/bin/executor" ]; then
      printf '%s\n' "${npm_prefix}/bin/executor"
      return 0
    fi
  fi

  for candidate in \
    /usr/local/bin/executor \
    /usr/bin/executor \
    /opt/homebrew/bin/executor \
    "${HOME}/.nvm/versions/node"/*/bin/executor
  do
    if [ -x "${candidate}" ]; then
      printf '%s\n' "${candidate}"
      return 0
    fi
  done

  return 1
}

if command -v ss >/dev/null 2>&1; then
  if ss -ltn | awk '{print $4}' | grep -q ":${EXECUTOR_PORT}\$"; then
    if ! systemctl is-active --quiet "${EXECUTOR_SERVICE_NAME}"; then
      echo "port ${EXECUTOR_PORT} is already occupied by another process" >&2
      exit 1
    fi
  fi
fi

mkdir -p "${EXECUTOR_STATE_DIR}"

if ! command -v executor >/dev/null 2>&1; then
  npm install -g executor
fi

EXECUTOR_BIN="$(resolve_executor_bin)" || {
  echo "unable to resolve executor binary after installation" >&2
  exit 1
}

cat >"/etc/systemd/system/${EXECUTOR_SERVICE_NAME}" <<EOF
[Unit]
Description=Executor sidecar local runtime
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=${EXECUTOR_STATE_DIR}
Environment=HOME=/root
ExecStart=${EXECUTOR_BIN} web
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now "${EXECUTOR_SERVICE_NAME}"

attempt=0
until curl -fsS "http://127.0.0.1:${EXECUTOR_PORT}/api/scope" >/dev/null 2>&1; do
  attempt=$((attempt + 1))
  if [ "${attempt}" -ge 20 ]; then
    systemctl status "${EXECUTOR_SERVICE_NAME}" --no-pager || true
    echo "executor sidecar did not become healthy on 127.0.0.1:${EXECUTOR_PORT}" >&2
    exit 1
  fi
  sleep 2
done

echo "executor sidecar is ready on http://127.0.0.1:${EXECUTOR_PORT}"
