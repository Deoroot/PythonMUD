"""Helion Vanta client — colour theme.

Adapted from the Rust Belt MUD theme (dark industrial) to fit
Helion Vanta's aesthetic: deep space / arid sci-fi.
Primary accent is a cold teal-cyan instead of RustBelt's warm gold.
"""

# ── Base backgrounds ────────────────────────────────────────────────────────
BG_DEEP   = (6,  10,  14)    # very dark blue-black — window fill
BG_PANEL  = (12, 18,  24)    # panel background
BG_HEADER = (18, 26,  36)    # panel header bar

# ── Accent — teal / cyan palette ────────────────────────────────────────────
TEAL_BRIGHT = (80,  220, 200)
TEAL_MID    = (55,  170, 155)
TEAL_DIM    = (35,  110, 100)
TEAL_FAINT  = (18,  55,  50)

# Keep "GOLD" aliases mapped to teal so panel code that references GOLD_* still works
GOLD_BRIGHT = TEAL_BRIGHT
GOLD_MID    = TEAL_MID
GOLD_DIM    = TEAL_DIM
GOLD_FAINT  = TEAL_FAINT

# ── Borders ─────────────────────────────────────────────────────────────────
BORDER_BRIGHT = (55,  160, 145)
BORDER_DIM    = (28,  75,  68)

# ── Corner bracket decorations ───────────────────────────────────────────────
CORNER_LEN = 8
CORNER_W   = 1

# ── Status bar colours ───────────────────────────────────────────────────────
COL_HP      = (80,  210, 110)   # green — health
COL_STAMINA = (80,  160, 220)   # blue  — stamina
COL_BAR_BG  = (20,  30,  35)
COL_WARN    = (220, 170, 50)
COL_DANGER  = (220, 60,  60)
COL_OK      = (80,  200, 110)

# Aliases used by shared panel code (ship_panel heritage)
COL_HULL   = COL_HP
COL_FUEL   = COL_STAMINA
COL_SHIELD = (80,  130, 220)

# ── Input field ─────────────────────────────────────────────────────────────
BG_INPUT   = (10,  16,  22)    # text input bar background
TEXT_INPUT = (160, 230, 220)   # command input bar text colour

# ── Text ────────────────────────────────────────────────────────────────────
TEXT_BRIGHT = (220, 230, 235)

# ── Tab / button colours ─────────────────────────────────────────────────────
TAB_ACTIVE = (30,  55,  50)
TAB_IDLE   = (14,  22,  20)
TAB_BORDER = (40,  90,  80)

BTN_METAL     = (28,  40,  38)
BTN_METAL_HOV = (40,  62,  58)
BTN_METAL_BDR = (55,  90,  82)
BTN_METAL_TXT = TEXT_BRIGHT
