# -*- mode: python ; coding: utf-8 -*-
# Build : pyinstaller packaging/voicenik.spec
# Produit dist/VoiceNik/ (mode onedir : démarrage rapide, contrairement au onefile
# qui devrait décompresser >1 Go de DLL CUDA à chaque lancement).

import site
from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files

project_root = Path(SPECPATH).parent

# DLL cuBLAS / cuDNN des wheels pip nvidia-* (transcription GPU).
cuda_binaries = []
for base in site.getsitepackages():
    for dll in Path(base, "nvidia").glob("*/bin/*.dll"):
        cuda_binaries.append((str(dll), "."))

a = Analysis(
    [str(project_root / "voicenik" / "__main__.py")],
    pathex=[str(project_root)],
    binaries=cuda_binaries,
    datas=collect_data_files("faster_whisper")
    + [(str(project_root / "voicenik" / "assets"), "voicenik/assets")],
    hiddenimports=["pystray._win32"],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    exclude_binaries=True,
    name="VoiceNik",
    console=False,
    upx=False,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    name="VoiceNik",
)
