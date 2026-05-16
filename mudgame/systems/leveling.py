"""Pure leveling formulas for Helion Vanta.

Single source of truth for stat maxima at any level/attr combination.
No Evennia imports — safe to use from the mudgame pure layer.

Consumers
---------
* ``helionvanta/typeclasses/characters.py``  — backfill repair in ``at_init``
* ``helionvanta/commands/cmd_utils.py``      — ``_check_level_up``
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Stat-gain constants
# ---------------------------------------------------------------------------

# Per-level incremental gains applied once per normal level-up.
LEVEL_STAT_GAINS: dict[str, int] = {
    "hp_max": 10,
    "shield_max": 10,
    "stamina_max": 8,
    "focus_max": 5,
}

# Base (level-1) stat maxima before any attribute bonuses.
LEVEL_STAT_BASE: dict[str, int] = {
    "hp_max": 100,
    "shield_max": 100,
    "stamina_max": 100,
    "focus_max": 50,
}

# Attribute points awarded per level-up at level 6+.
ATTR_POINTS_PER_LEVEL: int = 2

# Skill points awarded per level-up (normal levels only).
SKILL_POINTS_PER_LEVEL: int = 3


# ---------------------------------------------------------------------------
# Canonical maxima formula
# ---------------------------------------------------------------------------

def stat_maxima_for_level(level: int, attrs: dict) -> dict[str, int]:
    """Return expected stat maxima for a character at *level* with *attrs*.

    This is the single source of truth used by both the backfill-repair code
    in ``characters.py`` and the incremental constants in ``cmd_utils.py``.

    Scaling rules
    ~~~~~~~~~~~~~
    * hp_max      = 100 + (level-1)*10 + max(0, CON  - 10) * 3
    * stamina_max = 100 + (level-1)*8  + max(0, DEX  - 10) * 3
                                        + max(0, CON  - 10) * 2
    * shield_max  = 100 + (level-1)*10 + max(0, MIND - 10) * 4
    * focus_max   =  50 + (level-1)*5  + max(0, PER  - 10) * 2

    Parameters
    ----------
    level:
        Character level (1-indexed; clamped to at least 1).
    attrs:
        Dict of primary attributes; missing keys default to 10.

    Returns
    -------
    dict with keys ``hp_max``, ``stamina_max``, ``shield_max``, ``focus_max``.
    """
    gains = max(0, level - 1)
    con  = attrs.get("con",  10)
    dex  = attrs.get("dex",  10)
    mind = attrs.get("mind", 10)
    per  = attrs.get("per",  10)
    return {
        "hp_max": (
            LEVEL_STAT_BASE["hp_max"]
            + gains * LEVEL_STAT_GAINS["hp_max"]
            + max(0, con - 10) * 3
        ),
        "stamina_max": (
            LEVEL_STAT_BASE["stamina_max"]
            + gains * LEVEL_STAT_GAINS["stamina_max"]
            + max(0, dex - 10) * 3
            + max(0, con - 10) * 2
        ),
        "shield_max": (
            LEVEL_STAT_BASE["shield_max"]
            + gains * LEVEL_STAT_GAINS["shield_max"]
            + max(0, mind - 10) * 4
        ),
        "focus_max": (
            LEVEL_STAT_BASE["focus_max"]
            + gains * LEVEL_STAT_GAINS["focus_max"]
            + max(0, per - 10) * 2
        ),
    }
