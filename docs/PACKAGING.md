# Упаковка Expense Splitter

## Требования

- Python 3.11+;
- dev-зависимости `python -m pip install -e ".[dev]"`;
- PyInstaller из проектной `.venv`.

Пользовательская папка `data/` не встраивается в executables: приложение читает и создаёт данные в
runtime-рабочей директории.

## Windows

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\build-windows.ps1 -NoUpx
```

Скрипт использует `packaging/expense_splitter.spec`, создаёт `.venv` при необходимости, устанавливает
dev-зависимости и пишет generated output в `build/` и `dist/`.

Ожидаемые файлы:

```text
dist/expense-splitter.exe
dist/expense-splitter-launcher.exe
dist/expense-splitter-gui.exe
```

`expense-splitter-gui.exe` собирается с `console=False`; CLI и console launcher сохраняют консоль.

```powershell
.\dist\expense-splitter.exe --help
.\dist\expense-splitter-launcher.exe --help
.\dist\expense-splitter-gui.exe --help
```

## Linux/macOS

```bash
./scripts/build-unix.sh
./scripts/build-unix.sh --noupx
```

Spec создаёт CLI, launcher и GUI targets для текущей платформы. Tkinter должен присутствовать в
системной поставке Python.

## GitHub Actions

`.github/workflows/ci.yml` запускает quality checks на push/PR. `.github/workflows/build-release.yml`
собирает release artifacts по настроенным branch/tag triggers; перед релизом проверьте актуальные
условия непосредственно в workflow и выполните P2.REL.1.

## Generated artifacts

`build/` и `dist/` игнорируются Git. Не добавляйте exe, PyInstaller work files, caches и локальные
reports в обычный source commit.
