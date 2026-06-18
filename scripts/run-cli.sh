#!/bin/bash
set -e

VENV_PATH="$(dirname "$0")/../.venv"

if [ ! -f "$VENV_PATH/bin/activate" ]; then
    echo -e "\033[0;31mVirtual environment not found. Please run install.sh first.\033[0m"
    exit 1
fi

source "$VENV_PATH/bin/activate"
expense-splitter "$@"
