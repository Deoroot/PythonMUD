"""Character generation EvMenu for Helion Vanta.

Triggered automatically on first puppet of a new character.  Presents a brief
atmospheric intro followed by a background selection that sets starting skill
and attribute bonuses.

Entry point: start_chargen(caller)

Menu flow:
  node_intro  →  node_background  →  node_confirm  →  node_apply  (exits)
"""

from __future__ import annotations

import sys
from pathlib import Path


def _ensure_project_root() -> None:
    root = str(Path(__file__).resolve().parents[2])
    if root not in sys.path:
        sys.path.insert(0, root)


_ensure_project_root()

from evennia.utils.evmenu import EvMenu  # noqa: E402
from mudgame.data.world_data import BACKGROUND_DATA, BACKGROUND_ORDER, WORLD_DATA  # noqa: E402

_ITEMS = WORLD_DATA.get("items", {})


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def start_chargen(caller) -> None:
    """Launch the character creation EvMenu on *caller*."""
    EvMenu(
        caller,
        "world.chargen",
        startnode="node_intro",
        persistent=False,
    )


# ---------------------------------------------------------------------------
# EvMenu nodes
# ---------------------------------------------------------------------------


def node_intro(caller, raw_string, **kwargs):
    text = (
        "|c=================================================================|n\n"
        "\n"
        "  |wThe Shardfield.|n  Eighty years of colony ships have carved\n"
        "  something worth fighting for out of the void.\n"
        "\n"
        "  Helion Reach is the colony — marshal corps, civilian council,\n"
        "  and eighty years of accumulated culture held together on a budget.\n"
        "  Across sixteen sectors of impassable asteroid void: |cVanta IX|n.\n"
        "  Alien ruins. Architecture no engineer can date. A vault that has\n"
        "  swallowed every expedition sent to open it.\n"
        "\n"
        "  The Reaches draw contractors, discharged soldiers, and those with\n"
        "  nothing left to lose.  Energy weapons are a colony luxury.  This\n"
        "  far out, you learn the blade — or you don't come back.\n"
        "\n"
        "  You've arrived.  What you are is what you carried here.\n"
        "\n"
        "|c=================================================================|n\n"
        "\n"
        "  Press |wEnter|n to continue."
    )
    options = [
        {"key": "_default", "goto": "node_background"},
        {"key": "", "goto": "node_background"},
    ]
    return text, options


def node_background(caller, raw_string, **kwargs):
    lines = [
        "|wChoose your background.|n\n",
    ]
    for i, bg_key in enumerate(BACKGROUND_ORDER, 1):
        bg = BACKGROUND_DATA[bg_key]
        lines.append(f"  |w{i}.|n |c{bg['name']}|n — {bg['short']}")
    lines.append("\nType the number of your choice.")

    text = "\n".join(lines)

    options = []
    for i, bg_key in enumerate(BACKGROUND_ORDER, 1):
        options.append(
            {
                "key": str(i),
                "desc": BACKGROUND_DATA[bg_key]["name"],
                "goto": ("node_confirm", {"background": bg_key}),
            }
        )
    return text, options


def node_confirm(caller, raw_string, background: str | None = None, **kwargs):
    if not background or background not in BACKGROUND_DATA:
        return node_background(caller, raw_string)

    bg = BACKGROUND_DATA[background]

    # Build a readable bonus summary.
    bonus_parts = []
    for sk, val in bg["skill_bonuses"].items():
        bonus_parts.append(f"|g+{val}|n {sk}")
    for attr, val in bg["attr_bonuses"].items():
        bonus_parts.append(f"|g+{val}|n {attr.upper()}")
    if bg["credits"]:
        bonus_parts.append(f"|g+{bg['credits']}|n starting credits")
    bonus_str = "  ·  ".join(bonus_parts)

    # Derived note for MIND (PSI max) and CON (HP max).
    notes = []
    mind_bonus = bg["attr_bonuses"].get("mind", 0)
    con_bonus = bg["attr_bonuses"].get("con", 0)
    if mind_bonus:
        notes.append(f"MIND +{mind_bonus} → PSI max +{mind_bonus * 5}")
    if con_bonus:
        notes.append(f"CON +{con_bonus} → HP max +{con_bonus * 3}")
    note_str = ("  (" + ", ".join(notes) + ")") if notes else ""

    # Starting weapon line.
    main_wpn_key = bg["starting_weapon"]
    main_wpn_name = _ITEMS.get(main_wpn_key, {}).get("name", main_wpn_key)
    off_wpn_key = bg.get("off_hand_weapon")
    if off_wpn_key:
        off_wpn_name = _ITEMS.get(off_wpn_key, {}).get("name", off_wpn_key)
        weapon_str = f"{main_wpn_name}  +  {off_wpn_name} (off-hand)"
    else:
        weapon_str = main_wpn_name

    # Faction rep line.
    rep_parts = [
        f"|c+{amt}|n {faction.replace('_', ' ').title()}"
        for faction, amt in bg.get("rep_bonus", {}).items()
    ]
    rep_str = "  ·  ".join(rep_parts) if rep_parts else "none"

    text = (
        f"|w{bg['name']}|n\n"
        f"\n"
        f"{bg['desc']}\n"
        f"\n"
        f"|yBonuses:|n  {bonus_str}{note_str}\n"
        f"|yWeapon:|n   {weapon_str}\n"
        f"|yRep:|n      {rep_str}\n"
        f"|yPerk:|n     {bg['perk_desc']}\n"
        f"\n"
        f"Confirm this background?  (|wy|n / |wn|n)"
    )
    options = [
        {
            "key": "y",
            "desc": "Confirm",
            "goto": ("node_apply", {"background": background}),
        },
        {
            "key": "yes",
            "desc": "Confirm",
            "goto": ("node_apply", {"background": background}),
        },
        {"key": "n", "desc": "Back to list", "goto": "node_background"},
        {"key": "no", "desc": "Back to list", "goto": "node_background"},
    ]
    return text, options


def node_apply(caller, raw_string, background: str | None = None, **kwargs):
    """Apply the chosen background bonuses and mark chargen complete."""
    if not background or background not in BACKGROUND_DATA:
        return node_background(caller, raw_string)

    bg = BACKGROUND_DATA[background]

    # --- Skills ---
    skills = dict(caller.db.skills or {})
    for sk, val in bg["skill_bonuses"].items():
        skills[sk] = skills.get(sk, 0) + val
    caller.db.skills = skills

    # --- Attributes ---
    attrs = dict(caller.db.attrs or {})
    for attr, val in bg["attr_bonuses"].items():
        attrs[attr] = attrs.get(attr, 10) + val
    caller.db.attrs = attrs

    # --- Resource recalculation ---
    # PSI max: formula is 10 + MIND × 5 (keep consistent with rest of codebase).
    mind = attrs.get("mind", 10)
    new_psi_max = 10 + mind * 5
    caller.db.psi_max = new_psi_max
    caller.db.psi = new_psi_max

    # HP max: base 100, +3 per CON above 10.
    con = attrs.get("con", 10)
    new_hp_max = 100 + max(0, (con - 10) * 3)
    caller.db.hp_max = new_hp_max
    caller.db.hp = new_hp_max

    # --- Starting credits ---
    if bg["credits"]:
        ledger = dict(caller.db.ledger or {})
        ledger["credits"] = ledger.get("credits", 0) + bg["credits"]
        caller.db.ledger = ledger

    # --- Starting weapon ---
    # Equip the background's weapon(s) into the appropriate slots.
    # Items are gifted (not added to ledger inventory) — consistent with
    # the default training_vibroblade that all characters start with.
    equipped = dict(caller.db.equipped or {})
    main_wpn = bg["starting_weapon"]
    off_wpn = bg.get("off_hand_weapon")
    if main_wpn:
        equipped["main_hand"] = main_wpn
    if off_wpn:
        equipped["off_hand"] = off_wpn
    caller.db.equipped = equipped

    # --- Starting reputation ---
    rep = dict(caller.db.reputation or {})
    rep.setdefault("helion_colony", 0)
    rep.setdefault("vanta_clans", 0)
    for faction, amount in bg.get("rep_bonus", {}).items():
        rep[faction] = rep.get(faction, 0) + amount
    caller.db.reputation = rep

    # --- Mark chargen complete ---
    caller.db.background = background
    caller.db.chargen_complete = True

    bg_name = bg["name"]
    text = (
        f"|gBackground confirmed: |w{bg_name}|n\n"
        f"\n"
        f"Your history is your own.  The Shardfield doesn't care where you\n"
        f"came from — only what you do next.\n"
        f"\n"
        f"Type |wscore|n to review your starting stats.\n"
        f"Type |wlook|n to see your surroundings.\n"
        f"Type |whelp|n for a list of available commands."
    )
    # Returning None for options closes the menu.
    return text, None
