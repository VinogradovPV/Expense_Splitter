#!/bin/bash
set -e

echo -e "\033[0;36mStarting Expense Splitter Installation...\033[0m"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "\033[0;31mError: Python 3 is not installed or not in PATH.\033[0m"
    exit 1
fi

PYTHON_VERSION=$(python3 --version)
echo "Found Python: $PYTHON_VERSION"

# Create virtual environment
VENV_PATH="$(dirname "$0")/../.venv"
if [ ! -d "$VENV_PATH" ]; then
    echo -e "\033[0;33mCreating virtual environment...\033[0m"
    python3 -m venv "$VENV_PATH"
else
    echo -e "\033[0;33mVirtual environment already exists.\033[0m"
fi

# Activate and install
echo -e "\033[0;33mInstalling dependencies...\033[0m"
source "$VENV_PATH/bin/activate"
python3 -m pip install --upgrade pip

PROJECT_ROOT="$(dirname "$0")/.."
if [ "$1" == "-Dev" ] || [ "$1" == "--dev" ]; then
    pip install -e "$PROJECT_ROOT[dev]"
else
    pip install -e "$PROJECT_ROOT"
fi

# Check installation
echo -e "\033[0;33mVerifying installation...\033[0m"
if ! expense-splitter --help > /dev/null; then
    echo -e "\033[0;31mError: Installation verification failed.\033[0m"
    exit 1
fi

echo ""
echo -e "\033[0;32mInstallation completed successfully!\033[0m"
echo "Run launcher:"
echo -e "\033[0;36m./scripts/run-launcher.sh\033[0m"
echo "Run CLI:"
echo -e "\033[0;36m./scripts/run-cli.sh --help\033[0m"
