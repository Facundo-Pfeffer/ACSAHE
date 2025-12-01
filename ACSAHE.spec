# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_submodules

# Collect all plotly submodules to avoid ModuleNotFoundError
plotly_submodules = collect_submodules('plotly')

a = Analysis(
    ['main.py'],
    pathex=[r'C:\HP Laptop Facundo Pfeffer - Drive Backup\Repositories\ACSAHE'],
    binaries=[],
    datas=[('build', 'build')],
    hiddenimports=plotly_submodules,
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
    a.binaries,
    a.datas,
    [],
    name='ACSAHE',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['build\\gui\\images\\logo_H.ico'],
)
