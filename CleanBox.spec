# -*- mode: python ; coding: utf-8 -*-
# CleanBox PyInstaller Spec File
# This file ensures all local modules are bundled correctly

a = Analysis(
    ['src/main.py'],
    pathex=['src'],
    binaries=[],
    datas=[('src/assets', 'assets')],
    hiddenimports=[
        # Features
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
        # Shared
        'shared',
        'shared.constants',
        'shared.registry',
        'shared.utils',
        'shared.config',
        'shared.config.manager',
        # UI
        'ui',
        'ui.main_window',
        'ui.tray_icon',
        'ui.components',
        'ui.components.sidebar',
        'ui.views',
        'ui.views.cleanup_view',
        'ui.views.settings_view',
        'ui.views.storage_view',
    ],
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
    icon='src/assets/icon.ico',
)
