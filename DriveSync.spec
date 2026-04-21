# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['DriveSync.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['pandas', 'numpy', 'matplotlib', 'scipy', 'tkinter', 'PIL', 'openpyxl', 'PyQt5', 'PyQt6', 'PySide2', 'PySide6', 'IPython', 'notebook', 'jedi', 'docutils', 'tzdata', 'setuptools', 'distutils', 'wheel', 'pkg_resources', 'pip'],
    noarchive=False,
    optimize=2,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='DriveSync',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['DriveSync.ico'],
)
