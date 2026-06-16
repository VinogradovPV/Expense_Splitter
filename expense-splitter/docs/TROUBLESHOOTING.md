# Troubleshooting Expense Splitter

This document provides solutions to common issues you might encounter while using or installing Expense Splitter.

## 1. Installation Issues

### 1.1. Python not found

**Problem:** When running `install.ps1` or `install.sh`, you get an error like "Python is not installed or not in PATH."

**Solution:** Ensure Python 3.11 or newer is installed on your system and added to your system's PATH environment variable. You can download Python from [python.org](https://www.python.org/downloads/). After installation, restart your terminal.

### 1.2. Virtual environment activation fails

**Problem:** The `activate` script for the virtual environment doesn't work.

**Solution:**
- **Windows:** Ensure your PowerShell execution policy allows running local scripts. You might need to run `Set-ExecutionPolicy RemoteSigned -Scope CurrentUser` in an administrator PowerShell session. After activation, you can revert the policy if needed.
- **Linux/macOS:** Ensure the `source` command is used correctly: `source ./.venv/bin/activate`.

### 1.3. `pip install -e .` fails

**Problem:** Dependencies fail to install or the project doesn't install in editable mode.

**Solution:**
- Check your internet connection.
- Ensure `pip` is up to date: `python -m pip install --upgrade pip`.
- If you're on Windows and encounter path length issues, try moving the project to a shorter path (e.g., `C:\ES`).
- Check the error message for specific dependency failures and try installing them manually.

## 2. Application Usage Issues

### 2.1. `expense-splitter` command not found

**Problem:** After installation, running `expense-splitter` or `expense-splitter-launcher` results in a "command not found" error.

**Solution:**
- **If using scripts:** Ensure you are running the commands via `scripts/run-cli.ps1` (Windows) or `scripts/run-cli.sh` (Linux/macOS), or that your virtual environment is activated if you installed in developer mode.
- **If in developer mode:** Make sure your virtual environment is activated (`source ./.venv/bin/activate` or `.\.venv\Scripts\Activate.ps1`).
- **Re-run installer:** Sometimes re-running the `install.ps1` or `install.sh` script can resolve path issues.

### 2.2. Data files not found or corrupted

**Problem:** The application reports errors related to `participants.yaml` or `purchases.yaml`.

**Solution:**
- **Run `init` command:** If data files are missing, run `expense-splitter init --with-examples` to create default files.
- **Check file integrity:** Open `data/participants.yaml` and `data/purchases.yaml` in a text editor to ensure they are valid YAML. Incorrect formatting can cause issues.
- **Backup and restore:** If data is corrupted, try restoring from a backup if you have one. Otherwise, you might need to re-initialize data.

### 2.3. Incorrect calculations

**Problem:** Balances or settlements seem incorrect.

**Solution:**
- **Verify input data:** Double-check the amounts, payers, and participants for each purchase in `data/purchases.yaml`.
- **Check for rounding issues:** Expense Splitter uses `Decimal` for precise calculations, but small discrepancies can occur due to floating-point arithmetic if you manually entered values from other sources. Ensure all amounts are entered correctly.
- **Report a bug:** If you suspect a calculation error, please report it to the developers with detailed steps to reproduce.

## 3. Development Issues

### 3.1. `pytest` or `ruff` not found

**Problem:** When running `pytest` or `ruff`, you get a "command not found" error.

**Solution:** Ensure you have installed the development dependencies. If you used `install.ps1 -Dev` or `install.sh --dev`, these should be available. Otherwise, activate your virtual environment and run `pip install -e .[dev]`.

### 3.2. PyInstaller build fails

**Problem:** The `build-windows.ps1` or `build-unix.sh` script fails during the PyInstaller step.

**Solution:**
- Ensure `pyinstaller` is installed in your virtual environment (`pip install pyinstaller`).
- Check the PyInstaller output for specific error messages. Common issues include missing `hiddenimports` or `datas` entries in `packaging/expense_splitter.spec`.
- Try building without UPX compression by adding `--noupx` to the build command (e.g., `.\scripts\build-windows.ps1 --noupx`).

## 4. Getting Help

If you encounter an issue not covered here, or if the solutions provided do not resolve your problem, please:

1.  **Check the GitHub Issues**: Someone else might have already reported a similar issue.
2.  **Open a new issue**: Provide a detailed description of the problem, steps to reproduce it, your operating system, Python version, and any relevant error messages. Attach your `REPORT.md` if it contains useful information.
