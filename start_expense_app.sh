#!/bin/bash
# Automatically identify the project directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    streamlit run app.py --server.headless true
else
    echo "Virtual environment not found. Please ensure 'venv' exists in $SCRIPT_DIR"
    exit 1
fi
