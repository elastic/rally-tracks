#!/usr/bin/env bash
set -euo pipefail
# This script is a compatibility wrapper. The implementation lives in download.py.

if command -v python3 &>/dev/null; then
    PYTHON=python3
elif command -v python &>/dev/null; then
    PYTHON=python
else
    echo "error: Python 3 is required but neither 'python3' nor 'python' was found on PATH." >&2
    exit 1
fi

exec "$PYTHON" "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/download.py" "$@"
