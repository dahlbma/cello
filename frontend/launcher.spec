# -*- mode: python ; coding: utf-8 -*-


block_cipher = None


b = Analysis(
    ['launcher.py'],
    pathex=[],
    binaries=[],
    datas=[('./assets/launcher.ui', './assets'), ('./assets/*.ico', './assets')],
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
bpyz = PYZ(b.pure, b.zipped_data, cipher=block_cipher)

bexe = EXE(
    bpyz,
    b.scripts,
    b.binaries,
    b.zipfiles,
    b.datas,
    [],
    name='cello',
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
)