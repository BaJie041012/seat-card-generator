# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for 席卡生成系统 desktop app"""

import os
import customtkinter

block_cipher = None
ctk_path = customtkinter.__path__[0]
base_dir = os.path.dirname(os.path.abspath(SPEC))

a = Analysis(
    [os.path.join(base_dir, 'desktop_app.py')],
    pathex=[base_dir],
    binaries=[],
    datas=[
        # templates
        (os.path.join(base_dir, 'templates'), 'templates'),
        # customtkinter assets
        (os.path.join(ctk_path, 'assets'), 'customtkinter/assets'),
    ],
    hiddenimports=[
        'customtkinter',
        'config',
        'ai_service',
        'text_extractor',
        'card_generator',
        'template_processor',
        'docx',
        'PyPDF2',
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
    name='席卡生成系统',
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
)
