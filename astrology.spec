# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Western Astrology Calculator
This ensures all dependencies are bundled correctly
"""
from PyInstaller.utils.hooks import collect_submodules, collect_data_files
import os

a = Analysis(
    ['astrology_gui_fixed.py'],
    pathex=[],
    binaries=[],
    datas=[
        # Include kerykeion data files (ephemeris, configurations)
        *collect_data_files('kerykeion'),
        # Include pyswisseph ephemeris data
        *collect_data_files('pyswisseph'),
        # Include timezonefinder data
        *collect_data_files('timezonefinder'),
    ],
    hiddenimports=[
        'customtkinter',
        'geopy',
        'geopy.geocoders',
        'timezonefinder',
        'kerykeion',
        'kerykeion.chart_data_factory',
        'kerykeion.charts',
        'kerykeion.charts.chart_drawer',
        'kerykeion.astrological_subject',
        'kerykeion.report_generator',
        'pyswisseph',
        'tkinter',
        'threading',
        'datetime',
        'pathlib',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludedimports=[],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Western_Astrology_Calculator',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # False = GUI only (no console window)
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=('icon.ico' if os.path.exists('icon.ico') else None),
)
