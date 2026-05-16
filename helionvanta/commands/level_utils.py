"""Level and skill progression helpers.

Extracted from cmd_utils.py.  All helpers operate on Evennia db objects but
contain no Command logic.

Exports
-------
_SKILL_SOFT_CAP, _SKILL_GROW_CHANCE
_maybe_grow_skill(caller, skill_name)
_check_level_up(caller) -> list[str]
"""

from __future__ import annotations

import random
import sys
from pathlib import Path


def _ensure_project_root_on_path() -> None:
    root = str(Path(__file__).resolve().parents[2])
    if root not in sys.path:
        sys.path.insert(0, root)


_ensure_project_root_on_path()

from mudgame.data.constants import LEVEL_XP_TABLE, MAIN_LEVEL_CAP as _MAIN_LEVEL_CAP  # noqa: E402
from mudgame.systems.leveling import (  # noqa: E402
    LEVEL_STAT_GAINS as _LEVEL_STAT_GAINS,
    LEVEL_STAT_BASE as _LEVEL_STAT_BASE,
    ATTR_POINTS_PER_LEVEL as _ATTR_POINTS_PER_LEVEL,
    SKILL_POINTS_PER_LEVEL as _SKILL_POINTS_PER_LEVEL,
)


# ---------------------------------------------------------------------------
# Skill constants
# ---------------------------------------------------------------------------

# Keep in sync with mudgame/systems/combat.py SKILL_SOFT_CAP.
_SKILL_SOFT_CAP = 60
_SKILL_GROW_CHANCE = 0.25   # 25 % chance to gain +1 on each relevant skill use


# ---------------------------------------------------------------------------
# Level / skill helpers
# ---------------------------------------------------------------------------

def _maybe_grow_skill(caller, skill_name: str) -> None:
    """Randomly increment a skill by 1 if it is below the soft cap."""
    if random.random() >= _SKILL_GROW_CHANCE:
        return
    skills = caller.db.skills or {"melee": 10, "dodge": 10, "parry": 10}
    current = skills.get(skill_name, 10)
    if current >= _SKILL_SOFT_CAP:
        return
    skills[skill_name] = current + 1
    caller.db.skills = skills


def _check_level_up(caller) -> list[str]:
    """Check if caller has enough XP to level up; apply gains if so. Returns message lines."""
    msgs = []
    xp = caller.db.xp or 0
    level = caller.db.level or 1

    while True:
        next_level = level + 1
        threshold = LEVEL_XP_TABLE.get(next_level)
        if threshold is None or xp < threshold:
            break

        level = next_level
        caller.db.level = level

        if level <= _MAIN_LEVEL_CAP:
            # Normal stat-gain level-up.
            for stat, gain in _LEVEL_STAT_GAINS.items():
                base = _LEVEL_STAT_BASE.get(stat, 0)
                current_max = getattr(caller.db, stat) or base
                setattr(caller.db, stat, current_max + gain)

            # Attribute gains:
            #   Levels 2–5: auto +1 to all attributes each level-up.
            #   Level 6+:   award attr_points for manual spending.
            if level <= 5:
                attrs = caller.db.attrs or {
                    "str": 10, "dex": 10, "con": 10, "mind": 10,
                    "cha": 10, "per": 10, "luck": 10,
                }
                for k in attrs:
                    attrs[k] = attrs[k] + 1
                caller.db.attrs = attrs
                # CON +1 → hp_max +3, stamina_max +2; DEX +1 → stamina_max +3;
                # MIND +1 → psi_max +5, shield_max +4; PER +1 → focus_max +2.
                caller.db.hp_max = (caller.db.hp_max or 100) + 3
                caller.db.stamina_max = (caller.db.stamina_max or 100) + 5  # DEX(+3) + CON(+2)
                caller.db.shield_max = (caller.db.shield_max or 100) + 4
                caller.db.focus_max = (caller.db.focus_max or 50) + 2
                caller.db.psi_max = (caller.db.psi_max or 60) + 5
                attr_msg = ("+1 all Attrs (CON: +3 HP, +2 Stamina max | DEX: +3 Stamina max | "
                            "MIND: +4 Shield, +5 PSI max | PER: +2 Focus max)")
            else:
                caller.db.attr_points = (caller.db.attr_points or 0) + _ATTR_POINTS_PER_LEVEL
                attr_msg = f"+{_ATTR_POINTS_PER_LEVEL} attr points to spend (use: train <attr>)"

            # Fully restore all stats on level-up — it's a reward.
            caller.db.hp = caller.db.hp_max
            caller.db.shield_integrity = caller.db.shield_max
            caller.db.stamina = caller.db.stamina_max
            caller.db.focus = caller.db.focus_max
            caller.db.psi = caller.db.psi_max or 60

            # Award skill points to spend above the soft cap.
            caller.db.skill_points = (caller.db.skill_points or 0) + _SKILL_POINTS_PER_LEVEL

            msgs.append(
                f"|y*** LEVEL UP! You are now level {level}. "
                f"HP +{_LEVEL_STAT_GAINS['hp_max']} | Shield +{_LEVEL_STAT_GAINS['shield_max']} | "
                f"Stamina +{_LEVEL_STAT_GAINS['stamina_max']} | Focus +{_LEVEL_STAT_GAINS['focus_max']}. "
                f"{attr_msg}. All resources restored. +{_SKILL_POINTS_PER_LEVEL} skill points. ***|n"
            )
        else:
            # Post-cap: award a free_level token for guild advancement, plus
            # 1 skill point so the player still gains something to spend.
            caller.db.free_levels = (caller.db.free_levels or 0) + 1
            free_total = caller.db.free_levels
            caller.db.skill_points = (caller.db.skill_points or 0) + 1

            # Restore resources on level-up.
            caller.db.hp = caller.db.hp_max
            caller.db.shield_integrity = caller.db.shield_max
            caller.db.stamina = caller.db.stamina_max
            caller.db.focus = caller.db.focus_max
            caller.db.psi = caller.db.psi_max or 60

            msgs.append(
                f"|y*** LEVEL UP! You are now level {level}. "
                f"|cGuild advancement token earned|y — free levels: {free_total}. "
                f"+1 skill point. "
                f"Visit your guild hall to advance your rank! Resources restored. ***|n"
            )

    return msgs
