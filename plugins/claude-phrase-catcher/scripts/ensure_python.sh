#!/usr/bin/env bash

PYTHON_BIN=""
LOG_FILE="${CLAUDE_PLUGIN_ROOT}/scripts/Logs/ensure_python.log"

# ensure Logs dir exists
mkdir -p "${CLAUDE_PLUGIN_ROOT}/scripts/Logs"

echo "=== ensure_python.sh started $(date) ===" > "$LOG_FILE"
echo "CLAUDE_PLUGIN_ROOT: ${CLAUDE_PLUGIN_ROOT}" >> "$LOG_FILE"

OS="$(uname -s)"
echo "OS: $OS" >> "$LOG_FILE"

if [[ "$OS" == MINGW* || "$OS" == CYGWIN* || "$OS" == MSYS* ]]; then
    if command -v python3 &> /dev/null; then
        PYTHON_BIN="python3"
    elif command -v python &> /dev/null; then
        PYTHON_BIN="python"
    fi
else
    echo "Searching for python3 binaries..." >> "$LOG_FILE"

    while IFS= read -r candidate; do
        echo "Testing: $candidate" >> "$LOG_FILE"
        if "$candidate" -c "import tkinter" &> /dev/null 2>&1; then
            echo "tkinter OK: $candidate" >> "$LOG_FILE"
            PYTHON_BIN="$candidate"
            break
        else
            echo "tkinter FAILED: $candidate" >> "$LOG_FILE"
        fi
    done < <(find /usr /usr/local /opt /home ~/.local -name "python3*" -type f -executable 2>/dev/null | sort)
fi

if [ -z "$PYTHON_BIN" ]; then
    echo "ERROR: no Python 3 with tkinter found" >> "$LOG_FILE"
    echo "⚠️  claude-phrase-catcher: no Python 3 with tkinter found."
    if [[ "$OS" == MINGW* || "$OS" == CYGWIN* || "$OS" == MSYS* ]]; then
        echo "Install Python from https://www.python.org/downloads/"
    else
        echo "On Ubuntu/Debian run: sudo apt install python3-tk"
    fi
    exit 0
fi

echo "Selected Python: $PYTHON_BIN" >> "$LOG_FILE"
echo "$PYTHON_BIN" > "${CLAUDE_PLUGIN_ROOT}/scripts/.python_bin"
echo "Written to .python_bin successfully" >> "$LOG_FILE"

"$PYTHON_BIN" "${CLAUDE_PLUGIN_ROOT}/scripts/ensure_deps.py"