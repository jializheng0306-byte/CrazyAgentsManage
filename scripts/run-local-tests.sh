#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_PYTHON="${ROOT_DIR}/.venv/bin/python"

if [[ ! -x "${VENV_PYTHON}" ]]; then
  echo "Missing ${VENV_PYTHON}. Run scripts/setup-local-test-env.sh first." >&2
  exit 1
fi

cd "${ROOT_DIR}"
if [[ "$#" -gt 0 ]]; then
  TARGETS=("$@")
else
  TARGETS=(tests/test_sprint2.py tests/test_sprint3.py tests/test_sprint4.py)
fi

"${VENV_PYTHON}" -m pytest "${TARGETS[@]}" -q
