"""Pure loot resolution functions.

All functions are plain Python with no Evennia dependencies so they can be
unit-tested without a running game server.

The Evennia bridge layer in mud_commands.py is responsible for:
  - Feeding mob definitions from WORLD_DATA
  - Writing dropped item keys to ``room.db.floor_items``
  - Writing credit awards to ``caller.db.ledger``
"""

from __future__ import annotations

import random as _random_module


# ---------------------------------------------------------------------------
# Item drop resolution
# ---------------------------------------------------------------------------

def resolve_loot_drops(
    loot_table: list[dict],
    rng: _random_module.Random | None = None,
) -> list[str]:
    """Roll each entry in a loot table and return the keys that pass.

    Args:
        loot_table: List of ``{"item": str, "chance": float}`` dicts.
                    ``chance`` is a 0.0–1.0 probability per entry.
        rng:        Optional seeded Random for deterministic tests.
                    When None the module-level random is used.

    Returns:
        List of item key strings that were selected (may be empty).
    """
    rand = rng or _random_module
    return [
        entry["item"]
        for entry in loot_table
        if rand.random() < entry["chance"]
    ]


# ---------------------------------------------------------------------------
# Credit drop resolution
# ---------------------------------------------------------------------------

def resolve_credit_drop(
    credit_drop: dict,
    rng: _random_module.Random | None = None,
) -> int:
    """Roll a random credit amount within the mob's defined range.

    Args:
        credit_drop: Dict with ``"min"`` and ``"max"`` integer keys.
        rng:         Optional seeded Random for deterministic tests.

    Returns:
        Credit amount as an integer (inclusive of min and max).
    """
    rand = rng or _random_module
    return rand.randint(credit_drop["min"], credit_drop["max"])
