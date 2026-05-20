"""Helion Vanta GMCP push functions.

Sends structured JSON to the pygame client via Evennia's OOB/GMCP mechanism.
The helionvanta_client listens for these module names and updates its panels.

GMCP modules used:
  HelionVanta.Account.Ooc     — account/character list on login
  HelionVanta.Char.Status     — character name, HP, stamina, credits, location
  HelionVanta.World.Map       — visible map tiles centred on the player (13×9 viewport)
  HelionVanta.World.Context   — current terrain context → drives image/panel switching
  HelionVanta.UI.Sound        — sound event name → client plays matching audio file
  HelionVanta.UI.Music        — music track change
  HelionVanta.UI.Notify       — popup notification text

World.Context strings (drive the context image panel in the pygame client):
  "overworld"       — travelling the open overworld grid
  "settlement"      — inside a settlement / outpost (glyph 'c')
  "named_location"  — at or inside a named location gateway ('*')
  "ruins"           — ancient ruins / industrial ruins area
  "dungeon"         — instanced dungeon interior
  "combat"          — in active combat

Sound event names:
  "footstep"        — movement on normal terrain
  "footstep_heavy"  — movement on stamina-costing terrain
  "enter_location"  — entering a named location
  "combat_start"    — combat begins
  "combat_hit"      — player takes a hit
  "combat_win"      — encounter won
  "ambient_change"  — context/terrain shift
"""

from __future__ import annotations


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _gmcp(session, module: str, data: dict):
    """Send GMCP data to one session.

    Evennia's OOB encode_gmcp routing requires underscores as separators:
      "HelionVanta_World_Map" → wire "HelionVanta.World.Map"
    """
    session.msg(**{module.replace(".", "_"): ([], data)})


def _send(character, module: str, data: dict):
    """Send GMCP data to all sessions for a character."""
    account = getattr(character, "account", None)
    if account:
        for session in account.sessions.all():
            _gmcp(session, module, data)
    else:
        for session in character.sessions.all():
            _gmcp(session, module, data)


# ---------------------------------------------------------------------------
# Account / OOC
# ---------------------------------------------------------------------------

def send_ooc_state(account, session=None):
    """Push OOC character list. Called from Account.at_post_login."""
    chars = []
    try:
        for char in account.characters:
            if char:
                chars.append({"name": char.key, "dbid": char.dbid})
    except Exception:
        pass

    payload = {
        "account":    account.key,
        "characters": chars,
    }
    if session:
        _gmcp(session, "HelionVanta.Account.Ooc", payload)
    else:
        for sess in account.sessions.all():
            _gmcp(sess, "HelionVanta.Account.Ooc", payload)


# ---------------------------------------------------------------------------
# Character status
# ---------------------------------------------------------------------------

def send_char_status(character):
    """Push character stats to the client's CharPanel."""
    pos = character.db.overworld_pos or {}
    data = {
        "name":     character.key,
        "hp":       getattr(character.db, "hp", 100),
        "hp_max":   getattr(character.db, "hp_max", 100),
        "stamina":  getattr(character.db, "stamina", 100),
        "stam_max": getattr(character.db, "stamina_max", 100),
        "credits":  getattr(character.db, "credits", 0),
        "planet":   pos.get("planet", ""),
        "x":        pos.get("x", 0),
        "y":        pos.get("y", 0),
    }
    _send(character, "HelionVanta.Char.Status", data)


# ---------------------------------------------------------------------------
# World map
# ---------------------------------------------------------------------------

def send_world_map(character):
    """Push a 13×9 viewport of the overworld map centred on the player.

    Sends the raw glyph grid (no ANSI) plus the player position so the
    client's MapPanel can render it with its own colour palette.

    Data format:
      {
        "planet":   "kael_cluster",
        "planet_name": "Kael Cluster",
        "x": 15, "y": 8,
        "viewport_w": 13, "viewport_h": 9,
        "rows": ["..@....", ...],   # 9 strings, each 13 chars wide
        "terrain_name": "Dust Flats",
        "terrain_desc": "A wide expanse...",
        "named_location": "Spaceport" or null,
        "exits": ["n", "e", "s", "w"]
      }
    """
    from mudgame.data.world_data import WORLD_DATA
    from mudgame.systems.overworld import (
        get_glyph, get_terrain_def, get_available_exits,
        get_named_location, render_minimap_plain,
    )

    pos = character.db.overworld_pos
    if not pos:
        return

    planet_key  = pos.get("planet", "kael_cluster")
    px          = pos.get("x", 0)
    py          = pos.get("y", 0)

    ow_data     = WORLD_DATA.get("overworld", {}).get(planet_key, {})
    planet_map  = ow_data.get("map", [])
    planet_name = ow_data.get("name", planet_key)

    if not planet_map:
        return

    glyph  = get_glyph(planet_map, px, py)
    tdef   = get_terrain_def(planet_key, glyph, x=px)
    named  = get_named_location(planet_key, px, py, ow_data)
    exits  = get_available_exits(planet_key, planet_map, px, py)

    # Plain-text viewport (no ANSI); client applies its own colours.
    rows = render_minimap_plain(planet_map, px, py)

    _send(character, "HelionVanta.World.Map", {
        "planet":       planet_key,
        "planet_name":  planet_name,
        "x":            px,
        "y":            py,
        "viewport_w":   13,
        "viewport_h":   9,
        "rows":         rows,
        "terrain_name": tdef.name,
        "terrain_desc": tdef.desc,
        "named_location": named["name"] if named else None,
        "exits":        exits,
    })


# ---------------------------------------------------------------------------
# UI context
# ---------------------------------------------------------------------------

# Map terrain glyph → context key for the context panel image.
_GLYPH_CONTEXT = {
    "c":  "settlement",
    "*":  "named_location",
    "i":  "ruins",
    "R":  "ruins",
    ":":  "void",
    "=":  "road",
    "~":  "impassable",
    "m":  "impassable",
}


def send_ui_context(character, context: str, music: str = None):
    """Tell the client which context image/music to display."""
    character.db.ui_context = context
    _send(character, "HelionVanta.UI.Context", {"context": context})
    if music:
        send_music(character, music)


def send_context_from_position(character):
    """Derive the UI context from the player's current terrain glyph and push it."""
    from mudgame.data.world_data import WORLD_DATA
    from mudgame.systems.overworld import get_glyph, get_terrain_def

    pos = character.db.overworld_pos
    if not pos:
        send_ui_context(character, "overworld")
        return

    planet_key = pos.get("planet", "kael_cluster")
    px         = pos.get("x", 0)
    py         = pos.get("y", 0)

    ow_data    = WORLD_DATA.get("overworld", {}).get(planet_key, {})
    planet_map = ow_data.get("map", [])
    if not planet_map:
        send_ui_context(character, "overworld")
        return

    glyph   = get_glyph(planet_map, px, py)
    context = _GLYPH_CONTEXT.get(glyph, "overworld")
    send_ui_context(character, context)


# ---------------------------------------------------------------------------
# Sound / Music
# ---------------------------------------------------------------------------

def send_sound(character, event: str):
    """Tell the client to play a sound effect."""
    _send(character, "HelionVanta.UI.Sound", {"event": event})


def send_music(character, track: str, loop: bool = True, fade_ms: int = 2000):
    """Tell the client to change the ambient music track."""
    _send(character, "HelionVanta.UI.Music", {
        "track":   track,
        "loop":    loop,
        "fade_ms": fade_ms,
    })


def send_notify(character, message: str, level: str = "info"):
    """Push a popup notification. Levels: 'info', 'warning', 'danger'."""
    _send(character, "HelionVanta.UI.Notify", {"message": message, "level": level})


# ---------------------------------------------------------------------------
# Convenience: push all relevant state at once (e.g. on move/look)
# ---------------------------------------------------------------------------

def push_all(character):
    """Push the full GMCP state update after a move or look command."""
    send_char_status(character)
    send_world_map(character)
    send_context_from_position(character)
