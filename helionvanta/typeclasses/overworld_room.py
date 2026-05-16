"""OverworldRoom typeclass.

One OverworldRoom instance exists for the kael_cluster (The Shardfield).
The room contains no static exits; movement is handled by OverworldCmdSet
commands that manipulate db.overworld_pos on the player.

db attributes (on the room object):
    planet_key   (str) — e.g. "kael_cluster", "glass_dunes_ruins", "cinder_warrens"
    planet_name  (str) — display name
    entry_point  (list[int, int]) — default [x, y] for first-time arrivals

db attributes (on the CHARACTER while in overworld):
    overworld_pos  (dict) — {"planet": str, "x": int, "y": int}
"""

from __future__ import annotations

import sys
from pathlib import Path

from evennia.objects.objects import DefaultRoom

from .objects import ObjectParent


def _ensure_project_root() -> None:
    root = str(Path(__file__).resolve().parents[2])
    if root not in sys.path:
        sys.path.insert(0, root)


class OverworldRoom(ObjectParent, DefaultRoom):
    """A single persistent room representing a planet's surface.

    Players navigate it by changing their db.overworld_pos rather
    than moving between Evennia room objects.
    """

    # ------------------------------------------------------------------
    # Evennia hooks
    # ------------------------------------------------------------------

    def at_object_receive(self, moved_obj, source_location, **kwargs):
        """Called when an object arrives in this room.

        Sets overworld position (from gateway coords or entry_point),
        then attaches OverworldCmdSet and sends the room description.
        """
        if not moved_obj.has_account:
            return  # ignore NPCs / mobs

        _ensure_project_root()
        from commands.overworld_commands import OverworldCmdSet

        planet_key = self.db.planet_key or "kael_cluster"

        # Determine spawn position.
        pos_set = False
        if source_location and hasattr(source_location, "db"):
            coords = source_location.db.overworld_coords
            if coords:
                # Validate coords are within this map's bounds before using them.
                # A room may carry overworld_coords for a *different* overworld
                # (e.g. vanta_ruins_entry holds planetary coords [22,22] but is
                # also the entry point for the Glass Dunes mini-overworld whose
                # map is only 20×14).  Out-of-bounds coords fall through to the
                # entry_point default below.
                _ensure_project_root()
                from mudgame.data.world_data import WORLD_DATA
                _ow_map = WORLD_DATA.get("overworld", {}).get(planet_key, {}).get("map", [])
                _map_h = len(_ow_map)
                _map_w = len(_ow_map[0]) if _ow_map else 0
                cx, cy = int(coords[0]), int(coords[1])
                if _map_w > 0 and 0 <= cx < _map_w and 0 <= cy < _map_h:
                    moved_obj.db.overworld_pos = {
                        "planet": planet_key,
                        "x": cx,
                        "y": cy,
                    }
                    pos_set = True

        if not pos_set:
            existing = moved_obj.db.overworld_pos or {}
            if existing.get("planet") != planet_key:
                ep = self.db.entry_point or [15, 5]
                moved_obj.db.overworld_pos = {
                    "planet": planet_key,
                    "x": int(ep[0]),
                    "y": int(ep[1]),
                }

        # Attach overworld command set (non-persistent so it's removed on
        # puppet disconnect / server restart without special cleanup).
        moved_obj.cmdset.add(OverworldCmdSet, persistent=False)

        # Show the current location.
        moved_obj.msg(self.return_appearance(moved_obj))

    def at_object_leave(self, moved_obj, target_location, **kwargs):
        """Called when an object leaves this room.

        Removes the overworld command set so normal commands resume.
        """
        if not moved_obj.has_account:
            return
        _ensure_project_root()
        from commands.overworld_commands import OverworldCmdSet

        try:
            moved_obj.cmdset.remove(OverworldCmdSet)
        except Exception:
            pass  # already absent is fine

    # ------------------------------------------------------------------
    # Appearance
    # ------------------------------------------------------------------

    def return_appearance(self, looker, **kwargs):
        """Generate the overworld display for *looker*."""
        if not looker:
            return ""

        _ensure_project_root()
        from mudgame.data.world_data import WORLD_DATA
        from mudgame.systems.overworld import generate_room_description, _RESET

        planet_key = self.db.planet_key or "kael_cluster"
        ow_data = WORLD_DATA.get("overworld", {}).get(planet_key, {})
        planet_name = ow_data.get("planet_name", planet_key)
        planet_map = ow_data.get("map", [])

        pos = (looker.db.overworld_pos or {})
        x = pos.get("x", 15)
        y = pos.get("y", 5)

        desc = generate_room_description(
            planet_key=planet_key,
            planet_name=planet_name,
            planet_map=planet_map,
            x=x,
            y=y,
            overworld_data=ow_data,
            colour=True,
        )

        # Append any encounter mobs that belong to this looker.
        encounter_lines = []
        for obj in self.contents:
            if not (getattr(obj, "db", None) and obj.db.is_encounter_mob):
                continue
            if obj.db.encounter_owner != looker.id:
                continue
            mob_name = obj.db.name or obj.key.replace("_", " ").title()
            if obj.db.auto_aggro:
                # Hostile — bright red
                colour_code = "\033[91m"
            else:
                # Passive — amber/yellow
                colour_code = "\033[33m"
            encounter_lines.append(
                f"  {colour_code}{mob_name}{_RESET}"
            )

        if encounter_lines:
            desc += "\nEncounters:\n" + "\n".join(encounter_lines)

        return desc
