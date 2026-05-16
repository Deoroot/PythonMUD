"""Status effect definitions and per-tick processing.

Effects are stored as dicts keyed by effect name → ticks remaining.
All functions are pure Python and take/return plain dicts so they can be
unit-tested without Evennia.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Definitions
# ---------------------------------------------------------------------------

STATUS_DEFS: dict[str, dict] = {
    "bleed": {
        "name": "Bleeding",
        "hp_drain": 4,          # HP lost per tick
        "skip_action": False,
        "defense_penalty": 0,
    },
    "stun": {
        "name": "Stunned",
        "hp_drain": 0,
        "skip_action": True,    # target skips its next action
        "defense_penalty": 0,
    },
    "weakened": {
        "name": "Weakened",
        "hp_drain": 0,
        "skip_action": False,
        "defense_penalty": 10,  # subtracted from dodge and parry skills
    },
    "off_balance": {
        "name": "Off-balance",
        "hp_drain": 0,
        "skip_action": False,
        "defense_penalty": 0,   # handled directly in _passive_defense_threshold via CharacterStats.off_balance
    },
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def apply_effect(effects: dict[str, int], name: str, ticks: int) -> dict[str, int]:
    """Add or refresh an effect, keeping whichever duration is longer."""
    effects = dict(effects)
    effects[name] = max(effects.get(name, 0), ticks)
    return effects


def is_stunned(effects: dict[str, int]) -> bool:
    return effects.get("stun", 0) > 0


def defense_penalty(effects: dict[str, int]) -> int:
    """Return the total skill penalty applied to dodge and parry."""
    total = 0
    for name, ticks in effects.items():
        if ticks > 0:
            total += STATUS_DEFS.get(name, {}).get("defense_penalty", 0)
    return total


def tick_effects(
    effects: dict[str, int],
    current_hp: int,
) -> tuple[dict[str, int], int, list[str]]:
    """Process one combat tick for all active effects.

    Returns:
        updated_effects: effects with decremented (and expired) ticks removed.
        hp_drained:      total HP lost this tick from DoT effects.
        messages:        list of effect note strings for the combat log.
    """
    updated: dict[str, int] = {}
    hp_drained = 0
    messages: list[str] = []

    for name, ticks in effects.items():
        defn = STATUS_DEFS.get(name, {})

        drain = defn.get("hp_drain", 0)
        if drain > 0:
            actual = min(drain, current_hp)   # can't drain below 0
            hp_drained += actual
            current_hp -= actual
            messages.append(f"bleed:{actual}")

        if defn.get("skip_action"):
            messages.append(f"stun:active")

        remaining = ticks - 1
        if remaining > 0:
            updated[name] = remaining

    return updated, hp_drained, messages
