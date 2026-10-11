"""Gera "my chaotic room.exe" (arquivo único) em dist/.

Uso:
    pip install pyinstaller customtkinter pillow
    python build_exe.py
"""

import os
import PyInstaller.__main__

AQUI = os.path.dirname(os.path.abspath(__file__))
ICONE = os.path.join(AQUI, "assets_icone", "icone_app_instrumentos", "icone.ico")

PyInstaller.__main__.run([
    os.path.join(AQUI, "app.py"),
    "--noconfirm", "--clean", "--onefile", "--windowed",
    "--name", "my chaotic room",
    "--icon", ICONE,
    "--add-data", f"{os.path.join(AQUI, 'assets_icone', 'icone_app_instrumentos')};assets_icone/icone_app_instrumentos",
    "--collect-all", "customtkinter",
])
