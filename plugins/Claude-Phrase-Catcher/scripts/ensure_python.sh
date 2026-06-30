#!/usr/bin/env bash

PYTHON_BIN=""

if command -v python3 &> /dev/null; then
    PYTHON_BIN="python3"
elif command -v python &> /dev/null; then
    PYTHON_BIN="python"
fi

if [ -z "$PYTHON_BIN" ]; then
    echo "⚠️  claude-phrase-catcher requires Python 3, but it was not found on this system."
    echo "Install it from https://www.python.org/downloads/ and restart Claude Code."
    exit 0
fi

"$PYTHON_BIN" "${CLAUDE_PLUGIN_ROOT}/scripts/ensure_deps.py"