# -*- mode: python ; coding: utf-8 -*-
import os
import shutil
import subprocess

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

# Copy libpython and other .so files to a local patched dir, then clear the
# executable-stack flag so the binary runs on kernels that refuse execstack.
patched_dir = os.path.join(SPECPATH, 'build', 'patched_libs')
os.makedirs(patched_dir, exist_ok=True)

patched_binaries = []
for dest, src, kind in a.binaries:
    if src and os.path.isfile(src) and ('.so' in os.path.basename(src)):
        dst = os.path.join(patched_dir, os.path.basename(src))
        shutil.copy2(src, dst)
        subprocess.run(['patchelf', '--clear-execstack', dst], check=False)
        patched_binaries.append((dest, dst, kind))
    else:
        patched_binaries.append((dest, src, kind))
a.binaries = patched_binaries

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='reactionbalancer',
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
