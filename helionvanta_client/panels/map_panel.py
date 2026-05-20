"""Overworld map panel — renders the 13×9 GMCP viewport of the Helion Vanta grid.

Replaces RustBelt's RadarPanel.  Instead of a radar sweep it draws the ASCII
terrain tiles received via HelionVanta.World.Map GMCP, using the same zone-
aware colour palette as the server's terminal map.

Layout (same right-column slot as RustBelt's radar):
  ┌─────────────────────────────┐
  │ ◈  MAP  —  Kael Cluster     │  ← header bar
  ├─────────────────────────────┤
  │   . . h . . . h . . . . . . │
  │   . . . f . @ . . h . . . . │  ← 13×9 tile grid, @ = player
  │   . h . . . . . . . c . . . │
  │   ...                       │
  ├─────────────────────────────┤
  │ Dust Flats (15, 8)          │  ← terrain info footer
  │ Exits: N  E  S              │
  └─────────────────────────────┘

The glyph colours mirror overworld.py's zone palettes so the visual language
is consistent between the terminal and the graphical client.
"""
from __future__ import annotations

import pygame
from theme import (
    BG_PANEL, BG_HEADER, GOLD_MID, GOLD_DIM, GOLD_BRIGHT, GOLD_FAINT,
    BORDER_BRIGHT, BORDER_DIM, CORNER_LEN, CORNER_W,
    TEAL_BRIGHT, TEAL_MID,
)

HEADER_H = 26
FOOTER_H = 44    # space for terrain name + exits line

# ── Glyph colours matching overworld.py palettes ────────────────────────────

# Helion Reach (x < 32): warm, arid
_HELION_COLOURS: dict[str, tuple] = {
    ".":  (210, 170,  60),   # amber        — Dust Flats
    "h":  (200, 200, 200),   # light grey   — Shale Ridge
    "m":  ( 80,  80,  80),   # dark grey    — Mountain Peak
    "f":  ( 80, 180,  80),   # green        — Scrubland
    "w":  (210,  80,  80),   # bright red   — Wasteland
    "r":  (160,  60,  60),   # dark red     — Runoff Channel
    "i":  ( 80, 190, 200),   # cyan         — Industrial Ruins
    "=":  (120, 220, 230),   # bright cyan  — Trade Road
    "~":  ( 60,  80, 180),   # blue         — Toxin Flats
    "c":  (230, 190,  50),   # gold         — Settlement
    "*":  (240, 240, 240),   # bright white — Named Location
    "@":  ( 80, 230, 120),   # bright green — Player
}

# Vanta IX (x >= 48): alien, cool
_VANTA_COLOURS: dict[str, tuple] = {
    ".":  ( 80, 220, 210),   # bright cyan    — Glass Dunes
    "f":  (210,  80, 220),   # bright magenta — Crystal Spires
    "h":  ( 80,  80,  80),   # dark grey      — Obsidian Hills
    "m":  ( 60,  60,  60),   # dark grey      — Void Peak
    "~":  ( 60,  80, 180),   # blue           — Null Sea
    "a":  (180,  60, 180),   # magenta        — Anomaly Zone
    "R":  (210, 165,  55),   # amber          — Ancient Ruins
    "=":  ( 80, 210, 220),   # bright cyan    — Carved Path
    "s":  (180, 180, 180),   # light grey     — Shattered Ground
    "c":  (230, 190,  50),   # gold           — Clan Outpost
    "*":  (240, 240, 240),   # bright white   — Named Location
    "@":  ( 80, 230, 120),   # bright green   — Player
}

# Asteroid Void (32 <= x < 48)
_VOID_COLOURS: dict[str, tuple] = {
    ":":  ( 70,  70,  70),   # dark grey  — Asteroid Debris
    "=":  ( 60, 160, 170),   # cyan       — Tradelane
    "*":  (240, 240, 240),
    "@":  ( 80, 230, 120),
}

# Generic / mini-overworld fallbacks
_GENERIC_COLOURS: dict[str, tuple] = {
    ".":  (200, 165,  55),
    "h":  (180, 180, 180),
    "m":  ( 80,  80,  80),
    "f":  ( 80, 180,  80),
    "w":  (200,  80,  80),
    "r":  (150,  55,  55),
    "i":  ( 80,  80,  80),
    "=":  ( 70, 190, 200),
    "~":  ( 55,  75, 175),
    "c":  (220, 180,  45),
    "a":  (175,  55, 175),
    "R":  ( 80,  80,  80),
    "s":  (160, 160, 160),
    ":":  ( 70,  70,  70),
    "g":  ( 80,  80,  80),
    "d":  (160,  55,  55),
    "#":  ( 70,  70,  70),
    "*":  (240, 240, 240),
    "@":  ( 80, 230, 120),
    " ":  ( 10,  18,  24),   # out-of-bounds
}

_IMPASSABLE_GLYPHS = frozenset({"m", "~", ":", "#"})


def _glyph_colour(glyph: str, col: int, planet: str) -> tuple:
    """Return an RGB tuple for *glyph* at column *col* on *planet*."""
    if planet == "kael_cluster":
        if col < 32:
            return _HELION_COLOURS.get(glyph) or _GENERIC_COLOURS.get(glyph, (120, 120, 120))
        elif col < 48:
            return _VOID_COLOURS.get(glyph) or _GENERIC_COLOURS.get(glyph, (120, 120, 120))
        else:
            return _VANTA_COLOURS.get(glyph) or _GENERIC_COLOURS.get(glyph, (120, 120, 120))
    return _GENERIC_COLOURS.get(glyph, (120, 120, 120))


def _corner_brackets(surf, rect, color=BORDER_BRIGHT):
    x, y, w, h = rect.x, rect.y, rect.w, rect.h
    for (cx, cy, dx, dy) in [
        (x,     y,      1,  1), (x+w-1, y,     -1,  1),
        (x,     y+h-1,  1, -1), (x+w-1, y+h-1, -1, -1),
    ]:
        pygame.draw.line(surf, color, (cx, cy), (cx + dx*CORNER_LEN, cy), CORNER_W)
        pygame.draw.line(surf, color, (cx, cy), (cx, cy + dy*CORNER_LEN), CORNER_W)


class MapPanel:
    """Draws the overworld tile viewport sent via HelionVanta.World.Map GMCP."""

    TILE_W = 14   # pixels per tile (monospace cell width)
    TILE_H = 16   # pixels per tile (monospace cell height)

    def __init__(self, rect: pygame.Rect, font: pygame.font.Font):
        self.rect   = rect
        self.font   = font
        self._data  = {}   # last GMCP payload
        self._font_tile: pygame.font.Font | None = None
        self._build_tile_font()

    # ------------------------------------------------------------------ #
    # GMCP handler
    # ------------------------------------------------------------------ #

    def on_map(self, data: dict):
        """Called when HelionVanta.World.Map GMCP arrives."""
        self._data = data

    # ------------------------------------------------------------------ #
    # Internal
    # ------------------------------------------------------------------ #

    def _build_tile_font(self):
        """Pick a monospace font for tile rendering, slightly larger than the UI font."""
        for name in ("Consolas", "DejaVu Sans Mono", "Courier New", "monospace"):
            try:
                f = pygame.font.SysFont(name, 15)
                if f:
                    self._font_tile = f
                    return
            except Exception:
                pass
        self._font_tile = pygame.font.Font(None, 15)

    # ------------------------------------------------------------------ #
    # Draw
    # ------------------------------------------------------------------ #

    def draw(self, surface: pygame.Surface):
        # Panel chrome
        pygame.draw.rect(surface, BG_PANEL, self.rect)
        pygame.draw.rect(surface, BORDER_BRIGHT, self.rect, 1)
        _corner_brackets(surface, self.rect)

        # Header
        hdr = pygame.Rect(self.rect.x, self.rect.y, self.rect.w, HEADER_H)
        pygame.draw.rect(surface, BG_HEADER, hdr)
        pygame.draw.line(surface, BORDER_DIM,
                         (hdr.x, hdr.bottom), (hdr.right, hdr.bottom), 1)

        planet_name = self._data.get("planet_name", "")
        label = "◈  MAP" + (f"  —  {planet_name}" if planet_name else "")
        lbl_s = self.font.render(label, True, GOLD_MID)
        surface.blit(lbl_s, (hdr.x + 8, hdr.y + (HEADER_H - lbl_s.get_height()) // 2))

        if not self._data:
            self._draw_no_data(surface)
            return

        rows   = self._data.get("rows", [])
        planet = self._data.get("planet", "")
        px     = self._data.get("x", 0)
        py     = self._data.get("y", 0)

        # ── Tile grid ──────────────────────────────────────────────────
        # Available vertical space between header and footer
        footer_rect = pygame.Rect(
            self.rect.x + 1,
            self.rect.bottom - FOOTER_H,
            self.rect.w - 2,
            FOOTER_H,
        )
        grid_rect = pygame.Rect(
            self.rect.x + 1,
            self.rect.y + HEADER_H + 1,
            self.rect.w - 2,
            self.rect.h - HEADER_H - FOOTER_H - 2,
        )
        pygame.draw.rect(surface, (8, 14, 20), grid_rect)

        if rows:
            tile_h = min(self.TILE_H, max(10, grid_rect.h // len(rows)))
            tile_w = min(self.TILE_W, max(8, grid_rect.w // (len(rows[0]) if rows[0] else 13)))

            # Centre the grid inside the available area
            total_w = tile_w * (len(rows[0]) if rows else 13)
            total_h = tile_h * len(rows)
            start_x = grid_rect.x + max(0, (grid_rect.w - total_w) // 2)
            start_y = grid_rect.y + max(0, (grid_rect.h - total_h) // 2)

            # Viewport half-widths (13 wide = 6+1+6, 9 tall = 4+1+4)
            half_w = (len(rows[0]) - 1) // 2 if rows else 6
            half_h = (len(rows) - 1) // 2 if rows else 4

            for row_i, row_str in enumerate(rows):
                gy = py - half_h + row_i   # absolute grid y of this row
                for col_i, glyph in enumerate(row_str):
                    gx = px - half_w + col_i   # absolute grid x of this cell
                    color = _glyph_colour(glyph, gx, planet)
                    glyph_surf = self._font_tile.render(glyph, True, color)
                    dx = start_x + col_i * tile_w
                    dy = start_y + row_i * tile_h
                    surface.blit(glyph_surf, (dx, dy))

            # Highlight ring around player tile (@)
            cx = start_x + half_w * tile_w
            cy = start_y + half_h * tile_h
            pygame.draw.rect(surface, (80, 230, 120),
                             pygame.Rect(cx - 1, cy - 1, tile_w + 2, tile_h + 2), 1)

        # ── Footer ─────────────────────────────────────────────────────
        pygame.draw.rect(surface, BG_HEADER, footer_rect)
        pygame.draw.line(surface, BORDER_DIM,
                         (footer_rect.x, footer_rect.y),
                         (footer_rect.right, footer_rect.y), 1)

        terrain_name = self._data.get("terrain_name", "")
        coords       = f"({self._data.get('x', 0)}, {self._data.get('y', 0)})"
        exits        = self._data.get("exits", [])
        named_loc    = self._data.get("named_location")

        fx = footer_rect.x + 6
        fy = footer_rect.y + 4

        header_txt = f"{terrain_name}  {coords}"
        if named_loc:
            header_txt += f"  ★ {named_loc}"
        header_s = self.font.render(header_txt, True, GOLD_BRIGHT)
        surface.blit(header_s, (fx, fy))

        if exits:
            exit_str = "  ".join(d.upper() for d in sorted(exits))
            exit_s   = self.font.render(f"Exits: {exit_str}", True, GOLD_DIM)
            surface.blit(exit_s, (fx, fy + 18))

    def _draw_no_data(self, surface: pygame.Surface):
        body = pygame.Rect(
            self.rect.x + 1,
            self.rect.y + HEADER_H + 1,
            self.rect.w - 2,
            self.rect.h - HEADER_H - 2,
        )
        pygame.draw.rect(surface, (8, 14, 20), body)
        cx, cy = body.centerx, body.centery
        msg = self.font.render("No map data", True, GOLD_DIM)
        surface.blit(msg, (cx - msg.get_width() // 2, cy - msg.get_height() // 2))
        hint = self.font.render("(move or look to update)", True, GOLD_FAINT)
        surface.blit(hint, (cx - hint.get_width() // 2, cy + 12))
