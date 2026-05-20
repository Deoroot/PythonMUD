"""Context image panel for the Helion Vanta client.

Adapted from RustBelt's ContextPanel.  Displays a background image per
terrain context (overworld, settlement, ruins, combat, etc.) received via
HelionVanta.UI.Context GMCP.  Falls back to a procedural placeholder
when no asset is found.

Features kept from RustBelt:
  - Film-grain overlay (NumPy when available, pure-Python fallback)
  - Collapsible quick-command button drawer (ACTIONS / NAV tabs)
  - Corner-bracket panel styling

Context → image asset mapping (assets/ui/context/<key>.png):
  overworld      — open terrain/sky panorama
  settlement     — settlement / outpost interior
  named_location — gateway or landmark
  ruins          — ancient / industrial ruins
  dungeon        — instanced dungeon interior
  combat         — active combat scene
  void           — asteroid void / space
  road           — trade road
  impassable     — generic blocked terrain
  character      — OOC / character select screen
"""
from __future__ import annotations

import os
import random
import pygame
from theme import (
    BTN_METAL, BTN_METAL_HOV, BTN_METAL_BDR, BTN_METAL_TXT,
    GOLD_DIM, GOLD_MID, GOLD_BRIGHT,
    BG_PANEL, BG_HEADER, BORDER_BRIGHT, BORDER_DIM,
    TAB_ACTIVE, TAB_IDLE, TAB_BORDER,
    CORNER_LEN, CORNER_W,
)

# ── Film grain ────────────────────────────────────────────────────────────────
_GRAIN_INTENSITY = 10
_GRAIN_FRAMES    = 5
_GRAIN_FPS_DIV   = 3

try:
    import numpy as _np
    _NUMPY_OK = True
except ImportError:
    _np = None
    _NUMPY_OK = False


def _make_grain_frame(w: int, h: int) -> pygame.Surface:
    sw, sh = max(4, w >> 2), max(4, h >> 2)
    if _NUMPY_OK:
        gray  = _np.random.randint(0, 256, (sh, sw), dtype=_np.uint8)
        alpha = _np.random.randint(0, _GRAIN_INTENSITY + 1, (sh, sw), dtype=_np.uint8)
        rgba  = _np.zeros((sh, sw, 4), dtype=_np.uint8)
        rgba[:, :, 0] = gray
        rgba[:, :, 1] = gray
        rgba[:, :, 2] = gray
        rgba[:, :, 3] = alpha
        small = pygame.image.frombuffer(rgba.tobytes(), (sw, sh), 'RGBA').convert_alpha()
    else:
        n   = sw * sh
        rnd = os.urandom(n * 2)
        buf = bytearray(n * 4)
        for i in range(n):
            g = rnd[i]
            a = rnd[n + i] * _GRAIN_INTENSITY >> 8
            j = i * 4
            buf[j] = buf[j+1] = buf[j+2] = g
            buf[j+3] = a
        small = pygame.image.frombuffer(bytes(buf), (sw, sh), 'RGBA').convert_alpha()
    return pygame.transform.scale(small, (w, h))


# ── Button layout ─────────────────────────────────────────────────────────────
BTN_COLS  = 4
BTN_H     = 28
BTN_GAP   = 4
TOGGLE_W  = 120
TOGGLE_H  = 24
MARGIN    = 6
TAB_H     = 26

# Commands shown per context and tab.
# Format: {context: {tab_name: [(label, cmd), ...]}}
_CONTEXT_BUTTONS: dict[str, dict[str, list]] = {
    "overworld": {
        "ACTIONS": [
            ("Look",    "look"),
            ("Status",  "status"),
            ("Map",     "map"),
            ("Inv",     "inventory"),
        ],
        "NAV": [
            ("North",   "go n"),
            ("South",   "go s"),
            ("East",    "go e"),
            ("West",    "go w"),
            ("NE",      "go ne"),
            ("NW",      "go nw"),
            ("SE",      "go se"),
            ("SW",      "go sw"),
        ],
    },
    "settlement": {
        "ACTIONS": [
            ("Look",    "look"),
            ("Status",  "status"),
            ("Talk",    "say hello"),
            ("Inv",     "inventory"),
        ],
        "NAV": [
            ("Leave",   "go out"),
        ],
    },
    "named_location": {
        "ACTIONS": [
            ("Look",    "look"),
            ("Enter",   "enter"),
            ("Status",  "status"),
            ("Inv",     "inventory"),
        ],
        "NAV": [
            ("Leave",   "go out"),
        ],
    },
    "ruins": {
        "ACTIONS": [
            ("Look",    "look"),
            ("Search",  "search"),
            ("Status",  "status"),
            ("Inv",     "inventory"),
        ],
        "NAV": [
            ("North",   "go n"),
            ("South",   "go s"),
            ("East",    "go e"),
            ("West",    "go w"),
            ("Leave",   "go out"),
        ],
    },
    "combat": {
        "ACTIONS": [
            ("Look",    "look"),
            ("Attack",  "attack"),
            ("Flee",    "flee"),
            ("Status",  "status"),
        ],
        "NAV": [],
    },
    "dungeon": {
        "ACTIONS": [
            ("Look",    "look"),
            ("Search",  "search"),
            ("Status",  "status"),
            ("Inv",     "inventory"),
        ],
        "NAV": [
            ("North",   "go n"),
            ("South",   "go s"),
            ("East",    "go e"),
            ("West",    "go w"),
            ("Leave",   "go out"),
        ],
    },
    "character": {
        "ACTIONS": [
            ("Look",    "look"),
            ("Status",  "status"),
        ],
        "NAV": [],
    },
}

# Placeholder tint per context (RGB) used when no image asset is found.
_CONTEXT_TINTS = {
    "overworld":      ( 25,  40,  30),
    "settlement":     ( 30,  25,  45),
    "named_location": ( 40,  30,  55),
    "ruins":          ( 22,  20,  18),
    "dungeon":        ( 10,  10,  16),
    "combat":         ( 40,  10,  10),
    "void":           (  8,  10,  18),
    "road":           ( 25,  35,  40),
    "impassable":     ( 12,  12,  12),
    "character":      ( 12,  18,  28),
}


def _corner_brackets(surf, rect, color=BORDER_BRIGHT):
    x, y, w, h = rect.x, rect.y, rect.w, rect.h
    for (cx, cy, dx, dy) in [
        (x,     y,      1,  1), (x+w-1, y,     -1,  1),
        (x,     y+h-1,  1, -1), (x+w-1, y+h-1, -1, -1),
    ]:
        pygame.draw.line(surf, color, (cx, cy), (cx + dx*CORNER_LEN, cy), CORNER_W)
        pygame.draw.line(surf, color, (cx, cy), (cx, cy + dy*CORNER_LEN), CORNER_W)


class ContextPanel:
    """Context image panel with collapsible action button drawer."""

    def __init__(self, rect: pygame.Rect, font: pygame.font.Font, asset_manager=None):
        self.rect         = rect
        self.font         = font
        self._am          = asset_manager
        self.context      = "character"
        self.on_command   = None   # callable(cmd_str)

        # Grain
        self._grain_frames: list[pygame.Surface] = []
        self._grain_idx  = 0
        self._grain_tick = 0

        # Drawer state
        self._drawer_open  = False
        self._active_tab   = "ACTIONS"
        self._hover_toggle = False
        self._hover_logout = False
        self._btn_hover_i  = -1
        self._tab_hover    = ""
        self._btn_rects: list[pygame.Rect] = []
        self._tab_rects: dict[str, pygame.Rect] = {}
        self._toggle_rect  = pygame.Rect(0, 0, 0, 0)
        self._logout_rect  = pygame.Rect(0, 0, 0, 0)

        # Login-waiting tiled backdrop (shown before first context image)
        self._login_waiting = True
        self._active_cmds: set[str] = set()

        self._build_layout()

    # ------------------------------------------------------------------ #
    # GMCP handler
    # ------------------------------------------------------------------ #

    def on_context(self, data: dict):
        """Called when HelionVanta.UI.Context GMCP arrives."""
        new_ctx = data.get("context", "overworld")
        if new_ctx != self.context:
            self.context     = new_ctx
            self._grain_frames = []   # regenerate grain for new size
            self._active_tab  = "ACTIONS"

    # ------------------------------------------------------------------ #
    # Public helpers
    # ------------------------------------------------------------------ #

    def set_login_waiting(self, waiting: bool):
        self._login_waiting = waiting

    def set_active_cmds(self, cmds: set):
        self._active_cmds = cmds

    # ------------------------------------------------------------------ #
    # Layout
    # ------------------------------------------------------------------ #

    def _build_layout(self):
        r = self.rect
        self._toggle_rect = pygame.Rect(
            r.right - TOGGLE_W - MARGIN,
            r.bottom - TOGGLE_H - MARGIN,
            TOGGLE_W, TOGGLE_H,
        )
        self._logout_rect = pygame.Rect(
            MARGIN, r.bottom - TOGGLE_H - MARGIN,
            80, TOGGLE_H,
        )

    def _drawer_rect(self) -> pygame.Rect:
        r = self.rect
        tab_labels = self._visible_tabs()
        tab_row    = TAB_H if len(tab_labels) > 1 else 0
        btns       = self._buttons_for_tab(self._active_tab)
        rows       = (len(btns) + BTN_COLS - 1) // BTN_COLS
        h          = tab_row + rows * (BTN_H + BTN_GAP) + BTN_GAP * 2 + TOGGLE_H + MARGIN * 2
        h          = min(h, r.h - 40)
        return pygame.Rect(r.x, r.bottom - h, r.w, h)

    def _visible_tabs(self) -> list[str]:
        ctx_btns = _CONTEXT_BUTTONS.get(self.context, {})
        return [t for t, bs in ctx_btns.items() if bs]

    def _buttons_for_tab(self, tab: str) -> list[tuple[str, str]]:
        return _CONTEXT_BUTTONS.get(self.context, {}).get(tab, [])

    # ------------------------------------------------------------------ #
    # Event handling
    # ------------------------------------------------------------------ #

    def handle_event(self, event, audio=None):
        if event.type == pygame.MOUSEMOTION:
            self._hover_toggle = self._toggle_rect.collidepoint(event.pos)
            self._hover_logout = self._logout_rect.collidepoint(event.pos)
            self._btn_hover_i  = -1
            self._tab_hover    = ""
            for i, r in enumerate(self._btn_rects):
                if r.collidepoint(event.pos):
                    self._btn_hover_i = i
                    break
            for name, r in self._tab_rects.items():
                if r.collidepoint(event.pos):
                    self._tab_hover = name
                    break

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self._toggle_rect.collidepoint(event.pos):
                self._drawer_open = not self._drawer_open
                return True

            if self._hover_logout and self.on_command:
                self.on_command("_logout")
                return True

            if self._drawer_open:
                for name, r in self._tab_rects.items():
                    if r.collidepoint(event.pos):
                        self._active_tab = name
                        return True
                for i, r in enumerate(self._btn_rects):
                    if r.collidepoint(event.pos):
                        btns = self._buttons_for_tab(self._active_tab)
                        if i < len(btns):
                            _, cmd = btns[i]
                            if self.on_command:
                                self.on_command(cmd)
                        return True
        return False

    # ------------------------------------------------------------------ #
    # Draw
    # ------------------------------------------------------------------ #

    def draw(self, surface: pygame.Surface):
        r = self.rect

        # ── Background image / placeholder ────────────────────────────
        if self._login_waiting:
            self._draw_login_waiting(surface)
        else:
            img = None
            if self._am:
                img = self._am.get_context_image(self.context, size=(r.w, r.h))
            if img:
                surface.blit(img, r.topleft)
            else:
                self._draw_placeholder(surface)

        # ── Film grain overlay ────────────────────────────────────────
        self._grain_tick += 1
        if self._grain_tick % _GRAIN_FPS_DIV == 0:
            self._grain_idx = (self._grain_idx + 1) % _GRAIN_FRAMES if _GRAIN_FRAMES else 0
        if not self._grain_frames:
            self._grain_frames = [_make_grain_frame(r.w, r.h) for _ in range(_GRAIN_FRAMES or 1)]
        if self._grain_frames:
            surface.blit(self._grain_frames[self._grain_idx % len(self._grain_frames)],
                         r.topleft)

        # ── Context label ─────────────────────────────────────────────
        label_txt = self.context.replace("_", " ").upper()
        lbl = self.font.render(label_txt, True, GOLD_DIM)
        lx  = r.x + 10
        ly  = r.y + 8
        surface.blit(lbl, (lx, ly))

        # ── Toggle button ─────────────────────────────────────────────
        self._build_layout()
        tog_col = BTN_METAL_HOV if self._hover_toggle else BTN_METAL
        pygame.draw.rect(surface, tog_col, self._toggle_rect)
        pygame.draw.rect(surface, BTN_METAL_BDR, self._toggle_rect, 1)
        sym  = "▲ ACTIONS" if not self._drawer_open else "▼ ACTIONS"
        ts   = self.font.render(sym, True, BTN_METAL_TXT)
        surface.blit(ts, (self._toggle_rect.x + (self._toggle_rect.w - ts.get_width()) // 2,
                          self._toggle_rect.y + (self._toggle_rect.h - ts.get_height()) // 2))

        # ── Logout button ─────────────────────────────────────────────
        lc  = BTN_METAL_HOV if self._hover_logout else BTN_METAL
        pygame.draw.rect(surface, lc, self._logout_rect)
        pygame.draw.rect(surface, BTN_METAL_BDR, self._logout_rect, 1)
        ls  = self.font.render("LOGOUT", True, BTN_METAL_TXT)
        surface.blit(ls, (self._logout_rect.x + (self._logout_rect.w - ls.get_width()) // 2,
                          self._logout_rect.y + (self._logout_rect.h - ls.get_height()) // 2))

        # ── Drawer ────────────────────────────────────────────────────
        if self._drawer_open:
            self._draw_drawer(surface)

    # ------------------------------------------------------------------ #

    def _draw_placeholder(self, surface: pygame.Surface):
        tint = _CONTEXT_TINTS.get(self.context, (15, 20, 25))
        pygame.draw.rect(surface, tint, self.rect)
        # Simple grid overlay as visual texture
        gc = tuple(min(255, c + 8) for c in tint)
        r  = self.rect
        for gx in range(r.x, r.right, 40):
            pygame.draw.line(surface, gc, (gx, r.y), (gx, r.bottom), 1)
        for gy in range(r.y, r.bottom, 40):
            pygame.draw.line(surface, gc, (r.x, gy), (r.right, gy), 1)

    def _draw_login_waiting(self, surface: pygame.Surface):
        pygame.draw.rect(surface, (10, 14, 20), self.rect)
        cx, cy = self.rect.centerx, self.rect.centery
        title = self.font.render("HELION VANTA", True, GOLD_BRIGHT)
        sub   = self.font.render("Connecting...", True, GOLD_DIM)
        surface.blit(title, (cx - title.get_width() // 2, cy - 20))
        surface.blit(sub,   (cx - sub.get_width()   // 2, cy + 6))

    def _draw_drawer(self, surface: pygame.Surface):
        dr     = self._drawer_rect()
        tabs   = self._visible_tabs()
        tab_row = TAB_H if len(tabs) > 1 else 0

        # Drawer background
        bg = pygame.Surface((dr.w, dr.h), pygame.SRCALPHA)
        bg.fill((12, 18, 24, 220))
        surface.blit(bg, dr.topleft)
        pygame.draw.rect(surface, BORDER_DIM, dr, 1)

        # Tab strip
        self._tab_rects = {}
        if len(tabs) > 1:
            tab_w = dr.w // len(tabs)
            for i, tab_name in enumerate(tabs):
                tx  = dr.x + i * tab_w
                tr  = pygame.Rect(tx, dr.y, tab_w, TAB_H)
                col = TAB_ACTIVE if tab_name == self._active_tab else TAB_IDLE
                if tab_name == self._tab_hover:
                    col = BTN_METAL_HOV
                pygame.draw.rect(surface, col, tr)
                pygame.draw.rect(surface, TAB_BORDER, tr, 1)
                ts  = self.font.render(tab_name, True,
                                       GOLD_BRIGHT if tab_name == self._active_tab else GOLD_DIM)
                surface.blit(ts, (tr.x + (tr.w - ts.get_width()) // 2,
                                  tr.y + (tr.h - ts.get_height()) // 2))
                self._tab_rects[tab_name] = tr

        # Button grid
        btns = self._buttons_for_tab(self._active_tab)
        self._btn_rects = []
        bx = dr.x + BTN_GAP
        by = dr.y + tab_row + BTN_GAP
        btn_w = (dr.w - BTN_GAP * (BTN_COLS + 1)) // BTN_COLS

        for i, (label, cmd) in enumerate(btns):
            col_i = i % BTN_COLS
            row_i = i // BTN_COLS
            rx = bx + col_i * (btn_w + BTN_GAP)
            ry = by + row_i * (BTN_H + BTN_GAP)
            br = pygame.Rect(rx, ry, btn_w, BTN_H)
            self._btn_rects.append(br)

            active  = cmd in self._active_cmds
            hovering = (i == self._btn_hover_i)
            fill    = BTN_METAL_HOV if hovering or active else BTN_METAL
            pygame.draw.rect(surface, fill, br)
            pygame.draw.rect(surface, BTN_METAL_BDR, br, 1)
            ls = self.font.render(label, True, BTN_METAL_TXT)
            surface.blit(ls, (br.x + (br.w - ls.get_width()) // 2,
                               br.y + (br.h - ls.get_height()) // 2))
