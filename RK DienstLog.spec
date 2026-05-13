# -*- mode: python ; coding: utf-8 -*-

import json

with open("version.json", "r", encoding="utf-8") as f:
    version_info = json.load(f)

APP_VERSION = version_info["version"]
APP_NAME = version_info["app_name"]
APP_BUNDLE_ID = version_info["bundle_id"]

a = Analysis(
    ['rk_dienstlog.py'],
    pathex=[],
    binaries=[],
    datas=[('version.json', '.'), ('rk_dienstlog_icon.png', '.')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='RK DienstLog',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['rk_dienstlog.icns'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='RK DienstLog',
)
app = BUNDLE(
    coll,
    name=f'{APP_NAME}.app',
    icon='rk_dienstlog.icns',
    bundle_identifier=APP_BUNDLE_ID,
    info_plist={
        'CFBundleShortVersionString': APP_VERSION,
        'CFBundleVersion': APP_VERSION,
        'CFBundleName': APP_NAME,
        'CFBundleDisplayName': APP_NAME,
    }
)
