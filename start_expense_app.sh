#!/bin/bash
set -e
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"
if [ -x ".venv/bin/python" ]; then
    .venv/bin/python desktop_app.py
elif [ -x "venv/bin/python" ]; then
    venv/bin/python desktop_app.py
else
    echo "Virtual environment not found."
    exit 1
fi
