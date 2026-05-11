#!/usr/bin/env bash
set -euo pipefail
# This script is a compatibility wrapper. The implementation lives in download.py.

MIN_PYTHON_MINOR=10  # requires 3.10+

_pick_python() {
    for candidate in python3 python; do
        if command -v "$candidate" &>/dev/null; then
            # Verify it is Python 3.10+
            if "$candidate" - <<'EOF' 2>/dev/null
import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)
EOF
            then
                echo "$candidate"
                return 0
            fi
        fi
    done
    return 1
}

if ! PYTHON="$(_pick_python)"; then
    echo "error: Python 3.${MIN_PYTHON_MINOR}+ is required but was not found on PATH." >&2
    echo "       Install it from https://www.python.org/downloads/ and re-run this script." >&2
    exit 1
fi

exec "$PYTHON" "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/download.py" "$@"
