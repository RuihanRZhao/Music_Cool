# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['../../src/python/main.py'],
    pathex=[],
    binaries=[
        # C++扩展模块（需要先编译）
        # ('../../build/ncm_decoder.so', '.'),
    ],
    datas=[
        # 图标文件
        # ('../../packaging/icons/app.icns', '.'),
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
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='NCMDecoder',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='NCMDecoder',
)

app = BUNDLE(
    coll,
    name='NCMDecoder.app',
    icon=None,  # 可以指定.icns文件路径
    bundle_identifier='com.cloudmusicdecoder.ncmdecoder',
)
