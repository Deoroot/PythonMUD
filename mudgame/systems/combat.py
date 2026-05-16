"""Melee-focused combat resolver for shield-heavy space setting."""

from __future__ import annotations

import random as _random_module
from dataclasses import dataclass
from typing import Literal

from mudgame.contracts import CharacterStats

Action = Literal["attack", "heavy", "parry", "dodge", "guard", "feint"]
DamageType = Literal["melee", "ranged"]

# Skills auto-grow by use up to this value; spending skill points is needed above it.
SKILL_SOFT_CAP = 60

# Damage bonus applied when a limb has no weapon equipped.
# Results in base attack damage of 14 + (-8) = 6 — noticeably weaker than any weapon.
UNARMED_BONUS = -8

# Hit-chance penalty for the off-hand limb (less natural accuracy).
OFFHAND_HIT_PENALTY = 15


@dataclass(slots=True)
class CombatEntity:
    name: str
    stats: CharacterStats


@dataclass(slots=True)
class CombatResult:
    attacker: str
    defender: str
    action: Action
    shield_damage: int
    hp_damage: int
    stamina_spent: int
    note: str


ACTION_STAMINA_COST: dict[Action, int] = {
    "attack": 0,   # basic attacks are free; stamina is reserved for special actions
    "heavy": 22,
    "parry": 8,
    "dodge": 12,
    "guard": 6,
    "feint": 7,
}

DEFENSE_DAMAGE_MULTIPLIER: dict[Action, float] = {
    "parry": 0.45,
    "dodge": 0.6,
    "guard": 0.75,
    "attack": 1.0,
    "heavy": 1.0,
    "feint": 1.0,
}


def _clamp_non_negative(value: int) -> int:
    return max(0, value)


def _scaled_damage(base_damage: int, defense_action: Action | None, bypass_defense: bool = False) -> int:
    if base_damage <= 0:
        return 0
    if not defense_action or bypass_defense:
        return base_damage
    multiplier = DEFENSE_DAMAGE_MULTIPLIER.get(defense_action, 1.0)
    return max(1, int(base_damage * multiplier))


def apply_hit(
    defender: CombatEntity,
    raw_damage: int,
    damage_type: DamageType = "melee",
) -> tuple[int, int, str]:
    """Apply damage considering shield behavior in this setting.

    Shields heavily suppress ranged damage and partially absorb melee until destabilized.
    """
    if raw_damage <= 0:
        return 0, 0, "no_damage"

    # Apply flat physical damage reduction from defender's armor.
    reduction = getattr(defender.stats, "phys_reduction", 0)
    if reduction > 0 and damage_type == "melee":
        raw_damage = max(1, raw_damage - reduction)

    shield = defender.stats.shield_integrity
    if shield <= 0:
        defender.stats.hp = _clamp_non_negative(defender.stats.hp - raw_damage)
        return 0, raw_damage, "shield_broken"

    if damage_type == "ranged":
        # Ranged is intentionally weak against active shields.
        shield_damage = max(1, raw_damage // 3)
        hp_damage = 0
        note = "ranged_deflected"
    else:
        # Melee can destabilize shields on contact.
        shield_damage = max(1, int(raw_damage * 0.75))
        overflow = max(0, raw_damage - shield)
        hp_damage = overflow
        note = "melee_contact"

    defender.stats.shield_integrity = _clamp_non_negative(shield - shield_damage)
    defender.stats.hp = _clamp_non_negative(defender.stats.hp - hp_damage)
    if defender.stats.shield_integrity == 0:
        note = "shield_broken"
    return shield_damage, hp_damage, note


def resolve_action(attacker: CombatEntity, defender: CombatEntity, action: Action) -> CombatResult:
    """Resolve one combat action with deterministic baseline values."""
    cost = ACTION_STAMINA_COST[action]
    if attacker.stats.stamina < cost:
        return CombatResult(
            attacker=attacker.name,
            defender=defender.name,
            action=action,
            shield_damage=0,
            hp_damage=0,
            stamina_spent=0,
            note="insufficient_stamina",
        )

    attacker.stats.stamina = _clamp_non_negative(attacker.stats.stamina - cost)

    if action in {"parry", "dodge", "guard"}:
        return CombatResult(
            attacker=attacker.name,
            defender=defender.name,
            action=action,
            shield_damage=0,
            hp_damage=0,
            stamina_spent=cost,
            note="defensive_action",
        )

    weapon_bonus = getattr(attacker.stats, "weapon_damage_bonus", 0)
    base_damage = (14 if action == "attack" else 24 if action == "heavy" else 8) + weapon_bonus
    if action == "feint":
        # Feints do little direct damage but tax focus for setup turns.
        defender.stats.focus = _clamp_non_negative(defender.stats.focus - 6)

    shield_damage, hp_damage, note = apply_hit(defender, raw_damage=base_damage, damage_type="melee")
    return CombatResult(
        attacker=attacker.name,
        defender=defender.name,
        action=action,
        shield_damage=shield_damage,
        hp_damage=hp_damage,
        stamina_spent=cost,
        note=note,
    )


def resolve_exchange(
    attacker: CombatEntity,
    defender: CombatEntity,
    attack_action: Action,
    defense_action: Action | None,
) -> CombatResult:
    """Resolve an offensive action against an explicit defensive response.

    This complements `resolve_action` for deterministic duel-style turns.
    """
    if attack_action not in {"attack", "heavy", "feint"}:
        return resolve_action(attacker, defender, attack_action)

    base_result = resolve_action(attacker, defender, attack_action)
    if base_result.note == "insufficient_stamina":
        return base_result

    if defense_action not in {"parry", "dodge", "guard", None}:
        defense_action = None

    if defense_action is None:
        return base_result

    # Roll back and re-apply with mitigation for deterministic defense interactions.
    total_raw = base_result.shield_damage + base_result.hp_damage
    defender.stats.shield_integrity += base_result.shield_damage
    defender.stats.hp += base_result.hp_damage

    bypass_defense = attack_action == "feint"
    mitigated_damage = _scaled_damage(total_raw, defense_action, bypass_defense=bypass_defense)
    shield_damage, hp_damage, note = apply_hit(defender, raw_damage=mitigated_damage, damage_type="melee")

    exchange_note = f"{note}_vs_{defense_action}"
    if bypass_defense:
        exchange_note = f"{note}_feint_bypass"

    return CombatResult(
        attacker=attacker.name,
        defender=defender.name,
        action=attack_action,
        shield_damage=shield_damage,
        hp_damage=hp_damage,
        stamina_spent=base_result.stamina_spent,
        note=exchange_note,
    )


# ---------------------------------------------------------------------------
# Skill-based passive defense resolution
# ---------------------------------------------------------------------------

def _hit_chance(attacker: CombatEntity) -> int:
    """Attacker's percentage chance to land a hit (0-90).

    Stamina adds a small bonus (max +6 at full stamina) so stamina drain
    during combat slightly degrades accuracy over time.

    weapon_type_skill adds up to +25 at skill 100 — specialising in your
    weapon type meaningfully rewards commitment to a fighting style.

    luck_attr adds a small flat bonus (+1 per 5 LUCK above 10; +2 at LUCK 20).
    """
    stamina_bonus = attacker.stats.stamina // 15
    type_bonus = attacker.stats.weapon_type_skill // 4   # 0–25 at skill 100
    luck_bonus = max(0, attacker.stats.luck_attr - 10) // 5  # +1 at LUCK 15, +2 at LUCK 20
    return min(90, 65 + attacker.stats.skill_melee // 2 + stamina_bonus + type_bonus + luck_bonus)


def _passive_defense_threshold(defender: CombatEntity) -> tuple[int, int, int]:
    """Return cumulative percentage thresholds for (avoid, dodge, parry).

    A single random roll 1-100 is compared against these in order:
      roll <= t_avoid  → avoided   (pure stat, no stamina cost)
      roll <= t_dodge  → dodged    (focus + skill_dodge, small stamina cost)
      roll <= t_parry  → parried   (focus + skill_parry, small stamina cost)
      else             → hit lands

    Focus boosts the effective defense skill (Stamina → offensive,
    Focus → defensive, as agreed).

    shield_parry_bonus is added to the parry window when the defender has a
    shield in their off_hand slot.

    luck_attr adds a small flat bonus to the avoid threshold (+1 at LUCK 20).

    off_balance halves the dodge and parry windows (applied after skill
    calculation, before capping) — represents a kicked/destabilised fighter
    struggling to mount a proper defense this round.
    """
    focus_bonus = defender.stats.focus // 12          # 0–4 at default 50 focus
    luck_avoid = max(0, defender.stats.luck_attr - 10) // 10  # +1 at LUCK 20
    t_avoid = min(10, 5 + focus_bonus + luck_avoid)   # max 10 %
    dodge_window = min(30, defender.stats.skill_dodge + focus_bonus)
    parry_window = min(25, defender.stats.skill_parry + focus_bonus)
    parry_window = min(35, parry_window + defender.stats.shield_parry_bonus)  # shield raises cap to 35
    if defender.stats.off_balance:
        dodge_window = dodge_window // 2
        parry_window = parry_window // 2
    t_dodge = t_avoid + dodge_window
    t_parry = t_dodge + parry_window
    return t_avoid, t_dodge, t_parry


def resolve_attack_passive(
    attacker: CombatEntity,
    defender: CombatEntity,
    action: Action,
    damage_type: DamageType = "melee",
    rng: _random_module.Random | None = None,
    hit_penalty: int = 0,
) -> CombatResult:
    """Resolve an offensive action with skill-based hit/miss and passive defense.

    Defense actions (dodge/parry) are automatic: the defender does not choose
    them; they trigger probabilistically based on skill level and Focus.
    Avoid is a small stat-only baseline any combatant has.

    Args:
        rng: Optional seeded Random instance for deterministic tests.
             When None the module-level random is used.
        hit_penalty: Percentage points subtracted from hit chance. Use
             OFFHAND_HIT_PENALTY for the off-hand limb.
    """
    rand = rng or _random_module

    cost = ACTION_STAMINA_COST.get(action, 10)
    if attacker.stats.stamina < cost:
        return CombatResult(
            attacker=attacker.name,
            defender=defender.name,
            action=action,
            shield_damage=0,
            hp_damage=0,
            stamina_spent=0,
            note="insufficient_stamina",
        )

    attacker.stats.stamina = _clamp_non_negative(attacker.stats.stamina - cost)

    # Feint drains defender's focus even if it misses — that's the point.
    if action == "feint":
        defender.stats.focus = _clamp_non_negative(defender.stats.focus - 6)

    # --- Hit check -------------------------------------------------------
    effective_hit_chance = max(5, _hit_chance(attacker) - hit_penalty)
    hit_roll = rand.randint(1, 100)
    if hit_roll > effective_hit_chance:
        return CombatResult(
            attacker=attacker.name,
            defender=defender.name,
            action=action,
            shield_damage=0,
            hp_damage=0,
            stamina_spent=cost,
            note="miss",
        )

    # --- Passive defense check -------------------------------------------
    t_avoid, t_dodge, t_parry = _passive_defense_threshold(defender)
    def_roll = rand.randint(1, 100)

    if def_roll <= t_avoid:
        # Avoid: pure reflex, no stamina cost, no skill growth.
        return CombatResult(
            attacker=attacker.name,
            defender=defender.name,
            action=action,
            shield_damage=0,
            hp_damage=0,
            stamina_spent=cost,
            note="avoided",
        )

    if def_roll <= t_dodge:
        # Dodge: skill-based full evade, small stamina cost on defender.
        defender.stats.stamina = _clamp_non_negative(defender.stats.stamina - 4)
        return CombatResult(
            attacker=attacker.name,
            defender=defender.name,
            action=action,
            shield_damage=0,
            hp_damage=0,
            stamina_spent=cost,
            note="dodged",
        )

    if def_roll <= t_parry:
        # Parry: skill-based partial block — damage reduced by ~50%.
        defender.stats.stamina = _clamp_non_negative(defender.stats.stamina - 3)
        weapon_bonus = getattr(attacker.stats, "weapon_damage_bonus", 0)
        base_damage = (14 if action == "attack" else 24 if action == "heavy" else 8) + weapon_bonus
        parried_damage = max(1, base_damage // 2)
        shield_damage, hp_damage, hit_note = apply_hit(defender, raw_damage=parried_damage, damage_type=damage_type)
        return CombatResult(
            attacker=attacker.name,
            defender=defender.name,
            action=action,
            shield_damage=shield_damage,
            hp_damage=hp_damage,
            stamina_spent=cost,
            note=f"parried_{hit_note}",
        )

    # --- Full hit --------------------------------------------------------
    weapon_bonus = getattr(attacker.stats, "weapon_damage_bonus", 0)
    base_damage = (14 if action == "attack" else 24 if action == "heavy" else 8) + weapon_bonus
    shield_damage, hp_damage, hit_note = apply_hit(defender, raw_damage=base_damage, damage_type=damage_type)
    return CombatResult(
        attacker=attacker.name,
        defender=defender.name,
        action=action,
        shield_damage=shield_damage,
        hp_damage=hp_damage,
        stamina_spent=cost,
        note=hit_note,
    )
