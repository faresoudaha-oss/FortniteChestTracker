# -*- mode: python ; coding: utf-8 -*-
import os

datas = [('assets', 'assets')]
if os.path.isdir('bin'):                      # ReplayExporter.exe compilé avant PyInstaller
    datas.append(('bin', 'bin'))

a = Analysis(['main.py'], pathex=['.'], datas=datas,
             excludes=['PySide6.QtWebEngineCore', 'PySide6.QtWebEngineWidgets', 'PySide6.Qt3DCore',
                       'PySide6.QtQuick', 'PySide6.QtQml', 'PySide6.QtMultimedia', 'PySide6.QtPdf'])
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, a.binaries, a.datas, [], name='FortniteChestTracker',
          icon='assets/icon.ico', console=False, upx=False, onefile=True)
