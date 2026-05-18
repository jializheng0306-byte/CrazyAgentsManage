#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="${ROOT_DIR}/.venv"

if command -v uv >/dev/null 2>&1; then
  if [[ ! -d "${VENV_DIR}" ]]; then
    uv venv --python python3 "${VENV_DIR}"
  fi
  uv pip install --python "${VENV_DIR}/bin/python" -r "${ROOT_DIR}/requirements-dev.txt"
else
  if [[ ! -d "${VENV_DIR}" ]]; then
    python3 -m venv "${VENV_DIR}"
  fi
  "${VENV_DIR}/bin/python" -m ensurepip --upgrade
  "${VENV_DIR}/bin/python" -m pip install --upgrade pip
  "${VENV_DIR}/bin/python" -m pip install -r "${ROOT_DIR}/requirements-dev.txt"
fi

printf 'Local test environment ready: %s\n' "${VENV_DIR}"
printf 'Activate with: source %s/bin/activate\n' "${VENV_DIR}"
