"""Character status panel — HP / stamina bars and character info.

Replaces RustBelt's ShipPanel.  Displays:
  - Character name
  - Current planet / coordinates
  - HP bar
  - Stamina bar
  - Credits

Data comes from HelionVanta.Char.Status GMCP:
  {
    "name":     "Kira",
    "hp":       80,
    "hp_max":   100,
    "stamina":  65,
    "stam_max": 100,
    "credits":  1500,
    "planet":   "kael_cluster",
    "x":        15,
    "y":        8
  }
"""
from __future__ import annotations

import pygame
from theme import (
    BG_PANEL, BG_HEADER, GOLD_BRIGHT, GOLD_MID, GOLD_DIM,
    BORDER_BRIGHT, BORDER_DIM, COL_BAR_BG,
    COL_HP, COL_STAMINA, COL_WARN, COL_DANGER, COL_OK,
    CORNER_LEN, CORNER_W,
)

_PLANET_LABELS = {
    "kael_cluster":    "Kael Cluster",
    "helion_reach":    "Helion Reach",
    "vanta_ix":        "Vanta IX",
    "glass_dunes_ruins": "Glass Dunes Ruins",
    "cinder_warrens":  "Cinder Warrens",
}


def _corner_brackets(surf, rect, color=BORDER_BRIGHT):
    x, y, w, h = rect.x, rect.y, rect.w, rect.h
    for (cx, cy, dx, dy) in [
        (x,     y,      1,  1), (x+w-1, y,     -1,  1),
        (x,     y+h-1,  1, -1), (x+w-1, y+h-1, -1, -1),
    ]:
        pygame.draw.line(surf, color, (cx, cy), (cx + dx*CORNER_LEN, cy), CORNER_W)
        pygame.draw.line(surf, color, (cx, cy), (cx, cy + dy*CORNER_LEN), CORNER_W)


class CharPanel:
    """Displays character name, location, HP, stamina and credits."""

    BAR_H = 9

    def __init__(self, rect: pygame.Rect, font: pygame.font.Font):
        self.rect = rect
        self.font = font
        self.data: dict = {}

    # ------------------------------------------------------------------ #
    # GMCP handler
    # ------------------------------------------------------------------ #

    def on_status(self, data: dict):
        """Called when HelionVanta.Char.Status GMCP arrives."""
        self.data = data

    # ------------------------------------------------------------------ #
    # Draw
    # ------------------------------------------------------------------ #

    def draw(self, surface: pygame.Surface):
        pygame.draw.rect(surface, BG_PANEL, self.rect)
        pygame.draw.rect(surface, BORDER_BRIGHT, self.rect, 1)
        _corner_brackets(surface, self.rect)

        x = self.rect.x + 10
        y = self.rect.y + 6

        # Header bar
        pygame.draw.rect(surface, BG_HEADER,
                         pygame.Rect(self.rect.x, self.rect.y, self.rect.w, 24))
        pygame.draw.line(surface, BORDER_DIM,
                         (self.rect.x, self.rect.y + 24),
                         (self.rect.right, self.rect.y + 24), 1)
        heading = self.font.render("◈  CHARACTER", True, GOLD_MID)
        surface.blit(heading, (x, y + 3))
        y += 30

        d = self.data
        if not d:
            placeholder = self.font.render("—  no character data  —", True, GOLD_DIM)
            surface.blit(placeholder, (x, y))
            return

        bar_w = self.rect.w - 20

        # Name
        name_surf = self.font.render(d.get("name", "Unknown"), True, GOLD_BRIGHT)
        surface.blit(name_surf, (x, y)); y += 18

        # Location
        planet_key  = d.get("planet", "")
        planet_lbl  = _PLANET_LABELS.get(planet_key, planet_key.replace("_", " ").title())
        coords      = f"({d.get('x', 0)}, {d.get('y', 0)})"
        loc_txt     = f"{planet_lbl}  {coords}" if planet_lbl else coords
        loc_surf    = self.font.render(loc_txt, True, GOLD_DIM)
        surface.blit(loc_surf, (x, y)); y += 20

        # HP bar
        self._bar(surface, x, y, "HP",
                  d.get("hp", 0), d.get("hp_max", 1), COL_HP, bar_w)
        y += 26

        # Stamina bar
        self._bar(surface, x, y, "STAMINA",
                  d.get("stamina", 0), d.get("stam_max", 1), COL_STAMINA, bar_w)
        y += 26

        # Credits
        credits = d.get("credits", 0)
        cr_surf = self.font.render(f"Credits  {credits:,}", True, GOLD_MID)
        surface.blit(cr_surf, (x, y))

    # ------------------------------------------------------------------ #

    def _bar(self, surface, x, y, label, current, maximum, color, bar_w):
        lbl = self.font.render(
            f"{label:<8}  {current}/{maximum}", True, GOLD_MID
        )
        surface.blit(lbl, (x, y))
        y += 13
        track = pygame.Rect(x, y, bar_w, self.BAR_H)
        pygame.draw.rect(surface, COL_BAR_BG, track)
        fill_w = int(bar_w * min(current / max(maximum, 1), 1.0))
        frac   = current / max(maximum, 1)
        draw_col = color if frac > 0.35 else COL_WARN if frac > 0.15 else COL_DANGER
        if fill_w > 0:
            pygame.draw.rect(surface, draw_col, (track.x, track.y, fill_w, self.BAR_H))
        pygame.draw.rect(surface, BORDER_DIM, track, 1)
