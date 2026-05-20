"""Scrolling MUD text output + command input bar.

Ported from the Rust Belt MUD client text_panel.py with the following changes:
  - Imports updated to reference HelionVanta theme colours
  - Helm-mode banner text updated for the HelionVanta overworld (WASD movement)
  - Title/prompt strings reference Helion Vanta instead of Rust Belt

Parses ANSI/VT100 colour codes emitted by Evennia and renders each text
segment in its correct colour. Supports standard 8+8 colours, bold, reset.
Input bar has a mode selector (CMD/SAY/ACT/PM) that wraps typed text with
the appropriate MUD command before sending.
"""
import re
import pygame
from theme import BG_PANEL, BG_INPUT, BORDER_BRIGHT, BORDER_DIM, TEXT_INPUT, GOLD_DIM

_ESC_RE = re.compile(r'\x1b\[[0-9;]*[mKHJABCDsuhl]|\x1b[()][0-9A-Z]|\x1b[=>]')


def _get_clipboard() -> str:
    try:
        import pygame.scrap as scrap
        scrap.init()
        data = scrap.get(pygame.SCRAP_TEXT)
        if data:
            return data.decode('utf-8', errors='ignore').replace('\x00', '').replace('\r', '')
    except Exception:
        pass
    return ""

def _set_clipboard(text: str):
    try:
        import pygame.scrap as scrap
        scrap.init()
        scrap.put(pygame.SCRAP_TEXT, (text + '\x00').encode('utf-8'))
    except Exception:
        pass

_FG_NORMAL = {
    30: (75,  75,  70),
    31: (185, 70,  70),
    32: (70,  175, 70),
    33: (195, 170, 60),
    34: (80,  115, 215),
    35: (175, 80,  175),
    36: (60,  185, 185),
    37: (210, 210, 205),
}
_FG_BRIGHT = {
    90: (130, 130, 125),
    91: (235, 105, 105),
    92: (105, 235, 105),
    93: (235, 235, 105),
    94: (115, 155, 245),
    95: (235, 115, 235),
    96: (105, 235, 235),
    97: (255, 255, 255),
}
_BOLD_UP = {30: 90, 31: 91, 32: 92, 33: 93, 34: 94, 35: 95, 36: 96, 37: 97}
DEFAULT_COLOR = (190, 220, 215)


def _brighten(c, f=1.25):
    return tuple(min(255, int(x * f)) for x in c)


def parse_ansi(text: str):
    """Return list of (segment_str, rgb_color) from an ANSI-encoded line."""
    segments = []
    pos = 0
    cur = DEFAULT_COLOR
    bold = False

    for m in _ESC_RE.finditer(text):
        if m.start() > pos:
            chunk = text[pos:m.start()]
            if chunk:
                segments.append((chunk, cur))
        pos = m.end()

        if not m.group().endswith('m'):
            continue

        inner = m.group()[2:-1]
        codes = [int(c) for c in inner.split(';') if c.isdigit()] if inner else [0]
        for code in codes:
            if code == 0:
                cur = DEFAULT_COLOR; bold = False
            elif code == 1:
                bold = True
                if cur != DEFAULT_COLOR:
                    cur = _brighten(cur)
            elif code == 22:
                bold = False
            elif 30 <= code <= 37:
                cur = _FG_BRIGHT[_BOLD_UP[code]] if bold else _FG_NORMAL[code]
            elif 90 <= code <= 97:
                cur = _FG_BRIGHT[code]
            elif code == 39:
                cur = DEFAULT_COLOR

    tail = text[pos:]
    if tail:
        segments.append((tail, cur))
    return segments or [('', DEFAULT_COLOR)]


_SEL_COLOR = (40, 110, 130, 90)

_MODES      = ("command", "say", "action", "local", "pm")
_MODE_LABEL = {"command": "CMD", "say": "SAY", "action": "ACT", "pm": "PM", "local": "LCL"}
_MODE_COLOR = {
    "command": (80,  200, 190),
    "say":     (70,  200, 90),
    "action":  (200, 180, 55),
    "pm":      (180, 80,  200),
    "local":   (0,   210, 210),
}
MODE_BTN_W      = 55
DROPDOWN_W      = 130
DROPDOWN_ITEM_H = 22


class TextPanel:
    LINE_HEIGHT = 17
    MAX_LINES   = 600

    def __init__(self, rect: pygame.Rect, font: pygame.font.Font,
                 asset_manager=None):
        self.rect           = rect
        self.font           = font
        self._am            = asset_manager
        self._lines: list   = []
        self._scroll_offset = 0
        self._input_text    = ""
        self.on_submit      = None
        self.on_keypress    = None
        # Text selection
        self._sel_anchor    = None
        self._sel_cursor    = None
        self._selecting     = False
        # Input mode
        self._input_mode    = "command"
        self._pm_target     = ""
        self._mode_open     = False
        self._mode_hover    = -1
        # Background cache
        self._bg_cache: pygame.Surface | None = None
        self._bg_size: tuple[int, int] | None = None
        # WASD helm mode (overworld movement shortcut)
        self._helm_mode = False

    # ------------------------------------------------------------------ #
    # Geometry
    # ------------------------------------------------------------------ #

    def _input_h(self):
        return self.font.get_height() + 10

    def _content_rect(self):
        ih = self._input_h()
        return pygame.Rect(self.rect.x + 1, self.rect.y + 1,
                           self.rect.w - 2, self.rect.h - ih - 3)

    def _input_rect(self):
        ih = self._input_h()
        return pygame.Rect(self.rect.x, self.rect.bottom - ih, self.rect.w, ih)

    def _mode_btn_rect(self):
        ir = self._input_rect()
        return pygame.Rect(ir.right - MODE_BTN_W, ir.y, MODE_BTN_W, ir.h)

    def _text_field_rect(self):
        ir = self._input_rect()
        return pygame.Rect(ir.x, ir.y, ir.w - MODE_BTN_W, ir.h)

    def _dropdown_rect(self):
        mbr    = self._mode_btn_rect()
        total_h = DROPDOWN_ITEM_H * len(_MODES)
        return pygame.Rect(mbr.right - DROPDOWN_W, mbr.y - total_h, DROPDOWN_W, total_h)

    def _visible_range(self):
        tr      = self._content_rect()
        visible = tr.height // self.LINE_HEIGHT
        end_idx = max(0, len(self._lines) - self._scroll_offset)
        start_idx = max(0, end_idx - visible)
        return start_idx, end_idx, visible

    def _y_to_abs_line(self, y):
        tr = self._content_rect()
        start_idx, _, _ = self._visible_range()
        row = (y - tr.y - 3) // self.LINE_HEIGHT
        return max(0, min(start_idx + row, len(self._lines) - 1))

    def _sel_text(self):
        if self._sel_anchor is None or self._sel_cursor is None:
            return ""
        lo = max(0, min(self._sel_anchor, self._sel_cursor))
        hi = min(len(self._lines) - 1, max(self._sel_anchor, self._sel_cursor))
        return "\n".join(
            "".join(seg for seg, _ in self._lines[i])
            for i in range(lo, hi + 1)
        )

    # ------------------------------------------------------------------ #
    # Word wrap
    # ------------------------------------------------------------------ #

    def _wrap_segments(self, segments, max_w):
        lines = []
        cur   = []
        cur_w = 0

        for seg_text, color in segments:
            i = 0
            while i < len(seg_text):
                if seg_text[i] == ' ':
                    token = ' '
                    i += 1
                else:
                    j = seg_text.find(' ', i)
                    if j == -1:
                        token = seg_text[i:]
                        i = len(seg_text)
                    else:
                        token = seg_text[i:j]
                        i = j

                if token == ' ' and cur_w == 0:
                    continue

                token_w = self.font.size(token)[0]

                if token != ' ' and cur_w + token_w > max_w and cur:
                    lines.append(cur)
                    cur   = []
                    cur_w = 0

                if cur and cur[-1][1] == color:
                    cur[-1] = (cur[-1][0] + token, color)
                else:
                    cur.append((token, color))
                cur_w += token_w

        if cur:
            lines.append(cur)
        return lines if lines else [[('', DEFAULT_COLOR)]]

    # ------------------------------------------------------------------ #
    # Data
    # ------------------------------------------------------------------ #

    def append(self, raw: str):
        max_w = self.rect.w - 14
        for part in raw.replace('\r', '').split('\n'):
            segs    = parse_ansi(part)
            wrapped = self._wrap_segments(segs, max_w)
            self._lines.extend(wrapped)
        if len(self._lines) > self.MAX_LINES:
            self._lines = self._lines[-self.MAX_LINES:]

    # ------------------------------------------------------------------ #
    # Input mode helpers
    # ------------------------------------------------------------------ #

    def _prompt_prefix(self):
        if self._input_mode == "say":
            return "SAY  "
        if self._input_mode == "action":
            return "ACT  "
        if self._input_mode == "local":
            return "LCL  "
        if self._input_mode == "pm":
            if not self._pm_target:
                return "PM to: "
            return f"PM → {self._pm_target}  "
        return "> "

    def _submit_input(self, text):
        if not self.on_submit:
            return
        mode = self._input_mode
        if mode == "say":
            if text:
                self.on_submit(f"say {text}")
        elif mode == "action":
            if text:
                self.on_submit(f"emote {text}")
        elif mode == "local":
            if text:
                self.on_submit(f"local {text}")
        elif mode == "pm":
            if not self._pm_target:
                self._pm_target = text
                return
            else:
                if text:
                    self.on_submit(f"page {self._pm_target}={text}")
                self._pm_target = ""
        else:
            if text:
                self.on_submit(text)

    def _visible_input_text(self, max_w):
        full = self._input_text + "█"
        if self.font.size(full)[0] <= max_w:
            return full
        lo, hi = 1, len(full)
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if self.font.size(full[-mid:])[0] <= max_w:
                lo = mid
            else:
                hi = mid - 1
        return full[-lo:]

    def has_input(self) -> bool:
        return bool(self._input_text)

    def set_helm_mode(self, active: bool):
        self._helm_mode = bool(active)
        if not active:
            self._input_text = ""

    # ------------------------------------------------------------------ #
    # Events
    # ------------------------------------------------------------------ #

    def handle_event(self, event):
        tr = self._content_rect()

        if event.type == pygame.KEYDOWN and self._helm_mode:
            return

        if event.type == pygame.KEYDOWN:
            mods = pygame.key.get_mods()
            if mods & pygame.KMOD_CTRL:
                if event.key == pygame.K_v:
                    self._input_text += _get_clipboard()
                    return
                elif event.key == pygame.K_c:
                    sel = self._sel_text()
                    _set_clipboard(sel if sel else self._input_text)
                    return
                elif event.key == pygame.K_a:
                    self._sel_anchor = 0
                    self._sel_cursor = len(self._lines) - 1
                    return

            self._sel_anchor = self._sel_cursor = None

            k = event.key
            if k == pygame.K_RETURN:
                cmd = self._input_text.strip()
                self._input_text = ""
                self._submit_input(cmd)
            elif k == pygame.K_BACKSPACE:
                if not self._input_text and self._input_mode == "pm" and self._pm_target:
                    self._pm_target = ""
                else:
                    self._input_text = self._input_text[:-1]
            elif k == pygame.K_ESCAPE:
                if self._mode_open:
                    self._mode_open = False
                elif self._input_mode == "pm" and self._pm_target:
                    self._pm_target = ""
                else:
                    self._input_mode = "command"
                    self._pm_target  = ""
            elif k == pygame.K_UP:
                self._scroll_offset = min(self._scroll_offset + 3,
                                          max(0, len(self._lines) - 1))
            elif k == pygame.K_DOWN:
                self._scroll_offset = max(self._scroll_offset - 3, 0)
            elif k == pygame.K_PAGEUP:
                self._scroll_offset = min(self._scroll_offset + 10,
                                          max(0, len(self._lines) - 1))
            elif k == pygame.K_PAGEDOWN:
                self._scroll_offset = max(self._scroll_offset - 10, 0)
            elif event.unicode and event.unicode.isprintable():
                self._input_text += event.unicode
                if self.on_keypress:
                    self.on_keypress()

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos

            if self._mode_open:
                dr = self._dropdown_rect()
                if dr.collidepoint(pos):
                    item = (pos[1] - dr.y) // DROPDOWN_ITEM_H
                    if 0 <= item < len(_MODES):
                        new_mode = _MODES[item]
                        if new_mode != self._input_mode:
                            self._input_mode = new_mode
                            self._pm_target  = ""
                            self._input_text = ""
                self._mode_open  = False
                self._mode_hover = -1
                return

            mbr = self._mode_btn_rect()
            if mbr.collidepoint(pos):
                self._mode_open = not self._mode_open
                return

            if tr.collidepoint(pos):
                self._sel_anchor = self._y_to_abs_line(pos[1])
                self._sel_cursor = self._sel_anchor
                self._selecting  = True

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self._selecting = False

        elif event.type == pygame.MOUSEMOTION:
            pos = event.pos
            if self._mode_open:
                dr = self._dropdown_rect()
                self._mode_hover = (pos[1] - dr.y) // DROPDOWN_ITEM_H if dr.collidepoint(pos) else -1
            if self._selecting and tr.collidepoint(pos):
                self._sel_cursor = self._y_to_abs_line(pos[1])

        elif event.type == pygame.MOUSEWHEEL:
            if self.rect.collidepoint(pygame.mouse.get_pos()):
                self._scroll_offset = max(0, min(
                    self._scroll_offset + event.y * 2,
                    max(0, len(self._lines) - 1),
                ))

    # ------------------------------------------------------------------ #
    # Draw
    # ------------------------------------------------------------------ #

    def _build_bg_cache(self):
        size = (self.rect.w, self.rect.h)
        bg = pygame.Surface(size).convert()
        bg.fill(BG_PANEL)
        self._bg_cache = bg
        self._bg_size  = size

    def draw(self, surface: pygame.Surface):
        if self._bg_size != (self.rect.w, self.rect.h) or self._bg_cache is None:
            self._build_bg_cache()
        surface.blit(self._bg_cache, self.rect.topleft)
        pygame.draw.rect(surface, BORDER_BRIGHT, self.rect, 1)

        text_rect = self._content_rect()
        start_idx, end_idx, _ = self._visible_range()

        has_sel = (self._sel_anchor is not None and
                   self._sel_cursor  is not None and
                   self._sel_anchor  != self._sel_cursor)
        if has_sel:
            sel_lo   = min(self._sel_anchor, self._sel_cursor)
            sel_hi   = max(self._sel_anchor, self._sel_cursor)
            sel_surf = pygame.Surface((text_rect.w, self.LINE_HEIGHT), pygame.SRCALPHA)
            sel_surf.fill(_SEL_COLOR)
            for abs_i in range(max(sel_lo, start_idx), min(sel_hi + 1, end_idx)):
                row = abs_i - start_idx
                sy  = text_rect.y + row * self.LINE_HEIGHT + 3
                surface.blit(sel_surf, (text_rect.x, sy))

        for row, segments in enumerate(self._lines[start_idx:end_idx]):
            x = text_rect.x + 6
            y = text_rect.y + row * self.LINE_HEIGHT + 3
            for seg_text, color in segments:
                if not seg_text:
                    continue
                try:
                    surf = self.font.render(seg_text, True, color)
                    surface.blit(surf, (x, y))
                    x += surf.get_width()
                except Exception:
                    pass

        if self._scroll_offset > 0:
            msg = self.font.render(
                f"  ↑ {self._scroll_offset} lines back  (↓/PgDn to return)",
                True, (60, 130, 120),
            )
            surface.blit(msg, (text_rect.x + 6, text_rect.y + 3))

        if has_sel:
            count = abs(self._sel_cursor - self._sel_anchor) + 1
            hint = self.font.render(
                f"  {count} line{'s' if count != 1 else ''} selected — Ctrl+C to copy",
                True, GOLD_DIM,
            )
            surface.blit(hint, (text_rect.x + 6, text_rect.bottom - self.LINE_HEIGHT - 2))

        # ── Input bar ────────────────────────────────────────────────────
        tfr = self._text_field_rect()
        mbr = self._mode_btn_rect()

        if self._helm_mode:
            pygame.draw.rect(surface, (8, 24, 30), tfr)
            pygame.draw.line(surface, (0, 180, 180), tfr.topleft, tfr.topright, 1)
            banner = self.font.render(
                "TRAVEL MODE  ·  WASD to move  ·  ESC to exit",
                True, (0, 210, 210),
            )
            surface.blit(banner, (tfr.x + 8, tfr.y + (tfr.h - banner.get_height()) // 2))
            pygame.draw.rect(surface, (8, 24, 30), mbr)
            pygame.draw.line(surface, (0, 180, 180), mbr.topleft, mbr.topright, 1)
            pygame.draw.line(surface, (0, 120, 120), mbr.topleft, mbr.bottomleft, 1)
            hlm = self.font.render("TRAVEL", True, (0, 210, 210))
            surface.blit(hlm, (mbr.x + (mbr.w - hlm.get_width()) // 2,
                                mbr.y + (mbr.h - hlm.get_height()) // 2))
        else:
            mc  = _MODE_COLOR[self._input_mode]
            pygame.draw.rect(surface, BG_INPUT, tfr)
            pygame.draw.line(surface, BORDER_BRIGHT, tfr.topleft, tfr.topright, 1)

            prefix   = self._prompt_prefix()
            pre_surf = self.font.render(prefix, True, mc)
            px = tfr.x + 8
            py = tfr.y + 4
            surface.blit(pre_surf, (px, py))

            available_w = tfr.w - 8 - pre_surf.get_width() - 4
            vis_text    = self._visible_input_text(available_w)
            txt_surf    = self.font.render(vis_text, True, TEXT_INPUT)
            surface.blit(txt_surf, (px + pre_surf.get_width(), py))

            pygame.draw.rect(surface, (14, 20, 28), mbr)
            pygame.draw.line(surface, BORDER_BRIGHT, mbr.topleft, mbr.topright, 1)
            pygame.draw.line(surface, BORDER_DIM,    mbr.topleft, mbr.bottomleft, 1)
            lbl_surf = self.font.render(_MODE_LABEL[self._input_mode], True, mc)
            surface.blit(lbl_surf, (mbr.x + (mbr.w - lbl_surf.get_width()) // 2,
                                     mbr.y + (mbr.h - lbl_surf.get_height()) // 2))

        if self._mode_open:
            dr  = self._dropdown_rect()
            bg  = pygame.Surface((dr.w, dr.h), pygame.SRCALPHA)
            bg.fill((10, 18, 24, 240))
            surface.blit(bg, dr.topleft)
            pygame.draw.rect(surface, BORDER_BRIGHT, dr, 1)

            for i, mode in enumerate(_MODES):
                item_r = pygame.Rect(dr.x, dr.y + i * DROPDOWN_ITEM_H, dr.w, DROPDOWN_ITEM_H)
                if i == self._mode_hover:
                    hov = pygame.Surface((dr.w, DROPDOWN_ITEM_H), pygame.SRCALPHA)
                    hov.fill((20, 50, 55, 200))
                    surface.blit(hov, item_r.topleft)
                col = _MODE_COLOR[mode]
                if mode == self._input_mode:
                    col = tuple(min(255, c + 70) for c in col)
                label_text = f"{_MODE_LABEL[mode]}  {mode.capitalize()}"
                ls = self.font.render(label_text, True, col)
                surface.blit(ls, (item_r.x + 8,
                                  item_r.y + (DROPDOWN_ITEM_H - ls.get_height()) // 2))
