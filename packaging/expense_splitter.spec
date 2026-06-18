# -*- mode: python ; coding: utf-8 -*-

import os
from pathlib import Path

block_cipher = None
UPX_ENABLED = os.environ.get("PYINSTALLER_NO_UPX") != "1"

PACKAGING_DIR = Path(SPECPATH).resolve()
PROJECT_ROOT = PACKAGING_DIR.parent
SRC_DIR = PROJECT_ROOT / "src"


def source_path(*parts):
    return str(SRC_DIR.joinpath(*parts))


common_analysis_kwargs = {
    "pathex": [str(SRC_DIR), str(PROJECT_ROOT)],
    "binaries": [],
    # User data lives in the runtime working directory and is intentionally not bundled.
    "datas": [],
    "hiddenimports": [],
    "hookspath": [],
    "hooksconfig": {},
    "runtime_hooks": [],
    "excludes": [],
    "win_no_prefer_redirects": False,
    "win_private_assemblies": False,
    "cipher": block_cipher,
    "noarchive": False,
}


cli_analysis = Analysis(
    [source_path("expense_splitter", "__main__.py")],
    **common_analysis_kwargs,
)
cli_pyz = PYZ(cli_analysis.pure, cli_analysis.zipped_data, cipher=block_cipher)

cli_exe = EXE(
    cli_pyz,
    cli_analysis.scripts,
    cli_analysis.binaries,
    cli_analysis.zipfiles,
    cli_analysis.datas,
    [],
    name="expense-splitter",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=UPX_ENABLED,
    upx_exclude=[],
    runtime_info=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

launcher_analysis = Analysis(
    [source_path("expense_splitter", "launcher.py")],
    **common_analysis_kwargs,
)
launcher_pyz = PYZ(launcher_analysis.pure, launcher_analysis.zipped_data, cipher=block_cipher)

launcher_exe = EXE(
    launcher_pyz,
    launcher_analysis.scripts,
    launcher_analysis.binaries,
    launcher_analysis.zipfiles,
    launcher_analysis.datas,
    [],
    name="expense-splitter-launcher",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=UPX_ENABLED,
    upx_exclude=[],
    runtime_info=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
