#!/usr/bin/env bash
set -e

# Auto-locate project directory regardless of where user runs it from
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

# Ensure venv exists
if [ ! -f "$DIR/.venv/bin/python" ]; then
    echo "⚡ Initializing virtual environment..."
    python3 -m venv "$DIR/.venv"
    "$DIR/.venv/bin/pip" install -r "$DIR/requirements.txt"
fi

export PYTHONPATH="$DIR"

# If no arguments provided, run demo
if [ $# -eq 0 ]; then
    exec "$DIR/.venv/bin/python" -m nexus.cli demo
else
    exec "$DIR/.venv/bin/python" -m nexus.cli "$@"
fi
