"""Evennia runtime bridge for building the vertical-slice MUD world."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _ensure_project_root_on_path() -> None:
    root = str(_project_root())
    if root not in sys.path:
        sys.path.insert(0, root)


def build_vertical_slice(force_reset: bool = False) -> dict[str, int]:
    """Create/update rooms, exits, NPCs and mobs from mudgame data.

    This is safe to run multiple times; existing objects are reused.
    """
    _ensure_project_root_on_path()

    from evennia import create_object, search_object
    from mudgame.data.world_data import WORLD_DATA

    overworld_rooms_created = 0

    rooms_created = 0
    exits_created = 0
    npcs_created = 0
    mobs_created = 0
    overworld_rooms_created = 0

    def _find_or_create_room(room_key: str, room_data: dict[str, Any], planet: str, area: str):
        nonlocal rooms_created

        existing = search_object(room_key, exact=True)
        if existing:
            room = existing[0]
        else:
            room = create_object(
                "typeclasses.rooms.Room",
                key=room_key,
            )
            rooms_created += 1

        room.db.room_key = room_key
        room.db.display_name = room_data.get("name", room_key)
        room.db.planet = planet
        room.db.area = area
        room.db.room_type = room_data.get("room_type", "spaceport")
        # Always prefer the desc from world_data when present; fall back to placeholder.
        data_desc = room_data.get("desc")
        if data_desc:
            room.db.desc = data_desc
        elif not room.db.desc or force_reset:
            room.db.desc = f"{room.db.display_name}. Sector: {planet}/{area}."
        return room

    def _ensure_exit(source_room, direction: str, target_room):
        nonlocal exits_created

        for ex in source_room.exits:
            if ex.key == direction:
                ex.destination = target_room
                return ex

        create_object(
            "typeclasses.exits.Exit",
            key=direction,
            location=source_room,
            destination=target_room,
        )
        exits_created += 1
        return None

    # Build all rooms first.
    room_map: dict[str, Any] = {}
    for planet_key, planet_data in WORLD_DATA["planets"].items():
        for area_key, area_data in planet_data["areas"].items():
            for room_key, room_data in area_data["rooms"].items():
                room_map[room_key] = _find_or_create_room(room_key, room_data, planet_key, area_key)

    for room_key, room_data in WORLD_DATA["shuttle"]["rooms"].items():
        room_map[room_key] = _find_or_create_room(room_key, room_data, "transit", "shuttle")

    # Build exits.
    for planet_data in WORLD_DATA["planets"].values():
        for area_data in planet_data["areas"].values():
            for room_key, room_data in area_data["rooms"].items():
                source = room_map[room_key]
                for direction, target_key in room_data.get("exits", {}).items():
                    if target_key == "dynamic":
                        continue
                    target = room_map[target_key]
                    _ensure_exit(source, direction, target)

    for room_key, room_data in WORLD_DATA["shuttle"]["rooms"].items():
        source = room_map[room_key]
        for direction, target_key in room_data.get("exits", {}).items():
            if target_key == "dynamic":
                # Default dock target is Helion; travel command updates this in runtime.
                target_key = "helion_shuttle_dock"
            if target_key == "locked":
                continue
            target = room_map[target_key]
            _ensure_exit(source, direction, target)

    def _find_or_create_actor(entry: dict[str, Any], actor_type: str):
        nonlocal npcs_created, mobs_created

        actor_key = entry["key"]
        existing = search_object(actor_key, exact=True)
        if existing:
            actor = existing[0]
        else:
            actor = create_object("typeclasses.objects.Object", key=actor_key)
            if actor_type == "npc":
                npcs_created += 1
            else:
                mobs_created += 1

        actor.location = room_map[entry["room"]]
        actor.db.actor_type = actor_type
        _stats_set = False
        for k, v in entry.items():
            if k == "room":
                actor.attributes.add("spawn_room_key", v)
                continue
            if k == "stats" and isinstance(v, dict):
                # Explicit stats dict takes precedence over level derivation.
                actor.attributes.add("hp", v.get("hp", 40))
                actor.attributes.add("hp_max", v.get("hp", 40))
                actor.attributes.add("shield_integrity", v.get("shield_integrity", 20))
                actor.attributes.add("shield_max", v.get("shield_integrity", 20))
                actor.attributes.add("mob_stamina", 80)
                _stats_set = True
            else:
                actor.attributes.add(k, v)

        # Level-derived stat fallback: used when no explicit stats dict is provided.
        if not _stats_set:
            _ensure_project_root_on_path()
            from mudgame.systems.mobs import stats_from_level
            _level = entry.get("level", 1)
            _derived = stats_from_level(_level)
            actor.attributes.add("hp", _derived["hp"])
            actor.attributes.add("hp_max", _derived["hp"])
            actor.attributes.add("shield_integrity", _derived["shield"])
            actor.attributes.add("shield_max", _derived["shield"])
            actor.attributes.add("mob_stamina", 80)
            # Also set xp if no explicit xp field was provided.
            if "xp" not in entry:
                actor.attributes.add("xp", _derived["xp"])

        return actor

    for npc in WORLD_DATA.get("npcs", []):
        _find_or_create_actor(npc, "npc")

    for mob in WORLD_DATA.get("mobs", []):
        _find_or_create_actor(mob, "mob")

    # -----------------------------------------------------------------------
    # Build overworld rooms (one per planet).
    # -----------------------------------------------------------------------

    # Gateway rooms: instanced area → (planet_key, overworld_coords)
    # All main-world gateways point to "kael_cluster" (unified 80×32 grid).
    # Vanta IX x coords are shifted +48 relative to the old 32×32 grid.
    GATEWAY_COORDS: dict[str, tuple[str, list[int]]] = {
        # Helion Reach side — x unchanged in unified grid
        "helion_gate":          ("kael_cluster", [15, 5]),
        "iron_covenant_hall":   ("kael_cluster", [23, 14]),
        "helion_warrens_entry": ("kael_cluster", [8, 21]),
        # Vanta IX side — x shifted +48 in unified grid
        "vanta_customs":        ("kael_cluster", [63, 5]),
        "psi_weavers_sanctum":  ("kael_cluster", [55, 14]),
        "vanta_ruins_entry":    ("kael_cluster", [70, 22]),
        # Glass Dunes mini-overworld gateways (unchanged)
        "vanta_ruins_core":     ("glass_dunes_ruins", [4, 8]),
        "vanta_ruins_vault":    ("glass_dunes_ruins", [15, 12]),
        # Cinder Warrens mini-overworld gateways (unchanged)
        "helion_warrens_core":  ("cinder_warrens", [5, 8]),
        "helion_warrens_forge": ("cinder_warrens", [14, 11]),
    }

    overworld_data = WORLD_DATA.get("overworld", {})
    ow_room_map: dict[str, Any] = {}

    for planet_key, ow_planet in overworld_data.items():
        ow_key = f"overworld_{planet_key}"
        existing = search_object(ow_key, exact=True)
        if existing:
            ow_room = existing[0]
        else:
            ow_room = create_object(
                "typeclasses.overworld_room.OverworldRoom",
                key=ow_key,
            )
            overworld_rooms_created += 1

        ow_room.db.planet_key = planet_key
        ow_room.db.planet_name = ow_planet.get("planet_name", planet_key)
        ow_room.db.entry_point = ow_planet.get("entry_point", [15, 5])
        ow_room_map[planet_key] = ow_room

    # Wire "out" exits from gateway rooms to overworld rooms.
    for room_key, (planet_key, coords) in GATEWAY_COORDS.items():
        if room_key not in room_map:
            continue
        gateway_room = room_map[room_key]
        if planet_key not in ow_room_map:
            continue
        ow_room = ow_room_map[planet_key]

        # Set return coordinates on the gateway room.
        gateway_room.db.overworld_coords = coords
        gateway_room.db.overworld_planet = planet_key

        # Add "out" exit if it doesn't already exist.
        _ensure_exit(gateway_room, "out", ow_room)

    # Wire the "down" exit from the Glass Dunes access lift into the mini-OW.
    # vanta_ruins_entry no longer has a static "down" exit in world_data (it was
    # removed so the lift descends into the Glass Dunes mini-overworld instead).
    if "vanta_ruins_entry" in room_map and "glass_dunes_ruins" in ow_room_map:
        _ensure_exit(room_map["vanta_ruins_entry"], "down", ow_room_map["glass_dunes_ruins"])

    # Wire the "down" exit from the Cinder Warrens entry hatch into the mini-OW.
    # helion_warrens_entry no longer has a static "down" exit in world_data (it was
    # removed so the hatch descends into the Cinder Warrens mini-overworld instead).
    if "helion_warrens_entry" in room_map and "cinder_warrens" in ow_room_map:
        _ensure_exit(room_map["helion_warrens_entry"], "down", ow_room_map["cinder_warrens"])

    return {
        "rooms_created": rooms_created,
        "exits_created": exits_created,
        "npcs_created": npcs_created,
        "mobs_created": mobs_created,
        "overworld_rooms_created": overworld_rooms_created,
        "total_rooms": len(room_map),
        "total_quests": len(WORLD_DATA.get("quests", [])),
    }
