# Troubleshooting Expense Splitter

## 0. GUI launcher

### 0.1. `run-gui.ps1` does not start because the script is not signed

**Problem:** PowerShell shows `PSSecurityException`, `UnauthorizedAccess`, or says that
`scripts\run-gui.ps1` does not have a digital signature.

**Solution:** Start the GUI through a one-time process policy bypass:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\run-gui.ps1
```

This does not change the system-wide execution policy.

### 0.2. GUI opens, but data is empty

Run initialization from CLI or use the existing installer flow:

```powershell
expense-splitter init --with-examples
```

The GUI also creates empty default YAML files when `data/` is missing.

### 0.3. GUI reports an error dialog

User-facing GUI errors are shown through dialogs without traceback. Check YAML files in `data/`
and the `.bak` copies if a data file was edited manually.

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
- **Read the file path in the error:** If the CLI prints `Data error in <path>`, the message includes the exact YAML file that could not be read.
- **Use automatic `.bak` copies:** Before replacing an existing YAML file, Expense Splitter creates a timestamped `.bak` copy next to the original file. If a recent edit breaks the data file, compare it with the newest `.bak` file and restore the last known-good content manually.
- **Backup and restore:** If data is corrupted and no usable `.bak` file exists, restore from your own backup if you have one. Otherwise, you might need to re-initialize data.

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

## 5. Analytics Reports

### 5.1. Mojibake in PowerShell or CSV

**Problem:** Russian text looks like unreadable replacement symbols or mixed Latin/Cyrillic noise.

**Solution:**
- Prefer opening CSV files from `reports/analytics/<year>/<period-id>/tables/` in Excel; they are written as `utf-8-sig`.
- In PowerShell, switch the console to UTF-8 before running checks:

```powershell
chcp 65001
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$OutputEncoding = [System.Text.UTF8Encoding]::new($false)
```

### 5.2. No PNG charts were created

**Problem:** `charts/` is empty after running analytics.

**Solution:** Check `tables/warnings.csv`. If the period has no purchases, Expense Splitter writes `chart_no_data` warnings instead of creating empty charts.

### 5.3. Removing generated analytics reports

Generated analytics reports are not source files. To remove them locally:

```powershell
Remove-Item -Recurse -Force reports\analytics
```

Do not delete `data/participants.yaml` or `data/purchases.yaml` unless you intentionally want to remove user data.

### 5.4. Сброс тестовых данных не запускается

GUI принимает только точную строку `RESET_TEST_DATA`. Перед очисткой должны быть доступны для
записи `data/purchases.yaml` и `data/settlement_periods.yaml`; рядом с ними создаются timestamped
`.bak`. Не удаляйте backups до проверки результата. Справочники `participants/groups/categories`
reset-test не очищает.

Если требуется лишь начать новый текущий расчет, используйте закрытие периода, а не reset-test:
закрытие сохраняет покупки в истории.

### 5.5. Новая категория или участник не сохраняется

Новая категория попадает в `data/categories.yaml` только после подтверждения в GUI. Неизвестные
участники не создаются из ручного поля автоматически: исправьте имя либо сначала добавьте
участника в справочник. Регистр известных имён нормализуется к значению из справочника.

Файлы `*.bak`, `.pytest_cache/`, `.ruff_cache/`, `dist/`, `build/`, `reports/` и `*.egg-info/`
являются generated artifacts и не должны добавляться в Git.

### 5.6. HTML не открывается или график отсутствует

Сначала создайте отчёт с `--format html` либо `--format all`. Открывайте
`analytics_dashboard.html` вместе с соседними папками `tables/` и `charts/`: ссылки относительные.
Отсутствующий PNG при пустом периоде не является ошибкой — HTML показывает сообщение об отсутствии
данных. Отчёт не выполняет сетевых запросов и работает offline.

### 5.7. XLSX не открывается или кнопка недоступна

Сначала создайте отчёт с `--format xlsx` либо `--format all`. GUI ищет файл
`expense_analytics_<period-id>.xlsx` в последней созданной папке отчёта. Для просмотра нужно
XLSX-совместимое приложение, но генерация не требует Microsoft Excel. При повреждении файла
повторите генерацию; generated `reports/` можно безопасно пересоздать.

If you encounter an issue not covered here, or if the solutions provided do not resolve your problem, please:

1.  **Check the GitHub Issues**: Someone else might have already reported a similar issue.
2.  **Open a new issue**: Provide a detailed description of the problem, steps to reproduce it, your operating system, Python version, and any relevant error messages. Attach your `REPORT.md` if it contains useful information.
