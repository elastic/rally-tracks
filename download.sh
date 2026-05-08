#!/usr/bin/env bash
# This script is a compatibility wrapper. The implementation lives in download.py.
exec python3 "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/download.py" "$@"
