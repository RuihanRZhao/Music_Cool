# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from PyInstaller.utils.hooks import collect_submodules

# Get paths - PyInstaller runs from project root, spec file is in packaging/pyinstaller/
# Use relative paths from project root (where PyInstaller is executed)
project_root = os.getcwd()  # PyInstaller runs from project root
python_src_dir = os.path.join(project_root, 'src', 'python')

# Add src/python to sys.path for this spec file
sys.path.insert(0, python_src_dir)

block_cipher = None

# Collect all submodules from gui package automatically
gui_hiddenimports = collect_submodules('gui')

a = Analysis(
    [os.path.join(python_src_dir, 'main.py')],
    pathex=[
        python_src_dir,  # Add src/python to path so 'gui' module can be found
    ],
    binaries=[
        # C++扩展模块（需要先编译）
        (os.path.join(project_root, 'build', 'ncm_decoder.pyd'), '.'),
        # OpenSSL DLL（如果使用动态链接）
        # (os.path.join(project_root, 'src', 'shared', 'ext', 'lib', 'libcrypto-1_1.dll'), '.'),
        # (os.path.join(project_root, 'src', 'shared', 'ext', 'lib', 'libssl-1_1.dll'), '.'),
    ],
    datas=[
        # 图标文件
        # (str(project_root / 'packaging' / 'icons' / 'app.ico'), '.'),
    ],
    hiddenimports=[
        'PyQt6',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'ncm_decoder',
        'decoder_wrapper',
    ] + gui_hiddenimports,  # Add all gui submodules automatically
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
    name='NCMDecoder',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 不显示控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # 可以指定图标文件路径
)
