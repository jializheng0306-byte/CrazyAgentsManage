#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CRAZY_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

RUN_LOCAL=1
RUN_CROSS_REPO=0

for arg in "$@"; do
  case "$arg" in
    --with-cross-repo)
      RUN_CROSS_REPO=1
      ;;
    --local-only)
      RUN_CROSS_REPO=0
      ;;
    --skip-local)
      RUN_LOCAL=0
      ;;
    --skip-cross-repo)
      RUN_CROSS_REPO=0
      ;;
    *)
      ;;
  esac
done

if [[ "$RUN_LOCAL" -eq 1 ]]; then
  echo "[governance] local harness consistency"
  python3 "${SCRIPT_DIR}/check_harness_governance_consistency.py"
fi

if [[ "$RUN_CROSS_REPO" -eq 1 ]]; then
  FLOWMIND_ROOT="${FLOWMIND_ROOT:-${CRAZY_ROOT}/../FlowMindDeploy}"
  SYNC_SCRIPT="${FLOWMIND_ROOT}/scripts/governance/check_cross_repo_prd_sync.py"
  if [[ ! -f "$SYNC_SCRIPT" ]]; then
    echo "[governance] missing cross-repo sync checker: ${SYNC_SCRIPT}" >&2
    exit 1
  fi
  echo "[governance] cross-repo PRD sync"
  "${SCRIPT_DIR}/check_cross_repo_prd_sync.sh"
fi

echo "[governance] checks passed"
