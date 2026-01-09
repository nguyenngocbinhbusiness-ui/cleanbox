# -*- mode: python ; coding: utf-8 -*-
# CleanBox PyInstaller Spec File
# This file ensures all local modules are bundled correctly

import os
import sys
from PyInstaller.utils.hooks import collect_submodules

# SPECPATH is the directory containing this spec file
# For this project, spec file is in project root, src is a subdirectory
SRC_DIR = os.path.join(SPECPATH, 'src')

# Add src to path for module collection
sys.path.insert(0, SRC_DIR)

# Collect ALL submodules from local packages
hiddenimports = []
hiddenimports += collect_submodules('features')
hiddenimports += collect_submodules('shared')
hiddenimports += collect_submodules('ui')

# Add explicit imports as fallback
hiddenimports += [
    'features.notifications.service',
    'features.cleanup.service',
    'features.cleanup.directory_detector',
    'features.cleanup.worker',
    'features.storage_monitor.service',
    'features.storage_monitor.utils',
    'shared.config.manager',
    'shared.constants',
    'shared.registry',
    'shared.utils',
    'ui.main_window',
    'ui.tray_icon',
    'ui.components.sidebar',
    'ui.views.cleanup_view',
    'ui.views.settings_view',
    'ui.views.storage_view',
]

a = Analysis(
    [os.path.join(SRC_DIR, 'main.py')],
    pathex=[SRC_DIR],
    binaries=[],
    datas=[(os.path.join(SRC_DIR, 'assets'), 'assets')],
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
