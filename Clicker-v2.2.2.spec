# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('icon.ico', '.'),
        ('icon.png', '.'),
        ('README.md', '.'),
        ('LICENSE', '.'),
        ('requirements.txt', '.'),
        ('clicker/config/default_settings.json', 'clicker/config/'),
        ('clicker/config/default_keystrokes.txt', 'clicker/config/'),
    ],
    hiddenimports=[
        'clicker.core.automation',
        'clicker.system.hotkeys',
        'clicker.ui.gui.main_window',
        'clicker.ui.indicators.system_tray',
        'clicker.config.manager',
        'clicker.utils.file_watcher',
        'clicker.system.singleton',
        'clicker.system.admin',
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
    name='Clicker-v2.2.2',
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
    icon='icon.ico',
)
