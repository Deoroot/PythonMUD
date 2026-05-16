"""UI, prompt, and combat-display helpers.

Extracted from cmd_utils.py.  No Command subclasses.

Exports
-------
_pretty_name(key) -> str
_damage_bar(damage, width) -> str
_hit_verb(total_dmg) -> str
_mob_health_label(hp, hp_max) -> str
_val_color(current, max_val) -> str
_format_prompt(caller) -> str
_send_prompt(caller)
_send_room_oob(caller)
_send_stats_oob(caller)
"""

from __future__ import annotations

import sys
from pathlib import Path


def _ensure_project_root_on_path() -> None:
    root = str(Path(__file__).resolve().parents[2])
    if root not in sys.path:
        sys.path.insert(0, root)


_ensure_project_root_on_path()

from mudgame.contracts import OOB_ROOM_UPDATE, OOB_STATS_UPDATE  # noqa: E402


# ---------------------------------------------------------------------------
# Basic display helpers
# ---------------------------------------------------------------------------

def _pretty_name(key: str) -> str:
    """Convert a snake_case key to a title-cased display name."""
    return key.replace("_", " ").title()


# ---------------------------------------------------------------------------
# Combat display helpers
# ---------------------------------------------------------------------------

def _damage_bar(damage: int, width: int = 8) -> str:
    """Return a BatMUD-style [ ###   ] bar for damage magnitude."""
    bars = min(width, max(0, damage // 4))
    return f"[{'#' * bars}{' ' * (width - bars)}]"


def _hit_verb(total_dmg: int) -> str:
    """Return a narrative verb based on total damage dealt."""
    if total_dmg <= 0:
        return "misses"
    elif total_dmg <= 3:
        return "grazes"
    elif total_dmg <= 8:
        return "hits"
    elif total_dmg <= 15:
        return "wounds"
    elif total_dmg <= 25:
        return "badly wounds"
    else:
        return "devastates"


def _mob_health_label(hp: int, hp_max: int) -> str:
    """Return a colored health status label like BatMUD."""
    pct = (hp / hp_max * 100) if hp_max > 0 else 0
    if pct >= 90:
        return f"|gin excellent shape|n ({pct:.0f}%)"
    elif pct >= 70:
        return f"|Gslightly hurt|n ({pct:.0f}%)"
    elif pct >= 50:
        return f"|ynoticeably hurt|n ({pct:.0f}%)"
    elif pct >= 30:
        return f"|Ynot in good shape|n ({pct:.0f}%)"
    elif pct >= 15:
        return f"|rbadly wounded|n ({pct:.0f}%)"
    else:
        return f"|Rnear death|n ({pct:.0f}%)"


# ---------------------------------------------------------------------------
# UI / prompt helpers
# ---------------------------------------------------------------------------

def _val_color(current: int, max_val: int) -> str:
    """Color code a stat value by percentage of max."""
    pct = current / max_val if max_val > 0 else 0
    if pct >= 0.6:
        return "|g"
    elif pct >= 0.3:
        return "|y"
    return "|r"


def _format_prompt(caller) -> str:
    """Compact colored resource prompt line. Format: 100H 100SH 80ST 60P>"""
    hp     = caller.db.hp or 0
    hp_max = caller.db.hp_max or 100
    sh     = caller.db.shield_integrity or 0
    sh_max = caller.db.shield_max or 100
    st     = caller.db.stamina or 0
    st_max = caller.db.stamina_max or 100
    psi     = caller.db.psi or 0
    psi_max = caller.db.psi_max or 60
    return (
        f"{_val_color(hp, hp_max)}{hp}|nH "
        f"{_val_color(sh, sh_max)}{sh}|nSH "
        f"{_val_color(st, st_max)}{st}|nST "
        f"{_val_color(psi, psi_max)}{psi}|nP|w>|n"
    )


def _send_prompt(caller) -> None:
    """Send the compact resource prompt to the caller."""
    caller.msg(_format_prompt(caller))
    _send_stats_oob(caller)


def _send_room_oob(caller) -> None:
    """Send current room data as an OOB message for client-side map updates."""
    room = caller.location
    if not room:
        return
    caller.msg(oob=(
        OOB_ROOM_UPDATE,
        [],
        {
            "room_key":    room.db.room_key    or room.key,
            "display_name": room.db.display_name or room.key,
            "area":        room.db.area        or "",
            "planet":      room.db.planet      or "",
            "room_type":   room.db.room_type   or "",
        },
    ))


def _send_stats_oob(caller) -> None:
    """Send current stat values as an OOB message for the client status bar."""
    caller.msg(oob=(
        OOB_STATS_UPDATE,
        [],
        {
            "hp":         caller.db.hp              or 0,
            "hp_max":     caller.db.hp_max           or 100,
            "shield":     caller.db.shield_integrity or 0,
            "shield_max": caller.db.shield_max       or 100,
            "stamina":    caller.db.stamina          or 0,
            "stamina_max": caller.db.stamina_max     or 100,
            "psi":        caller.db.psi              or 0,
            "psi_max":    caller.db.psi_max          or 60,
        },
    ))
