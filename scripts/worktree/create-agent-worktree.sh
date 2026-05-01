#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  scripts/worktree/create-agent-worktree.sh --agent <name> --lane <codex|ops|shared|docs|hotfix|release> --topic <topic> [--base <branch>] [--branch <branch>] [--parent <dir>]

Examples:
  scripts/worktree/create-agent-worktree.sh --agent codex --lane codex --topic runtime-alignment
  scripts/worktree/create-agent-worktree.sh --agent claude --lane shared --topic harness-review --base main
  scripts/worktree/create-agent-worktree.sh --agent codebuddy --lane docs --topic page-prd-pass --branch docs/page-prd-pass
EOF
}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

AGENT=""
LANE=""
TOPIC=""
BASE_BRANCH="main"
TARGET_BRANCH=""
PARENT_DIR="$(dirname "${REPO_ROOT}")"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --agent)
      AGENT="${2:-}"
      shift 2
      ;;
    --lane)
      LANE="${2:-}"
      shift 2
      ;;
    --topic)
      TOPIC="${2:-}"
      shift 2
      ;;
    --base)
      BASE_BRANCH="${2:-}"
      shift 2
      ;;
    --branch)
      TARGET_BRANCH="${2:-}"
      shift 2
      ;;
    --parent)
      PARENT_DIR="${2:-}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

if [[ -z "${AGENT}" || -z "${LANE}" || -z "${TOPIC}" ]]; then
  echo "Missing required arguments." >&2
  usage >&2
  exit 1
fi

case "${LANE}" in
  codex|ops|shared|docs|hotfix|release)
    ;;
  *)
    echo "Unsupported lane: ${LANE}" >&2
    exit 1
    ;;
esac

sanitize() {
  printf '%s' "$1" | tr '[:upper:]' '[:lower:]' | sed -E 's#[^a-z0-9._/-]+#-#g; s#/#-#g; s#-+#-#g; s#(^-|-$)##g'
}

AGENT_SAFE="$(sanitize "${AGENT}")"
TOPIC_SAFE="$(sanitize "${TOPIC}")"
REPO_NAME="$(basename "${REPO_ROOT}")"

if [[ -z "${TARGET_BRANCH}" ]]; then
  TARGET_BRANCH="${LANE}/${TOPIC_SAFE}"
fi

WORKTREE_NAME="${REPO_NAME}-${AGENT_SAFE}-${LANE}-${TOPIC_SAFE}"
WORKTREE_PATH="${PARENT_DIR}/${WORKTREE_NAME}"

echo "[worktree] repo=${REPO_ROOT}"
echo "[worktree] branch=${TARGET_BRANCH}"
echo "[worktree] base=${BASE_BRANCH}"
echo "[worktree] path=${WORKTREE_PATH}"

if [[ -e "${WORKTREE_PATH}" ]]; then
  echo "Target path already exists: ${WORKTREE_PATH}" >&2
  exit 1
fi

cd "${REPO_ROOT}"

git rev-parse --git-dir >/dev/null

if git show-ref --verify --quiet "refs/heads/${TARGET_BRANCH}"; then
  git worktree add "${WORKTREE_PATH}" "${TARGET_BRANCH}"
else
  git show-ref --verify --quiet "refs/heads/${BASE_BRANCH}" || {
    echo "Base branch not found locally: ${BASE_BRANCH}" >&2
    exit 1
  }
  git worktree add -b "${TARGET_BRANCH}" "${WORKTREE_PATH}" "${BASE_BRANCH}"
fi

cat <<EOF

[worktree] created successfully

Next steps:
1. cd ${WORKTREE_PATH}
2. Use the agent-specific adapter entry:
   - Codex / OMX: AGENTS.md
   - Other agents: use the repository adapter entry, then continue into docs/02-engineering/harness/HARNESS-ENTRY.md
3. Keep this worktree private to the assigned agent/runtime.
4. Write shared conclusions back to tracked artifacts only.

EOF
