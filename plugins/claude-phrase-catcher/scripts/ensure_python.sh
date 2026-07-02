#!/usr/bin/env bash

PYTHON_BIN=""

OS="$(uname -s)"

if [[ "$OS" == MINGW* || "$OS" == CYGWIN* || "$OS" == MSYS* ]]; then
    # Windows - python3 or python is reliable here, no need to search
    if command -v python3 &> /dev/null; then
        PYTHON_BIN="python3"
    elif command -v python &> /dev/null; then
        PYTHON_BIN="python"
    fi
else
    # Linux/Mac - search common install locations for a python3 with tkinter
    while IFS= read -r candidate; do
        if "$candidate" -c "import tkinter" &> /dev/null 2>&1; then
            PYTHON_BIN="$candidate"
            break
        fi
    done < <(find /usr /usr/local /opt /home ~/.local -name "python3*" -type f -executable 2>/dev/null | sort)
fi

if [ -z "$PYTHON_BIN" ]; then
    echo "⚠️  claude-phrase-catcher: no Python 3 with tkinter found."
    if [[ "$OS" == MINGW* || "$OS" == CYGWIN* || "$OS" == MSYS* ]]; then
        echo "Install Python from https://www.python.org/downloads/"
    else
        echo "On Ubuntu/Debian run: sudo apt install python3-tk"
    fi
    exit 0
fi

# save the working python path for show_frame.py to use
echo "$PYTHON_BIN" > "${CLAUDE_PLUGIN_ROOT}/scripts/.python_bin"

"$PYTHON_BIN" "${CLAUDE_PLUGIN_ROOT}/scripts/ensure_deps.py"