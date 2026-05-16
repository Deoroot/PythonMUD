"""Overworld commands — movement, map display, area entry.

These commands are only active while a player is inside an OverworldRoom.
They are attached via OverworldCmdSet in OverworldRoom.at_object_receive
and removed in OverworldRoom.at_object_leave.

Commands
--------
CmdOverworldMove   — n/ne/e/se/s/sw/w/nw (and full names)
CmdOverworldMap    — 'map'  (larger 21×15 zoomed view)
CmdOverworldEnter  — 'enter'  (step into named location)
CmdOverworldLook   — 'look'   (re-display current cell)
"""

from __future__ import annotations

import sys
from pathlib import Path

from evennia import CmdSet
from evennia.commands.default.muxcommand import MuxCommand


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ensure_project_root() -> None:
    root = str(Path(__file__).resolve().parents[2])
    if root not in sys.path:
        sys.path.insert(0, root)


def _get_ow_data(planet_key: str) -> dict:
    _ensure_project_root()
    from mudgame.data.world_data import WORLD_DATA
    return WORLD_DATA.get("overworld", {}).get(planet_key, {})


def _cleanup_encounter_mobs(caller) -> None:
    """Remove any encounter mobs that belong to *caller* from the overworld room."""
    room = caller.location
    if room is None:
        return
    for obj in list(room.contents):
        if getattr(obj, "db", None) and obj.db.is_encounter_mob and obj.db.encounter_owner == caller.id:
            obj.delete()


def _spawn_encounter_mob(caller, mob_key: str, aggro: bool, aggro_delay: int) -> None:
    """Spawn an encounter mob for *caller* in the overworld room."""
    from evennia import create_object, utils
    _ensure_project_root()
    from mudgame.systems.mobs import stats_from_level

    # Look up the mob template from world_data.
    from mudgame.data.world_data import WORLD_DATA
    mob_template = None
    for mob in WORLD_DATA.get("mobs", []):
        if mob.get("key") == mob_key:
            mob_template = mob
            break

    if mob_template is None:
        # Unknown mob key — create a generic level-1 mob.
        level = 1
        mob_name = mob_key.replace("_", " ").replace("ow ", "").title()
    else:
        level = mob_template.get("level", 1)
        mob_name = mob_template.get("name", mob_key.replace("_", " ").title())

    derived = stats_from_level(level)

    mob = create_object("typeclasses.objects.Object", key=mob_name, location=caller.location)
    mob.db.actor_type = "mob"
    mob.db.mob_key = mob_key
    mob.db.level = level
    mob.db.hp = derived["hp"]
    mob.db.hp_max = derived["hp"]
    mob.db.shield_integrity = derived["shield"]
    mob.db.shield_max = derived["shield"]
    mob.db.mob_stamina = 80
    mob.db.skills = {"melee": derived["melee"], "dodge": derived["dodge"], "parry": derived["parry"]}
    mob.db.xp = derived["xp"]
    mob.db.credit_drop = {"min": level * 5, "max": level * 12}
    mob.db.is_encounter_mob = True
    mob.db.encounter_owner = caller.id

    caller.msg(f"|yAn encounter begins! |r{mob_name}|n appears from the terrain.")

    if aggro:
        if aggro_delay <= 0:
            # Attack immediately via combat command.
            caller.msg(f"|r{mob_name}|n surges toward you!")
            mob.db.auto_aggro = caller.id
        else:
            delay_secs = aggro_delay * 3

            def _do_aggro(mob_id, caller_id):
                from evennia import search_object
                mobs = search_object("#" + str(mob_id), exact=True)
                callers = search_object("#" + str(caller_id), exact=True)
                if not mobs or not callers:
                    return
                m = mobs[0]
                c = callers[0]
                if m.location == c.location:
                    c.msg(f"|r{m.name}|n spots you and attacks!")
                    m.db.auto_aggro = caller_id

            utils.delay(delay_secs, _do_aggro, mob.id, caller.id)
            caller.msg(f"|y{mob_name}|n watches you cautiously.")


# ---------------------------------------------------------------------------
# CmdOverworldMove
# ---------------------------------------------------------------------------

class CmdOverworldMove(MuxCommand):
    """Move in a compass direction across the overworld.

    Usage:
        n / north
        ne / northeast
        e / east
        se / southeast
        s / south
        sw / southwest
        w / west
        nw / northwest
    """

    key = "n"
    aliases = [
        "north", "ne", "northeast",
        "e", "east",
        "se", "southeast",
        "s", "south",
        "sw", "southwest",
        "w", "west",
        "nw", "northwest",
    ]
    locks = "cmd:all()"
    help_category = "Overworld"

    # Map alias → canonical direction key
    _ALIAS_MAP: dict[str, str] = {
        "north": "n", "ne": "ne", "northeast": "ne",
        "east": "e", "e": "e",
        "south": "s", "se": "se", "southeast": "se",
        "s": "s", "sw": "sw", "southwest": "sw",
        "west": "w", "w": "w",
        "nw": "nw", "northwest": "nw",
        "n": "n",
    }

    def func(self):
        _ensure_project_root()
        from mudgame.systems.overworld import (
            DIRECTIONS, get_glyph, get_terrain_def, get_available_exits,
            roll_encounter, generate_room_description, get_named_location,
            DIRECTION_NAMES,
        )
        from mudgame.data.world_data import WORLD_DATA

        caller = self.caller
        pos = caller.db.overworld_pos or {}
        planet_key = pos.get("planet", "kael_cluster")
        x = pos.get("x", 15)
        y = pos.get("y", 5)

        ow_data = WORLD_DATA.get("overworld", {}).get(planet_key, {})
        planet_map = ow_data.get("map", [])
        planet_name = ow_data.get("planet_name", planet_key)

        # Determine direction key.
        cmd_used = self.cmdname.lower()
        dir_key = self._ALIAS_MAP.get(cmd_used, cmd_used)

        if dir_key not in DIRECTIONS:
            caller.msg("Unknown direction.")
            return

        dx, dy = DIRECTIONS[dir_key]
        nx, ny = x + dx, y + dy

        # Bounds check.
        map_height = len(planet_map)
        map_width = len(planet_map[0]) if map_height > 0 else 32
        if nx < 0 or ny < 0 or nx >= map_width or ny >= map_height:
            caller.msg("You cannot go that way — the edge of the mapped territory.")
            return

        # Passability check.
        glyph = get_glyph(planet_map, nx, ny)
        tdef = get_terrain_def(planet_key, glyph, x=nx)
        if not tdef.passable:
            msg = tdef.impassable_msg or f"The {tdef.name} is impassable."
            caller.msg(msg)
            return

        # Stamina drain for rough terrain.
        if tdef.stamina_cost > 0:
            current_stamina = caller.db.stamina or 0
            if current_stamina <= 0:
                caller.msg("|yYou're already exhausted, but push on through.|n")
            else:
                new_stamina = max(0, current_stamina - tdef.stamina_cost)
                caller.db.stamina = new_stamina
                if new_stamina == 0:
                    caller.msg("|yThe exertion drains the last of your stamina.|n")

        # Clean up old encounter mobs before moving.
        _cleanup_encounter_mobs(caller)

        # Update position.
        caller.db.overworld_pos = {"planet": planet_key, "x": nx, "y": ny}

        # Show new location.
        desc = generate_room_description(
            planet_key=planet_key,
            planet_name=planet_name,
            planet_map=planet_map,
            x=nx,
            y=ny,
            overworld_data=ow_data,
            colour=True,
        )
        dir_name = DIRECTION_NAMES.get(dir_key, dir_key)
        caller.msg(f"|g[{dir_name.title()}]|n\n{desc}")

        # Roll for encounter.
        import random
        entry = roll_encounter(planet_key, glyph, x=nx)
        if entry is not None:
            _spawn_encounter_mob(caller, entry.mob_key, entry.aggro, entry.aggro_delay)


# ---------------------------------------------------------------------------
# CmdOverworldMap
# ---------------------------------------------------------------------------

class CmdOverworldMap(MuxCommand):
    """Display an extended overworld map (21×15 viewport).

    Usage:
        map

    Shows a larger view of the surroundings with a terrain legend.
    """

    key = "map"
    locks = "cmd:all()"
    help_category = "Overworld"

    def func(self):
        _ensure_project_root()
        from mudgame.systems.overworld import (
            get_glyph, _colour, _RESET, _BORDER_COLOUR,
            HELION_TERRAIN, VANTA_TERRAIN, PLANET_TERRAIN,
            _HELION_GLYPH_COLOUR, _VANTA_GLYPH_COLOUR, _VOID_GLYPH_COLOUR,
        )
        from mudgame.data.world_data import WORLD_DATA

        caller = self.caller
        pos = caller.db.overworld_pos or {}
        planet_key = pos.get("planet", "kael_cluster")
        x = pos.get("x", 15)
        y = pos.get("y", 5)

        ow_data = WORLD_DATA.get("overworld", {}).get(planet_key, {})
        planet_map = ow_data.get("map", [])
        planet_name = ow_data.get("planet_name", planet_key)

        half_w = 10
        half_h = 7

        _bc = _BORDER_COLOUR
        _rc = _RESET

        lines = [f"{_bc}<--- {planet_name} (extended view) --->{_rc}"]
        lines.append(f"{_bc}<----------^---------->{_rc}")

        for dy in range(-half_h, half_h + 1):
            row_chars = []
            for dx in range(-half_w, half_w + 1):
                gx = x + dx
                gy = y + dy
                if dx == 0 and dy == 0:
                    row_chars.append(_colour("@", x=x, planet_key=planet_key))
                else:
                    glyph = get_glyph(planet_map, gx, gy)
                    row_chars.append(_colour(glyph, x=gx, planet_key=planet_key))
            lines.append("".join(row_chars))

        lines.append(f"{_bc}<----------v---------->{_rc}")

        # Legend
        terrain_map = PLANET_TERRAIN.get(planet_key, HELION_TERRAIN)
        legend_entries = []
        for glyph, tdef in terrain_map.items():
            legend_entries.append(f"  {_colour(glyph)} {tdef.name}")

        lines.append("")
        lines.append("Legend:")
        # Two columns
        for i in range(0, len(legend_entries), 2):
            left = legend_entries[i].ljust(30)
            right = legend_entries[i + 1] if (i + 1) < len(legend_entries) else ""
            lines.append(left + right)

        caller.msg("\n".join(lines))


# ---------------------------------------------------------------------------
# CmdOverworldEnter
# ---------------------------------------------------------------------------

class CmdOverworldEnter(MuxCommand):
    """Enter a named location at your current position.

    Usage:
        enter

    Only works when you are standing on a '*' (named location) cell.
    """

    key = "enter"
    locks = "cmd:all()"
    help_category = "Overworld"

    def func(self):
        _ensure_project_root()
        from mudgame.systems.overworld import get_glyph, get_named_location
        from mudgame.data.world_data import WORLD_DATA
        from evennia import search_object

        caller = self.caller
        pos = caller.db.overworld_pos or {}
        planet_key = pos.get("planet", "kael_cluster")
        x = pos.get("x", 15)
        y = pos.get("y", 5)

        ow_data = WORLD_DATA.get("overworld", {}).get(planet_key, {})
        planet_map = ow_data.get("map", [])

        glyph = get_glyph(planet_map, x, y)
        if glyph != "*":
            caller.msg("There is nothing to enter here.")
            return

        loc_data = get_named_location(planet_key, x, y, ow_data)
        if loc_data is None:
            caller.msg("This gateway is unmapped.")
            return

        room_key = loc_data.get("room_key")
        if not room_key:
            caller.msg("This location has no connected area.")
            return

        targets = search_object(room_key, exact=True)
        if not targets:
            caller.msg(f"Cannot find area '{room_key}'.")
            return

        dest = targets[0]
        # Clean up encounter mobs before leaving.
        _cleanup_encounter_mobs(caller)

        loc_name = loc_data["name"]
        caller.msg(f"You enter |w{loc_name}|n.")
        caller.move_to(dest, quiet=True)
        caller.msg(dest.return_appearance(caller))


# ---------------------------------------------------------------------------
# CmdOverworldLook
# ---------------------------------------------------------------------------

class CmdOverworldLook(MuxCommand):
    """Look at your current overworld location.

    Usage:
        look

    Redisplays the terrain description and mini-map.
    """

    key = "look"
    aliases = ["l"]
    locks = "cmd:all()"
    help_category = "Overworld"

    def func(self):
        caller = self.caller
        if caller.location:
            caller.msg(caller.location.return_appearance(caller))


# ---------------------------------------------------------------------------
# OverworldCmdSet
# ---------------------------------------------------------------------------

class OverworldCmdSet(CmdSet):
    """Commands active while the player is on the overworld surface."""

    key = "OverworldCmdSet"

    def at_cmdset_creation(self):
        self.add(CmdOverworldMove())
        self.add(CmdOverworldMap())
        self.add(CmdOverworldEnter())
        self.add(CmdOverworldLook())
