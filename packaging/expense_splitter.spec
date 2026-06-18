# -*- mode: python ; coding: utf-8 -*-

block_cipher = None


a = Analysis(
    ["../../src/expense_splitter/__main__.py"],
    pathex=["."],
    binaries=[],
    datas=[
        ("../../data", "data"),
        ("../../src/expense_splitter/defaults.py", "expense_splitter"),
        ("../../src/expense_splitter/models.py", "expense_splitter"),
        ("../../src/expense_splitter/storage.py", "expense_splitter"),
        ("../../src/expense_splitter/calculator.py", "expense_splitter"),
        ("../../src/expense_splitter/settlement.py", "expense_splitter"),
        ("../../src/expense_splitter/reporting.py", "expense_splitter"),
        ("../../src/expense_splitter/cli.py", "expense_splitter"),
        ("../../src/expense_splitter/launcher.py", "expense_splitter"),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="expense-splitter",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_info=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# Launcher for UX
launcher_a = Analysis(
    ["../../src/expense_splitter/launcher.py"],
    pathex=["."],
    binaries=[],
    datas=[
        ("../../data", "data"),
        ("../../src/expense_splitter/defaults.py", "expense_splitter"),
        ("../../src/expense_splitter/models.py", "expense_splitter"),
        ("../../src/expense_splitter/storage.py", "expense_splitter"),
        ("../../src/expense_splitter/calculator.py", "expense_splitter"),
        ("../../src/expense_splitter/settlement.py", "expense_splitter"),
        ("../../src/expense_splitter/reporting.py", "expense_splitter"),
        ("../../src/expense_splitter/cli.py", "expense_splitter"),
        ("../../src/expense_splitter/launcher.py", "expense_splitter"),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
launcher_pyz = PYZ(launcher_a.pure, launcher_a.zipped_data, cipher=block_cipher)

launcher_exe = EXE(
    launcher_pyz,
    launcher_a.scripts,
    launcher_a.binaries,
    launcher_a.zipfiles,
    launcher_a.datas,
    [],
    name="expense-splitter-launcher",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_info=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
