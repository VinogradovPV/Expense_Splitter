# Pull Request for Installer, Launcher, and Documentation

This document outlines the changes made in the `feature/installer-readme-launcher` branch and serves as a template for a Pull Request.

## Branch: `feature/installer-readme-launcher`

## Summary of Changes

This branch introduces significant improvements to the Expense Splitter project, focusing on user experience, ease of installation, and comprehensive documentation. The core CLI functionality remains unchanged, ensuring backward compatibility.

Key changes include:

1.  **Installer Scripts**: Cross-platform installation scripts (`install.ps1`, `install.sh`) for Windows and Linux/macOS, simplifying the setup process for end-users. These scripts handle virtual environment creation and dependency installation.
2.  **Run Scripts**: Dedicated scripts (`run-launcher.ps1`, `run-cli.ps1`, `run-launcher.sh`, `run-cli.sh`) to easily launch the UX launcher or CLI without manual virtual environment activation.
3.  **Uninstaller Script**: A script (`uninstall.ps1`) to remove the virtual environment and optionally user data.
4.  **UX Launcher**: An interactive terminal-based launcher (`src/expense_splitter/launcher.py`) providing a user-friendly menu for common operations like adding purchases, viewing balances, and generating reports. A new entry point `expense-splitter-launcher` has been added to `pyproject.toml`.
5.  **Packaging Infrastructure**: PyInstaller specification (`packaging/expense_splitter.spec`) and build scripts (`build-windows.ps1`, `build-unix.sh`) to enable the creation of standalone executables for Windows and Linux. `pyinstaller` has been added to `dev` dependencies.
6.  **GitHub Actions Workflow**: A `build-release.yml` workflow to automate testing and building of release artifacts (executables) for Windows and Linux upon tagging a new release.
7.  **Comprehensive Documentation**: Expanded `README.md` and new dedicated documentation files in the `docs/` directory:
    *   `INSTALLATION.md`: Detailed installation instructions for various platforms and user types.
    *   `PACKAGING.md`: Guide for building standalone executables.
    *   `TROUBLESHOOTING.md`: Solutions to common issues.
8.  **Quality Checks**: All existing tests (20 tests) continue to pass, and new smoke tests for the launcher have been added and passed.

## Motivation

The primary motivation for these changes is to transform Expense Splitter from a developer-centric CLI tool into a more accessible and user-friendly application. By providing simplified installation, an intuitive launcher, and clear documentation, we aim to lower the barrier to entry for non-technical users and streamline the release process.

## How to Test

1.  **Checkout the branch**: `git checkout feature/installer-readme-launcher`
2.  **Install dependencies (developer mode)**: 
    ```bash
    python -m venv .venv
    source .venv/bin/activate
    pip install -e .[dev]
    ```
3.  **Run all tests**: `PYTHONPATH=src python3 -m pytest tests/ -v` (All 23 tests should pass).
4.  **Test Windows Installer (if on Windows)**: `.\scripts\install.ps1` then `.\scripts\run-launcher.ps1` and `.\scripts\run-cli.ps1 balances`.
5.  **Test Linux/macOS Installer (if on Linux/macOS)**: `./scripts/install.sh` then `./scripts/run-launcher.sh` and `./scripts/run-cli.sh balances`.
6.  **Interact with the UX Launcher**: Run `expense-splitter-launcher` (after developer install) or `.\scripts\run-launcher.ps1` / `./scripts/run-launcher.sh` and test all menu options.
7.  **Verify CLI commands**: Ensure all `expense-splitter` CLI commands (`init`, `add-purchase`, `list-purchases`, `balances`, `settle`, `report`) work as expected.
8.  **Review Documentation**: Check `README.md`, `docs/INSTALLATION.md`, `docs/PACKAGING.md`, and `docs/TROUBLESHOOTING.md` for clarity and accuracy.

## Files Changed

- `.github/workflows/build-release.yml`
- `docs/INSTALLATION.md`
- `docs/PACKAGING.md`
- `docs/PULL_REQUEST_INSTALLER.md`
- `docs/TROUBLESHOOTING.md`
- `packaging/expense_splitter.spec`
- `pyproject.toml`
- `scripts/build-unix.sh`
- `scripts/build-windows.ps1`
- `scripts/install.sh`
- `scripts/install.ps1`
- `scripts/run-cli.sh`
- `scripts/run-cli.ps1`
- `scripts/run-launcher.sh`
- `scripts/run-launcher.ps1`
- `scripts/uninstall.ps1`
- `src/expense_splitter/launcher.py`
- `tests/test_launcher.py`
- `README.md` (will be updated in the next step)

## Next Steps

Upon approval and merge, this branch will be merged into `main`, and a new release tag (`vX.Y.Z`) can be created to trigger the GitHub Actions release workflow.
