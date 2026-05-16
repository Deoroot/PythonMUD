"""System contracts and shared interfaces for modular development."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Protocol

RoomType = Literal["spaceport", "industrial", "orbital", "ruins", "shuttle"]
ShipState = Literal["docked", "boarding", "in_transit", "arrived"]
CombatAction = Literal["attack", "heavy", "parry", "dodge", "guard", "feint"]

# ---------------------------------------------------------------------------
# Equipment slot definitions — imported by both typeclasses and commands so
# neither needs to import from the other.
# ---------------------------------------------------------------------------

#: Canonical display order for all gear slots.
EQUIPMENT_SLOTS: tuple[str, ...] = (
    "head", "torso", "legs", "feet", "main_hand", "off_hand", "utility"
)


def default_equipped() -> dict[str, str | None]:
    """Return a fresh equipped-dict with training_vibroblade in main_hand."""
    return {
        "head": None,
        "torso": None,
        "legs": None,
        "feet": None,
        "main_hand": "training_vibroblade",
        "off_hand": None,
        "utility": None,
    }


# ---------------------------------------------------------------------------
# OOB packet type keys — used by mud_commands helpers and any future client
# modules.  Import these instead of repeating the raw strings.
# ---------------------------------------------------------------------------

#: Packet type sent when a player's location changes (map update).
OOB_ROOM_UPDATE: str = "room_update"

#: Packet type sent whenever player stats change (HP/Stamina/Shield bar).
OOB_STATS_UPDATE: str = "stats_update"


@dataclass(slots=True)
class CharacterStats:
    hp: int = 100
    stamina: int = 100
    focus: int = 50
    shield_integrity: int = 100
    equipped_weapon: str = "training_vibroblade"
    weapon_damage_bonus: int = 0
    # Skills (0–100). Auto-grow by use up to SKILL_SOFT_CAP (60), then need
    # skill points from levelling to push further.
    skill_melee: int = 10       # offensive: hit chance + crit; boosted by Stamina
    skill_dodge: int = 10       # passive full-evade; boosted by Focus
    skill_parry: int = 10       # passive partial-block; boosted by Focus
    shield_parry_bonus: int = 0 # extra parry window when shield is in off_hand
    # Weapon-type specialisation skill for the currently equipped weapon.
    # Set at runtime from db.skills["blades"|"bludgeons"|"polearms"].
    # Adds up to +25 hit% at skill 100 (via _hit_chance in combat.py).
    weapon_type_skill: int = 0
    # Flat physical damage reduction from equipped armor.
    # Applied in apply_hit() before shield/HP split; minimum 1 damage always lands.
    phys_reduction: int = 0
    # Off-balance status: set True when the entity was kicked this round.
    # Halves the passive dodge and parry windows in _passive_defense_threshold().
    off_balance: bool = False
    # Primary attributes (base 10). Named with _attr suffix to avoid shadowing builtins.
    # Effects:
    #   str_attr  → melee weapon_damage_bonus (+1 per 3 pts above 10)
    #   dex_attr  → hit% and dodge% (+1 skill_melee per 5 pts, +1 skill_dodge per 4 pts)
    #   con_attr  → hp_max (+3/pt above 10), hp_regen (+1 per 5 pts above 10)
    #   mind_attr → psi_max (+5/pt), psi_regen (+1 per 5 pts above 10)
    #   cha_attr  → shop prices (reserved for future use)
    #   per_attr  → ranged hit% (+1 effective skill_melee per 3 PER above 10 when ranged weapon equipped)
    #   luck_attr → hit% (+1 per 5 pts above 10), avoid% (+1 at LUCK 20), crit% (+1% per pt above 10 on top of base 18%)
    str_attr:  int = 10
    dex_attr:  int = 10
    con_attr:  int = 10
    mind_attr: int = 10
    cha_attr:  int = 10
    per_attr:  int = 10
    luck_attr: int = 10


@dataclass(slots=True)
class RoomMeta:
    key: str
    planet: str
    area: str
    room_type: RoomType


class Combatant(Protocol):
    """Minimum interface combat systems require."""

    name: str
    stats: CharacterStats


class TravelMachine(Protocol):
    """Minimum travel state-machine interface."""

    state: ShipState

    def begin_boarding(self) -> ShipState: ...

    def depart(self) -> ShipState: ...

    def arrive(self) -> ShipState: ...

    def reset_docked(self) -> ShipState: ...
