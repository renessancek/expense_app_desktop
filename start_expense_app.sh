#!/bin/bash

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
    python desktop_launcher.py
elif [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    python desktop_launcher.py
else
    echo "Virtual environment not found. Please ensure '.venv' or 'venv' exists in $SCRIPT_DIR"
    exit 1
fi
