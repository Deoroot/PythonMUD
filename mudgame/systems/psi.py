"""PSI ability definitions and pure resolution functions.

PSI abilities are instant-use powers driven by the PSI pool (psi / psi_max).
They do not use the technique wind-up queue — they fire immediately.

Six abilities are defined:
  heal    — self-heal scaling with MIND; usable in and out of combat.
  shock   — ranged PSI damage to a combat target; bypasses phys_reduction;
            scales with MIND.
  ward    — PSI Weavers guild: erect a 1-round absorption barrier (rank 1+).
  bolt    — PSI Weavers guild: stronger PSI blast (rank 3+).
  shatter — PSI Weavers guild: massive burst + stun (rank 6+).
  lance   — PSI Weavers guild: void energy strike that bypasses shields (rank 13+).
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Definitions
# ---------------------------------------------------------------------------

PSI_ABILITY_DEFS: dict[str, dict] = {
    "heal": {
        "name": "PSI Heal",
        "psi_cost": 20,
        "target": "self",
        "combat_only": False,
        "desc": (
            "Channel PSI energy inward to mend wounds. "
            "Restores 10 HP at base MIND (10), +2 HP per MIND point above 10."
        ),
    },
    "shock": {
        "name": "PSI Shock",
        "psi_cost": 25,
        "target": "enemy",
        "combat_only": True,
        "desc": (
            "Discharge a concentrated pulse of PSI energy into a target's neural system. "
            "Bypasses physical armor. Deals 8 damage at base MIND (10), "
            "+3 per MIND point above 10. Shield absorbs first."
        ),
    },
    "ward": {
        "name": "Resonance Shield",
        "psi_cost": 30,
        "target": "self",
        "combat_only": False,
        "guild": "psi_weavers",
        "min_rank": 1,
        "desc": (
            "Erect a 1-round PSI barrier that absorbs 20 + (rank × 2) incoming melee "
            "damage. Expires at the end of the next combat round."
        ),
    },
    "bolt": {
        "name": "PSI Bolt",
        "psi_cost": 35,
        "target": "enemy",
        "combat_only": True,
        "guild": "psi_weavers",
        "min_rank": 3,
        "desc": (
            "A concentrated PSI blast. Deals 15 damage + 4 per MIND above 10. "
            "Bypasses physical armor. Shield absorbs first."
        ),
    },
    "shatter": {
        "name": "Mind Shatter",
        "psi_cost": 50,
        "target": "enemy",
        "combat_only": True,
        "guild": "psi_weavers",
        "min_rank": 6,
        "desc": (
            "Overwhelm neural defenses with a massive PSI burst. "
            "Deals 20 + 6 per MIND above 10 and stuns the target for 1 round."
        ),
    },
    "lance": {
        "name": "Void Lance",
        "psi_cost": 70,
        "target": "enemy",
        "combat_only": True,
        "guild": "psi_weavers",
        "min_rank": 13,
        "desc": (
            "Channel raw void energy into a piercing lance that bypasses shields entirely. "
            "Deals 30 + 8 per MIND above 10 direct HP damage. Costs 70 PSI."
        ),
    },
}

# ---------------------------------------------------------------------------
# Resolution functions (pure, testable — no Evennia imports)
# ---------------------------------------------------------------------------


def resolve_psi_heal(
    psi: int,
    psi_max: int,
    mind: int,
    hp: int,
    hp_max: int,
    heal_bonus: int = 0,
    cost_reduction: int = 0,
) -> tuple[int, int, str]:
    """Resolve a PSI Heal attempt.

    Args:
        psi:            Current PSI points.
        psi_max:        Maximum PSI capacity (used for context; not part of the formula).
        mind:           Character MIND attribute (base 10).
        hp:             Current HP.
        hp_max:         Maximum HP.
        heal_bonus:     Flat HP bonus from Focused Channel guild skill.
        cost_reduction: PSI cost reduction (e.g. 5 for Compact Remnant background).

    Returns:
        (new_psi, hp_gained, note)

        note is one of:
          "healed"           — success; new_psi and hp_gained are valid.
          "already_full"     — HP was already at max; PSI was not spent.
          "insufficient_psi" — not enough PSI; PSI was not spent.
    """
    cost = max(1, PSI_ABILITY_DEFS["heal"]["psi_cost"] - cost_reduction)
    if psi < cost:
        return psi, 0, "insufficient_psi"

    # Heal formula: 10 base + 2 per MIND above 10 + focused_channel bonus.
    heal_amount = 10 + max(0, (mind - 10) * 2) + heal_bonus
    hp_gained = min(hp_max - hp, heal_amount)

    if hp_gained <= 0:
        # PSI is not spent when already full.
        return psi, 0, "already_full"

    return psi - cost, hp_gained, "healed"


def resolve_psi_shock(
    psi: int,
    mind: int,
    defender_shield: int,
    defender_hp: int,
) -> tuple[int, int, int, str]:
    """Resolve a PSI Shock attempt.

    PSI damage bypasses physical armor (phys_reduction is not applied).
    Shield absorbs damage first; any remainder carries through to HP.

    Args:
        psi:              Attacker's current PSI points.
        mind:             Attacker's MIND attribute (base 10).
        defender_shield:  Target's current shield integrity (0 or more).
        defender_hp:      Target's current HP.

    Returns:
        (new_psi, shield_damage, hp_damage, note)

        note is one of:
          "shocked"          — success; damages are valid.
          "insufficient_psi" — not enough PSI; nothing changed.
    """
    cost = PSI_ABILITY_DEFS["shock"]["psi_cost"]
    if psi < cost:
        return psi, 0, 0, "insufficient_psi"

    # Damage formula: 8 base + 3 per MIND above 10.
    raw = 8 + max(0, (mind - 10) * 3)

    # Shield absorbs first.
    sh_dmg = min(max(0, defender_shield), raw)
    hp_dmg = max(0, raw - sh_dmg)

    return psi - cost, sh_dmg, hp_dmg, "shocked"


def resolve_psi_ward(
    psi: int,
    guild_rank: int,
) -> tuple[int, int, str]:
    """Resolve a Resonance Shield (PSI Ward) attempt.

    Args:
        psi:        Current PSI points.
        guild_rank: Player's PSI Weavers rank (must be >= 1).

    Returns:
        (new_psi, absorption, note)

        note is one of:
          "warded"           — success; absorption is the HP damage blocked next round.
          "insufficient_psi" — not enough PSI; nothing changed.
    """
    cost = PSI_ABILITY_DEFS["ward"]["psi_cost"]
    if psi < cost:
        return psi, 0, "insufficient_psi"

    absorption = 20 + guild_rank * 2
    return psi - cost, absorption, "warded"


def resolve_psi_bolt(
    psi: int,
    mind: int,
    defender_shield: int,
    defender_hp: int,
) -> tuple[int, int, int, str]:
    """Resolve a PSI Bolt attempt.

    Stronger than PSI Shock. Bypasses physical armor; shield absorbs first.

    Args:
        psi:              Attacker's current PSI points.
        mind:             Attacker's MIND attribute (base 10).
        defender_shield:  Target's current shield integrity.
        defender_hp:      Target's current HP.

    Returns:
        (new_psi, shield_damage, hp_damage, note)

        note is one of:
          "hit"              — success.
          "insufficient_psi" — not enough PSI; nothing changed.
    """
    cost = PSI_ABILITY_DEFS["bolt"]["psi_cost"]
    if psi < cost:
        return psi, 0, 0, "insufficient_psi"

    # Damage formula: 15 base + 4 per MIND above 10.
    raw = 15 + max(0, (mind - 10) * 4)

    sh_dmg = min(max(0, defender_shield), raw)
    hp_dmg = max(0, raw - sh_dmg)

    return psi - cost, sh_dmg, hp_dmg, "hit"


def resolve_psi_shatter(
    psi: int,
    mind: int,
    defender_shield: int,
    defender_hp: int,
) -> tuple[int, int, int, bool, str]:
    """Resolve a Mind Shatter attempt.

    Massive PSI burst that also stuns the target for 1 combat round.
    Bypasses physical armor; shield absorbs first.

    Args:
        psi:              Attacker's current PSI points.
        mind:             Attacker's MIND attribute (base 10).
        defender_shield:  Target's current shield integrity.
        defender_hp:      Target's current HP.

    Returns:
        (new_psi, shield_damage, hp_damage, stuns, note)

        note is one of:
          "shattered"        — success; stuns is True.
          "insufficient_psi" — not enough PSI; nothing changed.
    """
    cost = PSI_ABILITY_DEFS["shatter"]["psi_cost"]
    if psi < cost:
        return psi, 0, 0, False, "insufficient_psi"

    # Damage formula: 20 base + 6 per MIND above 10.
    raw = 20 + max(0, (mind - 10) * 6)

    sh_dmg = min(max(0, defender_shield), raw)
    hp_dmg = max(0, raw - sh_dmg)

    return psi - cost, sh_dmg, hp_dmg, True, "shattered"


def resolve_psi_lance(
    psi: int,
    mind: int,
    defender_hp: int,
) -> tuple[int, int, str]:
    """Resolve a Void Lance attempt.

    Channels raw void energy that bypasses shields entirely, dealing direct
    HP damage. Costs 70 PSI. Requires PSI Weavers rank 13.

    Args:
        psi:          Attacker's current PSI points.
        mind:         Attacker's MIND attribute (base 10).
        defender_hp:  Target's current HP.

    Returns:
        (new_psi, hp_damage, note)

        note is one of:
          "hit"              — success.
          "insufficient_psi" — not enough PSI; nothing changed.
    """
    cost = PSI_ABILITY_DEFS["lance"]["psi_cost"]
    if psi < cost:
        return psi, 0, "insufficient_psi"

    # Damage formula: 30 base + 8 per MIND above 10.
    hp_dmg = 30 + max(0, (mind - 10) * 8)

    return psi - cost, hp_dmg, "hit"


# ---------------------------------------------------------------------------
# Sleep recovery
# ---------------------------------------------------------------------------

def resolve_sleep_psi_restore(
    *,
    psi: int,
    psi_max: int,
    mind: int,
    partial: bool = False,
) -> tuple[int, int]:
    """Compute PSI restored by a sleep cycle.

    Formula: ``15 + max(0, (mind - 10) * 2)``, halved (floor) when partial.

    Args:
        psi:     Character's current PSI.
        psi_max: Character's maximum PSI.
        mind:    Character's MIND attribute.
        partial: True if the player woke early (half recovery).

    Returns:
        ``(new_psi, gained)`` — values after applying the restore, capped at
        *psi_max*.  ``gained`` may be 0 if already at full PSI.
    """
    restore = 15 + max(0, (mind - 10) * 2)
    if partial:
        restore //= 2
    new_psi = min(psi_max, psi + restore)
    return new_psi, new_psi - psi
