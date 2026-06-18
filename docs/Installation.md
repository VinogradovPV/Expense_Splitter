# Installation Guide for Expense Splitter

This document provides detailed instructions on how to install and set up the Expense Splitter application on various operating systems.

## 1. Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.11 or newer**: Expense Splitter is built with Python. You can download it from [python.org](https://www.python.org/downloads/).

## 2. Installation on Windows (using PowerShell scripts)

This is the recommended method for most Windows users.

1.  **Download the project**: Download the latest release from the [GitHub Releases page](https://github.com/YOUR_GITHUB_USERNAME/expense-splitter/releases) (replace `YOUR_GITHUB_USERNAME` with the actual username).
2.  **Extract the archive**: Unzip the downloaded file to a location of your choice (e.g., `C:\ExpenseSplitter`).
3.  **Open PowerShell**: Navigate to the extracted folder in PowerShell.
    ```powershell
    cd C:\ExpenseSplitter
    ```
4.  **Run the installer script**: Execute the `install.ps1` script. This will create a virtual environment and install all necessary dependencies.
    ```powershell
    .\scripts\install.ps1
    ```
    If you want to install development dependencies (e.g., for running tests), use:
    ```powershell
    .\scripts\install.ps1 -Dev
    ```
5.  **Verify installation**: After installation, you should see a success message and instructions on how to run the launcher and CLI.

## 3. Installation on Linux/macOS (using Bash scripts)

This is the recommended method for most Linux and macOS users.

1.  **Download the project**: Download the latest release from the [GitHub Releases page](https://github.com/YOUR_GITHUB_USERNAME/expense-splitter/releases) (replace `YOUR_GITHUB_USERNAME` with the actual username).
2.  **Extract the archive**: Unzip the downloaded file to a location of your choice (e.g., `~/ExpenseSplitter`).
3.  **Open Terminal**: Navigate to the extracted folder in your terminal.
    ```bash
    cd ~/ExpenseSplitter
    ```
4.  **Run the installer script**: Execute the `install.sh` script. This will create a virtual environment and install all necessary dependencies.
    ```bash
    ./scripts/install.sh
    ```
    If you want to install development dependencies (e.g., for running tests), use:
    ```bash
    ./scripts/install.sh --dev
    ```
5.  **Verify installation**: After installation, you should see a success message and instructions on how to run the launcher and CLI.

## 4. Developer Installation (using pip/uv)

This method is suitable for developers who want to contribute to the project or need more control over the environment.

1.  **Clone the repository**: 
    ```bash
    git clone https://github.com/YOUR_GITHUB_USERNAME/expense-splitter.git
    cd expense-splitter
    ```
2.  **Create a virtual environment**: 
    ```bash
    python -m venv .venv
    ```
3.  **Activate the virtual environment**: 
    - On Windows:
      ```powershell
      .\.venv\Scripts\Activate.ps1
      ```
    - On Linux/macOS:
      ```bash
      source ./.venv/bin/activate
      ```
4.  **Install the project in editable mode**: 
    ```bash
    pip install --upgrade pip
    pip install -e .[dev]
    ```
    This installs the project and its development dependencies, allowing you to make changes to the code directly.

## 5. Running the Application

After installation, you can run the application using either the UX Launcher or the Command-Line Interface (CLI).

### 5.1. UX Launcher

- On Windows:
  ```powershell
  .\scripts\run-launcher.ps1
  ```
- On Linux/macOS:
  ```bash
  ./scripts/run-launcher.sh
  ```

### 5.2. Command-Line Interface (CLI)

- On Windows:
  ```powershell
  .\scripts\run-cli.ps1 --help
  ```
- On Linux/macOS:
  ```bash
  ./scripts/run-cli.sh --help
  ```

Alternatively, if you installed in developer mode and activated the virtual environment, you can directly use:

```bash
expense-splitter --help
expense-splitter-launcher
```

## 6. Uninstallation

To uninstall the application:

- On Windows:
  ```powershell
  .\scripts\uninstall.ps1
  ```
- On Linux/macOS:
  ```bash
  ./scripts/uninstall.sh
  ```

To also remove user data (purchases, participants) during uninstallation, use the `-RemoveData` (Windows) or `--remove-data` (Linux/macOS) flag:

- On Windows:
  ```powershell
  .\scripts\uninstall.ps1 -RemoveData
  ```
- On Linux/macOS:
  ```bash
  ./scripts/uninstall.sh --remove-data
  ```

**Note**: User data is located in the `data/` directory within the project folder. Reports are in `reports/`.
