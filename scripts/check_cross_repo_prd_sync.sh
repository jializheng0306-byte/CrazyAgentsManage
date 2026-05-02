#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CRAZY_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
FLOWMIND_ROOT="${FLOWMIND_ROOT:-${CRAZY_ROOT}/../FlowMindDeploy}"

python3 "${FLOWMIND_ROOT}/scripts/governance/check_cross_repo_prd_sync.py" \
  --source-repo-root "${FLOWMIND_ROOT}" \
  --counterpart-repo-root "${CRAZY_ROOT}" \
  "$@"
