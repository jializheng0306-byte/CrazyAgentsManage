#!/usr/bin/env bash
# Compatibility wrapper for legacy operator/skill entrypoints.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec /usr/bin/python3 "${SCRIPT_DIR}/evening-trend-analysis.py" "$@"
