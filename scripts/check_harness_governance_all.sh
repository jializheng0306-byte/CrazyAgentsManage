#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

RUN_LOCAL=1
RUN_CROSS_REPO=1

for arg in "$@"; do
  case "$arg" in
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
  echo "[governance:all] local harness consistency"
  python3 "${SCRIPT_DIR}/check_harness_governance_consistency.py"
  echo "[governance:all] closeout chain consistency"
  python3 "${SCRIPT_DIR}/check_harness_closeout_chain.py"
fi

if [[ "$RUN_CROSS_REPO" -eq 1 ]]; then
  echo "[governance:all] cross-repo PRD sync"
  "${SCRIPT_DIR}/check_cross_repo_prd_sync.sh"
fi

echo "[governance:all] all checks passed"
