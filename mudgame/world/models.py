"""Core world and character data models."""

from __future__ import annotations

from dataclasses import dataclass, field

from mudgame.contracts import CharacterStats, RoomMeta


@dataclass(slots=True)
class CharacterModel:
    key: str
    stats: CharacterStats = field(default_factory=CharacterStats)
    inventory: list[str] = field(default_factory=list)
    quests: dict[str, str] = field(default_factory=dict)


@dataclass(slots=True)
class RoomModel:
    key: str
    meta: RoomMeta
    exits: dict[str, str] = field(default_factory=dict)
