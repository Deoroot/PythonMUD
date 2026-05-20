"""Minimal asset manager for Helion Vanta client.

Loads loose image and audio files from the assets/ directory next to this
script.  No pk3/zip pack support is needed for Helion Vanta — all assets
are loose files organised in a simple directory tree:

  assets/
    ui/
      icon.png          — window icon
      cursor.png        — optional custom cursor
      context/          — context background images
        overworld.png
        settlement.png
        named_location.png
        ruins.png
        dungeon.png
        combat.png
    sounds/             — short .wav SFX
    music/              — ambient .ogg tracks
    config.json         — optional server address override

Missing files are handled gracefully (placeholder surfaces / silent audio).
"""

from __future__ import annotations

import os
import json
import pygame


class AssetManager:
    def __init__(self, assets_dir: str, writable_assets_dir: str | None = None):
        self.assets_dir          = assets_dir
        self.writable_assets_dir = writable_assets_dir or assets_dir
        self.boot_log: list[str] = []
        self._image_cache: dict[str, pygame.Surface | None] = {}
        self._sound_cache: dict[str, pygame.mixer.Sound | None] = {}
        self._log(f"--- Helion Vanta asset dir: {assets_dir}")
        if os.path.isdir(assets_dir):
            self._log(f"+ Found asset directory.")
        else:
            self._log(f"! Asset directory not found — using placeholders.")

    # ------------------------------------------------------------------ #
    # Logging
    # ------------------------------------------------------------------ #

    def _log(self, msg: str):
        self.boot_log.append(msg)
        print(f"[ASSET] {msg}", flush=True)

    # ------------------------------------------------------------------ #
    # Raw file access (used for cursor, etc.)
    # ------------------------------------------------------------------ #

    def open_file(self, rel_path: str):
        """Return the full path string if the file exists, else None."""
        full = os.path.join(self.assets_dir, rel_path)
        if os.path.exists(full):
            return full
        return None

    # ------------------------------------------------------------------ #
    # Config
    # ------------------------------------------------------------------ #

    def load_config(self) -> dict:
        path = os.path.join(self.assets_dir, "config.json")
        if os.path.exists(path):
            try:
                with open(path, encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                self._log(f"! config.json parse error: {e}")
        return {}

    # ------------------------------------------------------------------ #
    # Images
    # ------------------------------------------------------------------ #

    def get_image(self, rel_path: str, size: tuple[int, int] | None = None) -> pygame.Surface | None:
        """Load and cache a surface from assets/<rel_path>.

        Returns None if the file does not exist.  Optionally scales to *size*.
        """
        key = f"{rel_path}@{size}"
        if key in self._image_cache:
            return self._image_cache[key]

        full = os.path.join(self.assets_dir, rel_path)
        surf = None
        if os.path.exists(full):
            try:
                surf = pygame.image.load(full).convert_alpha()
                if size and surf.get_size() != size:
                    surf = pygame.transform.smoothscale(surf, size)
                self._log(f"+ {rel_path}")
            except Exception as e:
                self._log(f"! {rel_path}: {e}")
        self._image_cache[key] = surf
        return surf

    def get_context_image(self, context: str,
                          size: tuple[int, int] | None = None) -> pygame.Surface | None:
        """Load assets/ui/context/<context>.png"""
        return self.get_image(f"ui/context/{context}.png", size=size)

    def get_ui_element(self, name: str,
                       size: tuple[int, int] | None = None) -> pygame.Surface | None:
        """Load assets/ui/<name>.png"""
        return self.get_image(f"ui/{name}.png", size=size)

    # ------------------------------------------------------------------ #
    # Sounds
    # ------------------------------------------------------------------ #

    def get_sound(self, name: str) -> pygame.mixer.Sound | None:
        """Load assets/sounds/<name>.wav  (cached)."""
        if name in self._sound_cache:
            return self._sound_cache[name]
        path = os.path.join(self.assets_dir, "sounds", f"{name}.wav")
        snd  = None
        if os.path.exists(path):
            try:
                snd = pygame.mixer.Sound(path)
                self._log(f"+ sounds/{name}.wav")
            except Exception as e:
                self._log(f"! sounds/{name}.wav: {e}")
        self._sound_cache[name] = snd
        return snd

    def get_music_path(self, name: str) -> str | None:
        """Return the full path to assets/music/<name>.ogg or .mp3, or None."""
        for ext in (".ogg", ".mp3"):
            p = os.path.join(self.assets_dir, "music", f"{name}{ext}")
            if os.path.exists(p):
                return p
        return None

    # ------------------------------------------------------------------ #
    # Placeholder surface
    # ------------------------------------------------------------------ #

    @staticmethod
    def make_placeholder(size: tuple[int, int], color=(20, 30, 35)) -> pygame.Surface:
        surf = pygame.Surface(size)
        surf.fill(color)
        return surf
