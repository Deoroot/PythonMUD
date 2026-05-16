"""Mob stat derivation from level.

All functions are pure Python with no Evennia dependency so they can
be unit-tested directly.

Level formula (agreed design):
    hp      = 14 + level * 13
    shield  = 4  + level * 13
    melee   = 5  + level * 5
    dodge   = 2  + level * 3
    parry   = 1  + level * 2
    xp      = level * 15

Level reference points:
    Level 2 → warren_raider  (common, Helion Warrens)
    Level 3 → dock_saboteur  (common, Vanta Ruins)
    Level 5 → glass_stalker  (elite,  Glass Dunes)
    Level 7 → vault_guardian (elite,  Relic Vault)
"""

from __future__ import annotations


def stats_from_level(level: int) -> dict[str, int]:
    """Return a dict of derived mob stats for the given level.

    Keys: hp, shield, melee, dodge, parry, xp
    """
    if level < 1:
        level = 1
    return {
        "hp":     14 + level * 13,
        "shield": 4  + level * 13,
        "melee":  5  + level * 5,
        "dodge":  2  + level * 3,
        "parry":  1  + level * 2,
        "xp":     level * 15,
    }
