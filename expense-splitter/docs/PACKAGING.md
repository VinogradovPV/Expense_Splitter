# Packaging Expense Splitter

This document describes how to build standalone executables for the Expense Splitter application using PyInstaller.

## Requirements

- Python 3.11+
- `pip`
- `PyInstaller`

## Setup

First, ensure you have PyInstaller installed in your development environment:

```bash
pip install pyinstaller
```

## Building for Windows

To build the `.exe` files for Windows, navigate to the project root and run the `build-windows.ps1` script:

```powershell
.\scripts\build-windows.ps1
```

This script will:
1. Install necessary build dependencies.
2. Run PyInstaller using the `expense_splitter.spec` file.
3. Place the generated executables (`expense-splitter.exe` and `expense-splitter-launcher.exe`) in the `dist/` directory.

## Building for Linux/macOS

To build the executables for Linux or macOS, navigate to the project root and run the `build-unix.sh` script:

```bash
./scripts/build-unix.sh
```

This script will:
1. Install necessary build dependencies.
2. Run PyInstaller using the `expense_splitter.spec` file.
3. Place the generated executables (`expense-splitter` and `expense-splitter-launcher`) in the `dist/` directory.

## PyInstaller Spec File (`packaging/expense_splitter.spec`)

The `.spec` file defines how PyInstaller should bundle the application. It includes:
- **Analysis**: Specifies the main script(s) and includes necessary data files (e.g., `data/` directory, Python modules).
- **EXE**: Configures the executable properties, such as name, console mode, and UPX compression.

This setup generates two executables:
- `expense-splitter`: The command-line interface (CLI) application.
- `expense-splitter-launcher`: The interactive UX launcher.

## Troubleshooting

- **Missing modules**: If PyInstaller fails due to missing modules, you might need to add them to the `hiddenimports` list in the `.spec` file.
- **Data files not found**: Ensure that the `datas` array in the `.spec` file correctly points to all necessary non-Python files (like `data/` directory).
