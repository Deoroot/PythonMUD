"""Login panel overlay — shown before connection is established.

Host and port are baked into assets/config.json (server.host / server.port).
This panel collects only username + password.

Calls on_connect(username, password, remember) when the user submits.

Adapted from the Rust Belt MUD client login_panel.py:
  - Title changed to HELION VANTA
  - Background darkened to match HelionVanta deep-space palette
  - All colour tokens updated to HelionVanta theme
"""
import pygame
from theme import (BG_PANEL, BG_INPUT, BORDER_BRIGHT, BORDER_DIM,
                   TEXT_INPUT, GOLD_DIM, GOLD_MID,
                   BTN_METAL, BTN_METAL_HOV, BTN_METAL_BDR, BTN_METAL_TXT)

PANEL_W   = 420
PANEL_H   = 260
FIELD_H   = 28
FIELD_GAP = 10
LBL_W     = 90
BTN_H     = 30


def _tile(surface: pygame.Surface, image: pygame.Surface, rect: pygame.Rect):
    iw, ih = image.get_size()
    old_clip = surface.get_clip()
    surface.set_clip(rect)
    for tx in range(rect.x, rect.right + iw, iw):
        for ty in range(rect.y, rect.bottom + ih, ih):
            surface.blit(image, (tx, ty))
    surface.set_clip(old_clip)


class LoginPanel:
    """Centered login overlay. draw() every frame; handle_event() for input."""

    def __init__(self, screen_w: int, screen_h: int, font: pygame.font.Font,
                 saved_username: str = "", asset_manager=None):
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.font     = font
        self.visible  = True

        self.on_connect = None   # callable(username, password, remember)

        px = (screen_w - PANEL_W) // 2
        py = (screen_h - PANEL_H) // 2
        self.rect = pygame.Rect(px, py, PANEL_W, PANEL_H)

        self._fields      = {"username": saved_username, "password": ""}
        self._field_order = ["username", "password"]
        self._focused     = "username"
        self._remember    = bool(saved_username)
        self._status      = ""
        self._status_col  = GOLD_DIM
        self._btn_hover   = False
        self._am          = asset_manager

        self._field_rects: dict[str, pygame.Rect] = {}
        self._btn_rect  = pygame.Rect(0, 0, 0, 0)
        self._chk_rect  = pygame.Rect(0, 0, 0, 0)
        self._build_rects()

    def _build_rects(self):
        x0 = self.rect.x + 20 + LBL_W + 8
        iw = self.rect.w - 20 - LBL_W - 8 - 20
        y  = self.rect.y + 60
        for key in self._field_order:
            self._field_rects[key] = pygame.Rect(x0, y, iw, FIELD_H)
            y += FIELD_H + FIELD_GAP
        y += 6
        self._chk_rect = pygame.Rect(x0, y + 4, 16, 16)
        y += 34
        self._btn_rect = pygame.Rect(self.rect.x + 20, y,
                                     self.rect.w - 40, BTN_H)

    def set_status(self, msg: str, error: bool = False):
        self._status     = msg
        self._status_col = (200, 70, 70) if error else GOLD_DIM

    # ------------------------------------------------------------------ #

    def handle_event(self, event) -> bool:
        if not self.visible:
            return False

        if event.type == pygame.KEYDOWN:
            k = event.key
            if k == pygame.K_TAB:
                idx = self._field_order.index(self._focused)
                self._focused = self._field_order[(idx + 1) % len(self._field_order)]
                return True
            if k == pygame.K_RETURN:
                self._submit(); return True
            if k == pygame.K_BACKSPACE:
                self._fields[self._focused] = self._fields[self._focused][:-1]
                return True
            if event.unicode and event.unicode.isprintable():
                self._fields[self._focused] += event.unicode
                return True

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
            if not self.rect.collidepoint(pos):
                return True
            for key, r in self._field_rects.items():
                if r.collidepoint(pos):
                    self._focused = key; return True
            if self._chk_rect.inflate(8, 8).collidepoint(pos):
                self._remember = not self._remember; return True
            if self._btn_rect.collidepoint(pos):
                self._submit(); return True

        elif event.type == pygame.MOUSEMOTION:
            self._btn_hover = self._btn_rect.collidepoint(event.pos)

        return self.visible

    def _submit(self):
        user = self._fields["username"].strip()
        pw   = self._fields["password"]
        if not user:
            self.set_status("Username is required.", error=True); return
        self.set_status("Connecting\u2026")
        if self.on_connect:
            self.on_connect(user, pw, self._remember)

    # ------------------------------------------------------------------ #

    def resize(self, screen_w: int, screen_h: int):
        self.screen_w = screen_w
        self.screen_h = screen_h
        px = (screen_w - PANEL_W) // 2
        py = (screen_h - PANEL_H) // 2
        self.rect = pygame.Rect(px, py, PANEL_W, PANEL_H)
        self._build_rects()

    def draw(self, surface: pygame.Surface):
        if not self.visible:
            return

        sw, sh = surface.get_size()
        dim = pygame.Surface((sw, sh), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 175))
        surface.blit(dim, (0, 0))

        pygame.draw.rect(surface, (8, 14, 20), self.rect)
        # Optional tiled texture background (config key: login_panel_bg)
        if self._am:
            bg = self._am.get_ui_element("login_panel_bg")
            if bg:
                _tile(surface, bg, self.rect)
                drk = pygame.Surface((self.rect.w, self.rect.h), pygame.SRCALPHA)
                drk.fill((0, 6, 12, 175))
                surface.blit(drk, self.rect.topleft)
        pygame.draw.rect(surface, BORDER_BRIGHT, self.rect, 1)

        title = self.font.render("HELION VANTA", True, GOLD_MID)
        surface.blit(title, (self.rect.centerx - title.get_width() // 2,
                              self.rect.y + 18))
        pygame.draw.line(surface, BORDER_DIM,
                         (self.rect.x + 20, self.rect.y + 46),
                         (self.rect.right - 20, self.rect.y + 46), 1)

        labels = {"username": "Account", "password": "Password"}
        for key in self._field_order:
            r       = self._field_rects[key]
            focused = (self._focused == key)
            ls = self.font.render(labels[key], True, GOLD_MID if focused else GOLD_DIM)
            surface.blit(ls, (self.rect.x + 20 + LBL_W - ls.get_width(),
                               r.y + (r.h - ls.get_height()) // 2))
            pygame.draw.rect(surface, BG_INPUT, r)
            pygame.draw.rect(surface, GOLD_MID if focused else BORDER_DIM, r, 1)
            val     = self._fields[key]
            display = ("*" * len(val)) if key == "password" else val
            ts = self.font.render(display + ("\u2588" if focused else ""), True, TEXT_INPUT)
            surface.set_clip(r.inflate(-2, -2))
            surface.blit(ts, (r.x + 6, r.y + (r.h - ts.get_height()) // 2))
            surface.set_clip(None)

        # Checkbox
        pygame.draw.rect(surface, BG_INPUT, self._chk_rect)
        pygame.draw.rect(surface, BORDER_DIM, self._chk_rect, 1)
        if self._remember:
            pygame.draw.line(surface, GOLD_MID,
                             (self._chk_rect.x + 3, self._chk_rect.centery),
                             (self._chk_rect.centerx, self._chk_rect.bottom - 4), 2)
            pygame.draw.line(surface, GOLD_MID,
                             (self._chk_rect.centerx, self._chk_rect.bottom - 4),
                             (self._chk_rect.right - 2, self._chk_rect.y + 4), 2)
        cl = self.font.render("Remember me", True, GOLD_DIM)
        surface.blit(cl, (self._chk_rect.right + 8,
                           self._chk_rect.y + (self._chk_rect.h - cl.get_height()) // 2))

        # Connect button
        btn_s = pygame.Surface((self._btn_rect.w, self._btn_rect.h), pygame.SRCALPHA)
        btn_s.fill((*( BTN_METAL_HOV if self._btn_hover else BTN_METAL), 230))
        surface.blit(btn_s, self._btn_rect.topleft)
        pygame.draw.rect(surface, BTN_METAL_BDR, self._btn_rect, 1)
        bevel = (min(255, BTN_METAL_BDR[0]+40), min(255, BTN_METAL_BDR[1]+35),
                 min(255, BTN_METAL_BDR[2]+20))
        pygame.draw.line(surface, bevel,
                         self._btn_rect.topleft, (self._btn_rect.right - 1, self._btn_rect.top), 1)
        bl = self.font.render("CONNECT", True, BTN_METAL_TXT)
        surface.blit(bl, (self._btn_rect.centerx - bl.get_width() // 2,
                           self._btn_rect.centery - bl.get_height() // 2))

        if self._status:
            ss = self.font.render(self._status, True, self._status_col)
            surface.blit(ss, (self.rect.centerx - ss.get_width() // 2,
                               self._btn_rect.bottom + 10))
