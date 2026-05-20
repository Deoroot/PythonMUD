"""Helion Vanta MUD Client — entry point.

Layout (1280x800):
  ┌──────────────────────────────┬───────────────────┐
  │  Context image + buttons     │  Character status │
  │  (left_w × top_h)            ├───────────────────┤
  │                              │  Overworld map    │
  ├──────────────────────────────┴───────────────────┤
  │  MUD text + command input  (full width, 300px)   │
  └──────────────────────────────────────────────────┘
  [Tab] toggles WASD travel mode on the overworld

Run: python main.py [--host HOST] [--port PORT] [--no-sounds] [--no-music]
  Host/port default to assets/config.json server section (localhost:4000 if absent).
"""
import sys
import os
import argparse
import re
import time
import traceback
import pygame

# ── Crash log ─────────────────────────────────────────────────────────────
_CRASH_LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "crash.log")


def _write_crash(exc_type, exc_value, exc_tb):
    lines = ["=" * 60 + "\n",
             f"CRASH  {time.strftime('%Y-%m-%d %H:%M:%S')}\n",
             "=" * 60 + "\n"]
    lines += traceback.format_exception(exc_type, exc_value, exc_tb)
    try:
        with open(_CRASH_LOG, "a", encoding="utf-8") as f:
            f.writelines(lines)
        print(f"\n[CRASH] Traceback written to {_CRASH_LOG}", flush=True)
    except Exception:
        pass
    sys.__excepthook__(exc_type, exc_value, exc_tb)


sys.excepthook = _write_crash

import paths as _paths
import auth
from asset_manager import AssetManager
from connection import HelionVantaConnection
from audio import AudioManager
from panels.text_panel import TextPanel
from panels.char_panel import CharPanel
from panels.map_panel import MapPanel
from panels.context_panel import ContextPanel
from panels.login_panel import LoginPanel
from theme import (BG_DEEP, BG_PANEL, BORDER_BRIGHT, GOLD_DIM, GOLD_MID,
                   BTN_METAL, BTN_METAL_HOV, BTN_METAL_BDR, BTN_METAL_TXT,
                   TAB_ACTIVE, TAB_IDLE, TAB_BORDER)

_ASSETS_DIR          = _paths.assets_dir()
_WRITABLE_ASSETS_DIR = _paths.writable_assets_dir()

WIDTH   = 1280
HEIGHT  = 800
TEXT_H  = 300
RIGHT_W = 380
CHAR_H  = 175      # character status panel height (top of right column)
MUTE_BTN_W = 64

# Contexts where WASD overworld travel is active
_WASD_CONTEXTS = frozenset({"overworld", "void", "road", "ruins", "named_location"})

# Context → music track fallback mapping
_CONTEXT_MUSIC = {
    "character":     "mainmenu",
    "overworld":     "overworld_ambient",
    "void":          "void_ambient",
    "settlement":    "settlement",
    "named_location":"named_location",
    "ruins":         "ruins_ambient",
    "dungeon":       "dungeon",
    "combat":        "combat",
    "road":          "overworld_ambient",
    "impassable":    "overworld_ambient",
}

_WASD_MAP = {
    pygame.K_w: "n", pygame.K_s: "s",
    pygame.K_a: "w", pygame.K_d: "e",
}

_MOVE_RATE = 2.3   # seconds between WASD moves (server enforces ~2.5 s cooldown)

# Mute cycle states
_MUTE_LABELS = {0: "SND:ON", 1: "SFX:XX", 2: "MUS:XX", 3: "MUTED!"}
_MUTE_COLORS = {
    0: GOLD_MID,
    1: (200, 140, 70),
    2: (200, 140, 70),
    3: (200, 70,  70),
}


# ── Layout ─────────────────────────────────────────────────────────────────

def build_rects(w: int = WIDTH, h: int = HEIGHT) -> dict:
    top_h  = h - TEXT_H
    left_w = w - RIGHT_W
    map_y  = CHAR_H
    map_h  = max(80, top_h - CHAR_H)
    return {
        "context": pygame.Rect(0,       0,      left_w,  top_h),
        "char":    pygame.Rect(left_w,  0,      RIGHT_W, CHAR_H),
        "map":     pygame.Rect(left_w,  map_y,  RIGHT_W, map_h),
        "text":    pygame.Rect(0,       top_h,  w,       TEXT_H),
        "mute":    pygame.Rect(w - 4 - MUTE_BTN_W, top_h - CHAR_H // 2 - 13,
                               MUTE_BTN_W, 26),
    }


# ── Font loading ───────────────────────────────────────────────────────────

_MONO_FONTS = ["Consolas", "DejaVu Sans Mono", "Liberation Mono",
               "Courier New", "monospace"]


def _load_font(size: int, bold: bool = False) -> pygame.font.Font:
    for fname in ("HelionVanta.ttf", "font.ttf"):
        p = os.path.join(_ASSETS_DIR, "ui", fname)
        if os.path.exists(p):
            try:
                return pygame.font.Font(p, size)
            except Exception:
                pass
    for name in _MONO_FONTS:
        try:
            f = pygame.font.SysFont(name, size, bold=bold)
            if f:
                return f
        except Exception:
            pass
    return pygame.font.Font(None, size)


# ── Boot screen ────────────────────────────────────────────────────────────

def _show_boot_screen(screen: pygame.Surface, font: pygame.font.Font,
                      boot_log: list, w: int, h: int):
    clock   = pygame.time.Clock()
    start   = pygame.time.get_ticks()
    TIMEOUT = 2200

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                return

        elapsed = pygame.time.get_ticks() - start
        screen.fill((4, 8, 12))

        y = 28
        hdr = font.render("HELION VANTA  —  ASSET FILESYSTEM", True, (50, 180, 155))
        screen.blit(hdr, (40, y)); y += 20
        pygame.draw.line(screen, (18, 65, 58), (40, y), (w - 40, y), 1); y += 10

        for line in boot_log:
            lo = line.lstrip()
            if lo.startswith("+ "):
                col = (70, 200, 90)
            elif lo.startswith("! "):
                col = (210, 80, 80)
            elif lo.startswith("---"):
                col = (40, 150, 130); y += 4
            elif lo.startswith("(no"):
                col = (80, 170, 150)
            else:
                col = (80, 120, 115)
            s = font.render(line, True, col)
            screen.blit(s, (40, y)); y += 17

        remaining_s = max(1, (TIMEOUT - elapsed) // 1000 + 1)
        hint = font.render(f"Press any key to continue  [{remaining_s}]",
                            True, (40, 60, 55))
        screen.blit(hint, (40, h - 30))
        pygame.display.flip()
        clock.tick(30)

        if elapsed >= TIMEOUT:
            return


# ── Mute button draw ───────────────────────────────────────────────────────

def _draw_mute_btn(surface, rect, font, state, hover):
    fill = TAB_ACTIVE if hover else TAB_IDLE
    pygame.draw.rect(surface, fill, rect)
    pygame.draw.rect(surface, TAB_BORDER, rect, 1)
    col = BTN_METAL_TXT if hover else _MUTE_COLORS[state]
    lbl = font.render(_MUTE_LABELS[state], True, col)
    surface.blit(lbl, (rect.x + (rect.w - lbl.get_width()) // 2,
                        rect.y + (rect.h - lbl.get_height()) // 2))


def _apply_mute(state, audio):
    audio.set_sounds_enabled(state not in (1, 3))
    audio.set_music_enabled(state not in (2, 3))


# ── Main ───────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Helion Vanta MUD Client")
    parser.add_argument("--host",      default=None)
    parser.add_argument("--port",      type=int, default=None)
    parser.add_argument("--no-sounds", action="store_true")
    parser.add_argument("--no-music",  action="store_true")
    args = parser.parse_args()

    print("=" * 60, flush=True)
    print("  HELION VANTA MUD CLIENT  starting up", flush=True)
    print(f"  pygame {pygame.version.ver}  |  python {sys.version.split()[0]}", flush=True)
    print("=" * 60, flush=True)

    pygame.init()
    pygame.key.set_repeat(400, 45)
    _win_size = [WIDTH, HEIGHT]
    screen = pygame.display.set_mode((_win_size[0], _win_size[1]), pygame.RESIZABLE)
    pygame.display.set_caption("Helion Vanta MUD")

    _icon_path = os.path.join(_ASSETS_DIR, "ui", "icon.png")
    if os.path.exists(_icon_path):
        try:
            pygame.display.set_icon(pygame.image.load(_icon_path))
        except Exception:
            pass

    clock      = pygame.time.Clock()
    font       = _load_font(13)
    font_small = _load_font(11)

    rects = build_rects(_win_size[0], _win_size[1])

    # ── Asset system ────────────────────────────────────────────────────
    am = AssetManager(_ASSETS_DIR, writable_assets_dir=_WRITABLE_ASSETS_DIR)

    _cursor_data = am.open_file("ui/cursor.png")
    if _cursor_data:
        try:
            cur_surf = pygame.image.load(_cursor_data).convert_alpha()
            cur_surf = pygame.transform.smoothscale(cur_surf, (64, 64))
            pygame.mouse.set_cursor(pygame.Cursor((0, 0), cur_surf))
        except Exception as exc:
            print(f"[cursor] {exc}", flush=True)

    _show_boot_screen(screen, font, am.boot_log, _win_size[0], _win_size[1])
    for line in am.boot_log:
        print(line, flush=True)

    _srv  = am.load_config().get("server", {})
    _host = args.host or _srv.get("host", "localhost")
    _port = args.port or _srv.get("port", 4000)
    print(f"  Server target: {_host}:{_port}", flush=True)

    # ── Panels ──────────────────────────────────────────────────────────
    context_panel = ContextPanel(rects["context"], font, asset_manager=am)
    context_panel.on_context({"context": "character"})
    char_panel    = CharPanel(rects["char"],    font_small)
    map_panel     = MapPanel(rects["map"],      font_small)
    text_panel    = TextPanel(rects["text"],    font,       asset_manager=am)

    for line in am.boot_log:
        text_panel.append(line)
    text_panel.append(f"  Server: {_host}:{_port}")
    text_panel.append("")

    # ── State ───────────────────────────────────────────────────────────
    _mute_hover  = [False]
    _mute_state  = [0]
    _helm_mode   = [False]
    _last_move_t = [0.0]

    if args.no_sounds and args.no_music:
        _mute_state[0] = 3
    elif args.no_sounds:
        _mute_state[0] = 1
    elif args.no_music:
        _mute_state[0] = 2

    def _apply_rects(new_rects: dict):
        rects.update(new_rects)
        context_panel.rect = rects["context"]
        context_panel._build_layout()
        char_panel.rect    = rects["char"]
        map_panel.rect     = rects["map"]
        text_panel.rect    = rects["text"]
        try:
            login_panel.resize(_win_size[0], _win_size[1])
        except NameError:
            pass

    def _set_helm_mode(active: bool):
        _helm_mode[0] = active
        text_panel.set_helm_mode(active)
        context_panel.set_active_cmds({"_helm_toggle"} if active else set())

    audio = AudioManager(asset_manager=am)
    _apply_mute(_mute_state[0], audio)
    audio.play_music("mainmenu")

    conn = HelionVantaConnection(_host, _port)

    def _on_connect_error(err: str):
        if _ls[0] not in ("wait_banner", "sent_connect"):
            return
        print(f"[CONN] error: {err}", flush=True)
        _ls[0]              = "panel"
        _creds[0]           = None
        _connect_sent_at[0] = 0.0
        login_panel.visible = True
        login_panel.set_status(f"Connection failed: {err}", error=True)

    conn.on_connect_error = _on_connect_error

    text_panel.on_keypress = lambda: audio.play_sound("keypress")

    # ── GMCP handlers ───────────────────────────────────────────────────
    conn.register_gmcp("HelionVanta.Char.Status",  char_panel.on_status)
    conn.register_gmcp("HelionVanta.World.Map",    map_panel.on_map)

    def _on_ooc(data):
        """OOC GMCP: list of puppetable characters."""
        if _ls[0] == "sent_connect":
            _login_success()
        chars = data.get("characters", [])
        if chars:
            text_panel.append("\n[OOC]  Available characters:")
            for c in chars:
                text_panel.append(f"  • {c}")
            text_panel.append("  Type:  ic <name>  to enter the world.\n")
        else:
            text_panel.append("\n[OOC]  No characters found.  "
                              "Type 'charcreate <name>' to create one.\n")
        if _ls[0] == "playing":
            pass   # suppress late OOC push that races after ic

    conn.register_gmcp("HelionVanta.Account.Ooc", _on_ooc)

    def _on_ui_context(data):
        ctx = data.get("context", "")
        print(f"[UI]   context -> {ctx!r}", flush=True)
        context_panel.on_context(data)
        if _helm_mode[0] and ctx not in _WASD_CONTEXTS:
            _set_helm_mode(False)
        context_panel.set_login_waiting(False)
        if _ls[0] == "ooc":
            _ls[0]            = "playing"
            _playing_since[0] = time.time()
            print("[STATE] ooc -> playing", flush=True)
        track = _CONTEXT_MUSIC.get(ctx)
        if track:
            audio.play_music(track)

    conn.register_gmcp("HelionVanta.UI.Context", _on_ui_context)
    conn.register_gmcp("HelionVanta.UI.Sound",   audio.on_sound)
    conn.register_gmcp("HelionVanta.UI.Music",   audio.on_music)
    conn.register_gmcp("HelionVanta.UI.Notify",  lambda d: text_panel.append(
        f"[{d.get('level','info').upper()}] {d.get('message','')}"))

    def _do_logout():
        conn.send_command("quit")
        conn.stop()
        _ls[0]              = "panel"
        _creds[0]           = None
        _connect_sent_at[0] = 0.0
        _playing_since[0]   = 0.0
        char_panel.data      = {}
        login_panel.visible  = True
        login_panel.set_status("Logged out.")
        context_panel.set_login_waiting(True)
        audio.play_music("mainmenu")

    def _on_ctx_command(cmd):
        if cmd == "_helm_toggle":
            _set_helm_mode(not _helm_mode[0])
            audio.play_sound("button_press")
            return
        if cmd == "_logout":
            _do_logout()
        else:
            conn.send_command(cmd)
            audio.play_sound("button_press")

    context_panel.on_command = _on_ctx_command

    # ── Login state machine ──────────────────────────────────────────────
    # States: "panel" | "wait_banner" | "sent_connect" | "ooc" | "playing"
    _ls              = ["panel"]
    _creds           = [None]
    _connect_sent_at = [0.0]
    _playing_since   = [0.0]

    saved = auth.load_credentials(_host, _port)
    login_panel = LoginPanel(
        _win_size[0], _win_size[1], font,
        saved_username=saved[0] if saved else "",
        asset_manager=am,
    )

    def _do_connect(username, password, remember):
        if _ls[0] in ("wait_banner", "sent_connect", "ooc", "playing"):
            return
        _creds[0]  = (username, password, remember)
        conn.host  = _host
        conn.port  = _port
        conn.start()
        _ls[0]     = "wait_banner"
        print(f"[STATE] panel -> wait_banner  (user={username!r})", flush=True)
        login_panel.set_status("Connecting\u2026")

    login_panel.on_connect = _do_connect

    def _login_success():
        if _ls[0] in ("ooc", "playing"):
            return
        creds  = _creds[0]
        _ls[0] = "ooc"
        _connect_sent_at[0] = 0.0
        login_panel.visible = False
        print("[STATE] sent_connect -> ooc  (login accepted)", flush=True)
        if creds and creds[2]:
            auth.save_credentials(creds[0], creds[1], _host, _port)
        _creds[0] = None

    def _login_fail(reason="Login failed — check credentials."):
        _ls[0] = "panel"
        print(f"[STATE] login FAILED: {reason}", flush=True)
        login_panel.visible = True
        login_panel.set_status(reason, error=True)
        auth.clear_credentials(_host, _port)
        _creds[0] = None

    _BANNER_TRIGGERS = ("welcome to", "====", "----")
    _LOGIN_ERRORS    = (
        "that is not a valid", "incorrect password", "not a correct",
        "no account", "account not found", "wrong password",
        "that password", "that account", "does not exist",
        "invalid username", "invalid password", "no such account",
        "password is wrong", "failed to authenticate",
        "too many failed",
    )
    _LOGIN_ANSI_RE = re.compile(
        r'\x1b\[[0-9;]*[mGKHFABCDEJsurh]|\x1b\([AB]|\x1b[=>]')

    def _on_text(line: str):
        text_panel.append(line)
        state = _ls[0]
        creds = _creds[0]
        lo    = _LOGIN_ANSI_RE.sub("", line).strip().lower()

        if state == "wait_banner":
            if creds and any(t in lo for t in _BANNER_TRIGGERS):
                conn.send_command(f"connect {creds[0]} {creds[1]}")
                _connect_sent_at[0] = time.time()
                _ls[0]              = "sent_connect"
                login_panel.set_status("Authenticating\u2026")

        elif state == "sent_connect":
            if any(err in lo for err in _LOGIN_ERRORS):
                _login_fail()

    conn.on_text         = _on_text
    text_panel.on_submit = conn.send_command

    if saved:
        login_panel.visible = False
        _do_connect(saved[0], saved[1], False)

    # ── Main loop ────────────────────────────────────────────────────────
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.VIDEORESIZE:
                _win_size[0], _win_size[1] = event.w, event.h
                screen = pygame.display.set_mode(
                    (_win_size[0], _win_size[1]), pygame.RESIZABLE)
                _apply_rects(build_rects(_win_size[0], _win_size[1]))
                continue

            if login_panel.handle_event(event):
                continue

            # Tab: toggle WASD travel mode on the overworld
            if (event.type == pygame.KEYDOWN and event.key == pygame.K_TAB
                    and _ls[0] == "playing"
                    and context_panel.context in _WASD_CONTEXTS):
                _set_helm_mode(not _helm_mode[0])
                audio.play_sound("button_press")
                continue

            # Mute button hover/click
            mute_rect = rects["mute"]
            if event.type == pygame.MOUSEMOTION:
                _mute_hover[0] = mute_rect.collidepoint(event.pos)
            if (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1
                    and mute_rect.collidepoint(event.pos)):
                _mute_state[0] = (_mute_state[0] + 1) % 4
                _apply_mute(_mute_state[0], audio)
                audio.play_sound("button_press")
                continue

            # Helm (WASD) mode events
            if (event.type == pygame.KEYDOWN
                    and _ls[0] == "playing"
                    and _helm_mode[0]):
                if event.key == pygame.K_ESCAPE:
                    _set_helm_mode(False)
                    continue
                _dir = _WASD_MAP.get(event.key)
                if _dir:
                    _now = time.time()
                    if _now - _last_move_t[0] >= _MOVE_RATE:
                        conn.send_command(f"go {_dir}")
                        audio.play_sound("footstep")
                        _last_move_t[0] = _now
                    continue

            text_panel.handle_event(event)
            context_panel.handle_event(event, audio)

        # Connection timeout (10 s with no server response after auth send)
        if (_ls[0] == "sent_connect"
                and _connect_sent_at[0] > 0
                and time.time() - _connect_sent_at[0] > 10.0):
            _login_fail("No response from server — connection may have dropped.")

        # WASD hold-to-move polling
        if _ls[0] == "playing" and _helm_mode[0]:
            _now = time.time()
            if _now - _last_move_t[0] >= _MOVE_RATE:
                _keys = pygame.key.get_pressed()
                for _k, _d in _WASD_MAP.items():
                    if _keys[_k]:
                        conn.send_command(f"go {_d}")
                        audio.play_sound("footstep")
                        _last_move_t[0] = _now
                        break

        # ── Draw ────────────────────────────────────────────────────────
        screen.fill(BG_DEEP)
        context_panel.draw(screen)
        char_panel.draw(screen)
        map_panel.draw(screen)
        text_panel.draw(screen)
        _draw_mute_btn(screen, rects["mute"], font_small,
                       _mute_state[0], _mute_hover[0])
        login_panel.draw(screen)   # topmost overlay
        pygame.display.flip()
        clock.tick(30)

    conn.stop()
    audio.cleanup()
    pygame.quit()


if __name__ == "__main__":
    main()
