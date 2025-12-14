# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['../../src/python/main.py'],
    pathex=[],
    binaries=[
        # C++扩展模块（需要先编译）
        ('../../build/ncm_decoder.pyd', '.'),
        # OpenSSL DLL（如果使用动态链接）
        # ('../../src/shared/ext/lib/libcrypto-1_1.dll', '.'),
        # ('../../src/shared/ext/lib/libssl-1_1.dll', '.'),
    ],
    datas=[
        # 图标文件
        # ('../../packaging/icons/app.ico', '.'),
    ],
    hiddenimports=[
        'PyQt6',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'ncm_decoder',
    ],
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
