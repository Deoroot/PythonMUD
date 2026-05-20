"""Frozen-executable-safe path resolution for the Helion Vanta client.

In a normal Python run, paths resolve relative to this file.
In a PyInstaller bundle (--onedir or --onefile), sys.frozen is True and
sys.executable points to the binary — assets live next to the binary on
disk so they can be updated without touching the binary itself.

Directory layout:
    <base_dir>/
        helionvanta[.exe]
        assets/
            ui/        ← context images, icon, font
            sounds/    ← SFX and music files
            config.json
"""
import os
import sys


def base_dir() -> str:
    """Directory that contains the assets/ folder.

    - Frozen (PyInstaller): directory of the binary
    - Normal Python run: directory of this file (helionvanta_client/)
    """
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


def assets_dir() -> str:
    """Path to the assets/ directory."""
    return os.path.join(base_dir(), "assets")


def data_dir() -> str:
    """Writable directory for runtime data (auth meta, cache).

    - Windows / portable installs: same as base_dir()
    - Linux system-wide install (base_dir not writable): XDG_DATA_HOME/helionvanta/
    """
    bd = base_dir()
    if sys.platform != "win32" and not os.access(bd, os.W_OK):
        xdg = os.environ.get("XDG_DATA_HOME",
                              os.path.join(os.path.expanduser("~"), ".local", "share"))
        return os.path.join(xdg, "helionvanta")
    return bd


def writable_assets_dir() -> str:
    """The assets/ directory under data_dir() — guaranteed writable."""
    return os.path.join(data_dir(), "assets")
