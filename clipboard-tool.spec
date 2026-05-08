# -*- mode: python ; coding: utf-8 -*-
"""
通用 PyInstaller spec 文件
支持：Ubuntu (Linux)、macOS (x86_64 & arm64)、Windows
"""
import sys
from PyInstaller.utils.hooks import collect_all

# 根据平台自动选择 pynput 隐藏导入
PLATFORM_HIDDEN_IMPORTS = {
    'darwin': [  # macOS (包括 x86_64 和 arm64)
        'pynput.keyboard._darwin',
        'pynput.mouse._darwin',
    ],
    'win32': [   # Windows
        'pynput.keyboard._win32',
        'pynput.mouse._win32',
    ],
    'linux': [   # Linux (Ubuntu 等)
        'pynput.keyboard._xorg',
        'pynput.mouse._xorg',
    ],
}

# 获取当前平台的隐藏导入
pynput_imports = PLATFORM_HIDDEN_IMPORTS.get(sys.platform, [])

# 基础隐藏导入（所有平台通用）
hiddenimports = [
    'PyQt6.QtSql',
] + pynput_imports

# 收集 PyQt6 的所有资源
datas = []
binaries = []
tmp_ret = collect_all('PyQt6')
datas += tmp_ret[0]
binaries += tmp_ret[1]
hiddenimports += tmp_ret[2]

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'numpy',
        'scipy',
        'pandas',
        'tkinter',
        'unittest',
        'pydoc',
        'doctest',
    ],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='clipboard-tool',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='clipboard-tool',
)
