"""Audio manager for Helion Vanta client.

Handles SFX (one-shot .wav) and ambient music (.ogg / .mp3) with crossfade.
Ported from the Rust Belt MUD audio.py — interface is identical.

Sound event names expected from HelionVanta.UI.Sound GMCP:
  "footstep"        — movement on normal terrain
  "footstep_heavy"  — movement on stamina-costing terrain
  "enter_location"  — entering a named location
  "combat_start"    — combat begins
  "combat_hit"      — player takes a hit
  "combat_win"      — encounter won
  "ambient_change"  — context/terrain shift
"""
from __future__ import annotations

import pygame


class AudioManager:
    def __init__(self, asset_manager=None):
        self._am             = asset_manager
        self._sounds_enabled = True
        self._music_enabled  = True
        self._current_track  = None

        if not pygame.mixer.get_init():
            try:
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            except Exception as e:
                print(f"[AUDIO] mixer init failed: {e}", flush=True)

    # ------------------------------------------------------------------ #
    # Enable / disable
    # ------------------------------------------------------------------ #

    def set_sounds_enabled(self, enabled: bool):
        self._sounds_enabled = enabled

    def set_music_enabled(self, enabled: bool):
        self._music_enabled = enabled
        if not enabled:
            pygame.mixer.music.stop()
        elif self._current_track:
            self.play_music(self._current_track)

    # ------------------------------------------------------------------ #
    # Sound effects
    # ------------------------------------------------------------------ #

    def play_sound(self, event: str):
        if not self._sounds_enabled:
            return
        if self._am is None:
            return
        snd = self._am.get_sound(event)
        if snd:
            try:
                snd.play()
            except Exception:
                pass

    # GMCP handler — called with {"event": "footstep"} dict
    def on_sound(self, data: dict):
        event = data.get("event", "")
        if event:
            self.play_sound(event)

    # ------------------------------------------------------------------ #
    # Music
    # ------------------------------------------------------------------ #

    def play_music(self, track: str, loop: bool = True, fade_ms: int = 2000):
        if track == self._current_track:
            return
        self._current_track = track
        if not self._music_enabled:
            return
        if self._am is None:
            return
        path = self._am.get_music_path(track)
        if not path:
            print(f"[AUDIO] music track not found: {track}", flush=True)
            return
        try:
            pygame.mixer.music.fadeout(fade_ms // 2)
            pygame.mixer.music.load(path)
            pygame.mixer.music.play(-1 if loop else 0, fade_ms=fade_ms)
        except Exception as e:
            print(f"[AUDIO] music play error ({track}): {e}", flush=True)

    # GMCP handler — called with {"track": "overworld_ambient", "loop": true, "fade_ms": 2000}
    def on_music(self, data: dict):
        track   = data.get("track", "")
        loop    = data.get("loop", True)
        fade_ms = int(data.get("fade_ms", 2000))
        if track:
            self.play_music(track, loop=loop, fade_ms=fade_ms)

    # ------------------------------------------------------------------ #
    # Cleanup
    # ------------------------------------------------------------------ #

    def cleanup(self):
        try:
            pygame.mixer.music.stop()
            pygame.mixer.quit()
        except Exception:
            pass
