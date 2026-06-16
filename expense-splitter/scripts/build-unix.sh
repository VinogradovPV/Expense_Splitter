#!/bin/bash
set -e

echo -e "\033[0;36mStarting Expense Splitter Unix Build...\033[0m"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "\033[0;31mError: Python 3 is not installed or not in PATH.\033[0m"
    exit 1
fi

# Create virtual environment if not exists
VENV_PATH="$(dirname "$0")/../.venv"
if [ ! -d "$VENV_PATH" ]; then
    echo -e "\033[0;33mCreating virtual environment...\033[0m"
    python3 -m venv "$VENV_PATH"
fi

# Activate and install build dependencies
source "$VENV_PATH/bin/activate"
echo -e "\033[0;33mInstalling build dependencies...\033[0m"
python3 -m pip install --upgrade pip
pip install pyinstaller

# Run PyInstaller
PROJECT_ROOT="$(dirname "$0")/.."
PACKAGING_DIR="$PROJECT_ROOT/packaging"
SPEC_FILE="$PACKAGING_DIR/expense_splitter.spec"

echo -e "\033[0;33mRunning PyInstaller...\033[0m"
cd "$PACKAGING_DIR"

PYINSTALLER_COMMAND="pyinstaller --clean --workpath build --distpath dist --specpath ."
if [ "$1" == "--noupx" ]; then
    PYINSTALLER_COMMAND+=" --noupx"
fi
PYINSTALLER_COMMAND+=" $SPEC_FILE"

$PYINSTALLER_COMMAND

if [ $? -ne 0 ]; then
    echo -e "\033[0;31mError: PyInstaller build failed.\033[0m"
    exit 1
fi

cd "$PROJECT_ROOT"

echo ""
echo -e "\033[0;32mBuild completed successfully!\033[0m"
echo -e "\033[0;32mExecutables are in the 'dist' folder:\033[0m"
ls -F "$PROJECT_ROOT/dist"
