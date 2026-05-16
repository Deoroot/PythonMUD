"""Active technique definitions and resolution.

Techniques are player-queued multi-tick combat moves. The player types the
technique name (e.g. 'slash') which stores it in db.queued_technique with a
wind-up counter. _run_combat_round decrements the counter each round and fires
the technique when it reaches zero, replacing the normal main-hand attack.
"""

from __future__ import annotations

import random as _random_module

from mudgame.contracts import CharacterStats
from mudgame.systems.combat import (
    CombatEntity,
    CombatResult,
    _clamp_non_negative,
    _hit_chance,
    _passive_defense_threshold,
    apply_hit,
)

# ---------------------------------------------------------------------------
# Definitions
# ---------------------------------------------------------------------------

TECHNIQUE_DEFS: dict[str, dict] = {
    "slash": {
        "name": "Slash",
        "wind_up": 1,           # rounds of wind-up before firing
        "stamina_cost": 14,
        "damage_scale": 1.4,    # multiplied against the normal attack base damage
        "shield_pierce": False,
        "applies": [("bleed", 3)],
        "preferred_weapon_types": ["blades"],
        "weapon_type_req": ["blades"],
        "skill_req": 20,        # blades skill >= 20 to unlock
        "desc": "A deliberate cutting strike. Draws blood on contact.",
    },
    "concussion": {
        "name": "Concussion Strike",
        "wind_up": 2,
        "stamina_cost": 20,
        "damage_scale": 2.0,
        "shield_pierce": False,
        "applies": [("stun", 1)],
        "preferred_weapon_types": ["bludgeons"],
        "weapon_type_req": ["bludgeons"],
        "skill_req": 20,        # bludgeons skill >= 20 to unlock
        "desc": "A heavy focused blow that stuns the target on contact.",
    },
    "lunge": {
        "name": "Lunge",
        "wind_up": 1,
        "stamina_cost": 16,
        "damage_scale": 1.6,
        "shield_pierce": True,  # 50 % of damage bypasses shield directly to HP
        "applies": [("weakened", 2)],
        "preferred_weapon_types": ["polearms", "blades"],
        "weapon_type_req": ["polearms", "blades"],
        "skill_req": 20,        # polearms or blades >= 20 to unlock
        "desc": "A committed thrust that punches through shield harmonics.",
    },
}


# ---------------------------------------------------------------------------
# Requirement gate (pure, testable)
# ---------------------------------------------------------------------------

def check_technique_requirements(
    technique_name: str,
    equipped_weapon_type: str,
    skills: dict[str, int],
) -> tuple[bool, str]:
    """Check whether a player meets requirements to queue a technique.

    Args:
        technique_name:       Key into TECHNIQUE_DEFS.
        equipped_weapon_type: The ``weapon_type`` field of the main_hand item
                              (empty string for unarmed / no weapon type).
        skills:               The player's ``db.skills`` dict.

    Returns:
        (allowed, reason_or_empty)
        ``allowed`` is True when all requirements are met.
        ``reason`` is a human-readable error string when ``allowed`` is False,
        or an empty string when True.
    """
    defn = TECHNIQUE_DEFS.get(technique_name)
    if not defn:
        return False, f"Unknown technique '{technique_name}'."

    weapon_type_req: list[str] = defn.get("weapon_type_req", [])
    skill_req: int = defn.get("skill_req", 0)

    # --- Weapon-type check --------------------------------------------------
    if weapon_type_req and equipped_weapon_type not in weapon_type_req:
        req_str = " or ".join(weapon_type_req)
        return (
            False,
            f"{defn['name']} requires a {req_str} weapon "
            f"(equipped: {equipped_weapon_type or 'none'}).",
        )

    # --- Skill threshold check ----------------------------------------------
    if skill_req > 0 and weapon_type_req:
        best = max((skills.get(wt, 0) for wt in weapon_type_req), default=0)
        if best < skill_req:
            req_str = "/".join(weapon_type_req)
            return (
                False,
                f"{defn['name']} requires {skill_req} in {req_str} skill "
                f"(you have {best}). Keep fighting with that weapon type to unlock it.",
            )

    return True, ""


# ---------------------------------------------------------------------------
# Resolution
# ---------------------------------------------------------------------------

def resolve_technique(
    attacker: CombatEntity,
    defender: CombatEntity,
    technique_name: str,
    rng: _random_module.Random | None = None,
) -> tuple[CombatResult, list[tuple[str, int]]]:
    """Resolve a fired technique.

    Returns:
        (CombatResult, applied_effects)

    applied_effects is a list of (effect_name, ticks) to apply to the defender.
    It is empty if the attack missed or was fully evaded.
    """
    rand = rng or _random_module
    defn = TECHNIQUE_DEFS.get(technique_name)
    if not defn:
        # Unknown technique — fall back to a plain attack result.
        return (
            CombatResult(
                attacker=attacker.name,
                defender=defender.name,
                action="attack",
                shield_damage=0,
                hp_damage=0,
                stamina_spent=0,
                note="unknown_technique",
            ),
            [],
        )

    cost = defn["stamina_cost"]
    if attacker.stats.stamina < cost:
        return (
            CombatResult(
                attacker=attacker.name,
                defender=defender.name,
                action="attack",
                shield_damage=0,
                hp_damage=0,
                stamina_spent=0,
                note="insufficient_stamina",
            ),
            [],
        )

    attacker.stats.stamina = _clamp_non_negative(attacker.stats.stamina - cost)

    # Hit check — same formula as resolve_attack_passive.
    hit_roll = rand.randint(1, 100)
    if hit_roll > _hit_chance(attacker):
        return (
            CombatResult(
                attacker=attacker.name,
                defender=defender.name,
                action="attack",
                shield_damage=0,
                hp_damage=0,
                stamina_spent=cost,
                note=f"technique_miss:{technique_name}",
            ),
            [],
        )

    # Passive defense check.
    t_avoid, t_dodge, t_parry = _passive_defense_threshold(defender)
    def_roll = rand.randint(1, 100)

    if def_roll <= t_avoid:
        return (
            CombatResult(
                attacker=attacker.name,
                defender=defender.name,
                action="attack",
                shield_damage=0,
                hp_damage=0,
                stamina_spent=cost,
                note=f"technique_avoided:{technique_name}",
            ),
            [],
        )

    if def_roll <= t_dodge:
        defender.stats.stamina = _clamp_non_negative(defender.stats.stamina - 4)
        return (
            CombatResult(
                attacker=attacker.name,
                defender=defender.name,
                action="attack",
                shield_damage=0,
                hp_damage=0,
                stamina_spent=cost,
                note=f"technique_dodged:{technique_name}",
            ),
            [],
        )

    # Hit lands — calculate scaled damage.
    weapon_bonus = getattr(attacker.stats, "weapon_damage_bonus", 0)
    base = 14 + weapon_bonus
    scaled = max(1, int(base * defn["damage_scale"]))

    if def_roll <= t_parry:
        # Parried: half scaled damage, no effects applied.
        defender.stats.stamina = _clamp_non_negative(defender.stats.stamina - 3)
        parried = max(1, scaled // 2)
        sh_dmg, hp_dmg, hit_note = apply_hit(defender, raw_damage=parried, damage_type="melee")
        return (
            CombatResult(
                attacker=attacker.name,
                defender=defender.name,
                action="attack",
                shield_damage=sh_dmg,
                hp_damage=hp_dmg,
                stamina_spent=cost,
                note=f"technique_parried:{technique_name}",
            ),
            [],
        )

    # Full hit.
    if defn["shield_pierce"]:
        # Half damage goes straight to HP, bypassing shield entirely.
        direct_hp = scaled // 2
        remainder = scaled - direct_hp
        sh_dmg, sh_hp, _ = apply_hit(defender, raw_damage=remainder, damage_type="melee")
        defender.stats.hp = _clamp_non_negative(defender.stats.hp - direct_hp)
        hp_dmg = sh_hp + direct_hp
        sh_dmg_total = sh_dmg
        note = f"technique_pierce:{technique_name}"
    else:
        sh_dmg_total, hp_dmg, _ = apply_hit(defender, raw_damage=scaled, damage_type="melee")
        note = f"technique_hit:{technique_name}"

    applied = list(defn.get("applies", []))
    return (
        CombatResult(
            attacker=attacker.name,
            defender=defender.name,
            action="attack",
            shield_damage=sh_dmg_total,
            hp_damage=hp_dmg,
            stamina_spent=cost,
            note=note,
        ),
        applied,
    )
