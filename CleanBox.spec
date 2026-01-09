# -*- mode: python ; coding: utf-8 -*-
# CleanBox PyInstaller Spec File
# This file ensures all local modules are bundled correctly

import os
import sys

# SPECPATH is the directory containing this spec file
SRC_DIR = os.path.join(SPECPATH, 'src')

# Add src to path BEFORE importing hooks
sys.path.insert(0, SRC_DIR)

from PyInstaller.utils.hooks import collect_all, collect_submodules

# Collect everything from local packages using collect_all
# This is more comprehensive than collect_submodules
datas = []
binaries = []
hiddenimports = []

for pkg in ['features', 'shared', 'ui']:
    try:
        d, b, h = collect_all(pkg)
        datas += d
        binaries += b
        hiddenimports += h
        print(f"Collected {pkg}: {len(h)} hidden imports")
    except Exception as e:
        print(f"Warning: collect_all failed for {pkg}: {e}")
        # Fallback to collect_submodules
        try:
            hiddenimports += collect_submodules(pkg)
        except:
            pass

# Add explicit fallback imports to ensure they are included
hiddenimports += [
    'features',
    'features.cleanup',
    'features.cleanup.service',
    'features.cleanup.directory_detector',
    'features.cleanup.worker',
    'features.notifications',
    'features.notifications.service',
    'features.storage_monitor',
    'features.storage_monitor.service',
    'features.storage_monitor.utils',
    'features.folder_scanner',
    'shared',
    'shared.constants',
    'shared.registry',
    'shared.utils',
    'shared.config',
    'shared.config.manager',
    'ui',
    'ui.main_window',
    'ui.tray_icon',
    'ui.components',
    'ui.components.sidebar',
    'ui.views',
    'ui.views.cleanup_view',
    'ui.views.settings_view',
    'ui.views.storage_view',
    'app',
]

# Remove duplicates
hiddenimports = list(set(hiddenimports))
print(f"Total hidden imports: {len(hiddenimports)}")

a = Analysis(
    [os.path.join(SRC_DIR, 'main.py')],
    pathex=[SRC_DIR],
    binaries=binaries,
    datas=datas + [(os.path.join(SRC_DIR, 'assets'), 'assets')],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='CleanBox',
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
    icon=os.path.join(SRC_DIR, 'assets', 'icon.ico'),
)
