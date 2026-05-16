"""Shared game constants.

Import from here rather than duplicating values across modules.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Levelling
# ---------------------------------------------------------------------------

# XP required to reach each level.  Level 1 is the starting level.
# Levels above MAIN_LEVEL_CAP award guild tokens instead of stat gains.
LEVEL_XP_TABLE: dict[int, int] = {
    2: 200,
    3: 500,
    4: 1_000,
    5: 2_000,
    6: 3_500,
    7: 5_500,
    8: 8_000,
    9: 11_000,
    10: 15_000,
    # Post-main-cap: guild token levels (each grants 1 free guild token)
    11: 20_000,
    12: 26_000,
    13: 33_000,
    14: 41_000,
    15: 50_000,
    16: 60_000,
    17: 71_000,
    18: 83_000,
    19: 96_000,
    20: 110_000,
    21: 125_000,
    22: 141_000,
    23: 158_000,
    24: 176_000,
    25: 195_000,
    26: 215_000,
    27: 236_000,
    28: 258_000,
    29: 281_000,
    30: 305_000,
    31: 330_000,
    32: 356_000,
    33: 383_000,
    34: 411_000,
    35: 440_000,
    36: 470_000,
    37: 501_000,
    38: 533_000,
    39: 566_000,
    40: 600_000,
}

# Levels up to and including this cap grant stat gains; above it, guild tokens.
MAIN_LEVEL_CAP: int = 10
