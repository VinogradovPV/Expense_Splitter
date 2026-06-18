#!/bin/bash
set -e

echo -e "\033[0;36mStarting Expense Splitter Unix Build...\033[0m"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
VENV_PATH="$PROJECT_ROOT/.venv"
PACKAGING_DIR="$PROJECT_ROOT/packaging"
SPEC_FILE="$PACKAGING_DIR/expense_splitter.spec"
BUILD_DIR="$PROJECT_ROOT/build"
DIST_DIR="$PROJECT_ROOT/dist"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "\033[0;31mError: Python 3 is not installed or not in PATH.\033[0m"
    exit 1
fi

# Create virtual environment if not exists
if [ ! -d "$VENV_PATH" ]; then
    echo -e "\033[0;33mCreating virtual environment...\033[0m"
    python3 -m venv "$VENV_PATH"
fi

# Activate and install build dependencies
source "$VENV_PATH/bin/activate"
echo -e "\033[0;33mInstalling build dependencies...\033[0m"
python -m pip install --upgrade pip
python -m pip install -e "$PROJECT_ROOT[dev]"

echo -e "\033[0;33mRunning PyInstaller...\033[0m"
cd "$PROJECT_ROOT"

PYINSTALLER_ARGS=(
    "--clean"
    "--workpath" "$BUILD_DIR"
    "--distpath" "$DIST_DIR"
)
if [ "$1" == "--noupx" ]; then
    export PYINSTALLER_NO_UPX=1
else
    unset PYINSTALLER_NO_UPX
fi
PYINSTALLER_ARGS+=("$SPEC_FILE")

if ! python -m PyInstaller "${PYINSTALLER_ARGS[@]}"; then
    echo -e "\033[0;31mError: PyInstaller build failed.\033[0m"
    exit 1
fi

echo ""
echo -e "\033[0;32mBuild completed successfully!\033[0m"
echo -e "\033[0;32mExecutables are in the 'dist' folder:\033[0m"
ls -F "$DIST_DIR"
