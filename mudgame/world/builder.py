"""World builder and validation helpers for seed scripts/tests."""

from __future__ import annotations

from collections import deque

from mudgame.data.world_data import WORLD_DATA

VALID_ROOM_TYPES = {"spaceport", "industrial", "orbital", "ruins", "shuttle"}


def flatten_rooms() -> dict[str, dict]:
    rooms: dict[str, dict] = {}

    for planet_key, planet_data in WORLD_DATA["planets"].items():
        for area_key, area_data in planet_data["areas"].items():
            for room_key, room_data in area_data["rooms"].items():
                rooms[room_key] = {
                    "planet": planet_key,
                    "area": area_key,
                    "room_type": room_data["room_type"],
                    "name": room_data["name"],
                    "exits": dict(room_data.get("exits", {})),
                }

    for room_key, room_data in WORLD_DATA["shuttle"]["rooms"].items():
        rooms[room_key] = {
            "planet": "transit",
            "area": "shuttle",
            "room_type": room_data["room_type"],
            "name": room_data["name"],
            "exits": dict(room_data.get("exits", {})),
        }

    return rooms


def validate_exit_targets(rooms: dict[str, dict]) -> list[str]:
    missing: list[str] = []
    for room_key, room_data in rooms.items():
        for _, target in room_data["exits"].items():
            if target in {"dynamic", "locked"}:
                continue
            if target not in rooms:
                missing.append(f"{room_key} -> {target}")
    return missing


def validate_room_metadata(rooms: dict[str, dict]) -> list[str]:
    issues: list[str] = []
    for room_key, room_data in rooms.items():
        planet = room_data.get("planet")
        area = room_data.get("area")
        room_type = room_data.get("room_type")

        if not isinstance(planet, str) or not planet:
            issues.append(f"{room_key}: invalid planet")
        if not isinstance(area, str) or not area:
            issues.append(f"{room_key}: invalid area")
        if room_type not in VALID_ROOM_TYPES:
            issues.append(f"{room_key}: invalid room_type '{room_type}'")
    return issues


def path_exists(start: str, goal: str, rooms: dict[str, dict]) -> bool:
    queue: deque[str] = deque([start])
    seen: set[str] = {start}

    while queue:
        current = queue.popleft()
        if current == goal:
            return True

        for target in rooms[current]["exits"].values():
            if target in {"dynamic", "locked"}:
                continue
            if target not in seen:
                seen.add(target)
                queue.append(target)

    return False


def seed_summary() -> dict[str, int]:
    rooms = flatten_rooms()
    return {
        "room_count": len(rooms),
        "npc_count": len(WORLD_DATA["npcs"]),
        "mob_count": len(WORLD_DATA["mobs"]),
        "quest_count": len(WORLD_DATA.get("quests", [])),
        "missing_exit_count": len(validate_exit_targets(rooms)),
        "invalid_metadata_count": len(validate_room_metadata(rooms)),
    }
