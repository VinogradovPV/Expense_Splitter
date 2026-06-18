# Packaging Expense Splitter

Документ описывает сборку standalone-исполняемых файлов Expense Splitter через
PyInstaller.

## Требования

- Python 3.11 или новее.
- `pip`.
- Установленные dev-зависимости проекта: `python -m pip install -e ".[dev]"`.

Скрипты сборки создают или используют локальное окружение `.venv` и ставят
проект в editable-режиме с dev-зависимостями.

## Структура

Целевая структура P0:

```text
.
├── pyproject.toml
├── src/expense_splitter/
├── packaging/expense_splitter.spec
├── scripts/build-windows.ps1
├── scripts/build-unix.sh
├── build/   # generated, ignored by git
└── dist/    # generated, ignored by git
```

`packaging/expense_splitter.spec` вычисляет корень проекта от своего
расположения и использует `src/` как путь импортов. Пользовательская рабочая
директория `data/` не встраивается в исполняемые файлы: данные создаются и
читаются в runtime-рабочей директории приложения.

## Windows

Из корня проекта:

```powershell
.\scripts\build-windows.ps1
```

Без UPX:

```powershell
.\scripts\build-windows.ps1 -NoUpx
```

Ожидаемые файлы:

```text
dist/expense-splitter.exe
dist/expense-splitter-launcher.exe
```

Проверка:

```powershell
.\dist\expense-splitter.exe --help
.\dist\expense-splitter-launcher.exe --help
```

## Linux/macOS

Из корня проекта:

```bash
./scripts/build-unix.sh
```

Без UPX:

```bash
./scripts/build-unix.sh --noupx
```

Ожидаемые файлы:

```text
dist/expense-splitter
dist/expense-splitter-launcher
```

Проверка:

```bash
./dist/expense-splitter --help
./dist/expense-splitter-launcher --help
```

## Git

`dist/` и `build/` являются generated artifacts и не должны попадать в commit.
Они уже перечислены в `.gitignore`.

## Troubleshooting

- Если PyInstaller не найден, переустановите dev-зависимости:
  `python -m pip install -e ".[dev]"`.
- Если сборка падает на путях, запускайте скрипт из корня проекта и проверьте,
  что существует `src/expense_splitter`.
- Если exe запускается, но не видит пользовательские данные, выполните
  `expense-splitter init` в нужной рабочей папке. Данные не встраиваются в exe.
