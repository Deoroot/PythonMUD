import random

from mudgame.contracts import CharacterStats
from mudgame.systems.combat import (
    CombatEntity, OFFHAND_HIT_PENALTY, SKILL_SOFT_CAP, UNARMED_BONUS,
    apply_hit, resolve_action, resolve_attack_passive, resolve_exchange,
)


def test_heavy_attack_reduces_shield_significantly():
    attacker = CombatEntity(name="P1", stats=CharacterStats(stamina=100))
    defender = CombatEntity(name="Raider", stats=CharacterStats(shield_integrity=50, hp=100))

    result = resolve_action(attacker, defender, "heavy")

    assert result.shield_damage >= 10
    assert defender.stats.shield_integrity < 50


def test_attack_can_overflow_to_hp_when_shield_breaks():
    attacker = CombatEntity(name="P1", stats=CharacterStats(stamina=100))
    defender = CombatEntity(name="Raider", stats=CharacterStats(shield_integrity=4, hp=100))

    result = resolve_action(attacker, defender, "attack")

    assert result.note == "shield_broken"
    assert result.hp_damage > 0
    assert defender.stats.hp < 100


def test_guard_reduces_incoming_attack_in_exchange():
    attacker = CombatEntity(name="P1", stats=CharacterStats(stamina=100))
    defender_no_guard = CombatEntity(name="Raider", stats=CharacterStats(shield_integrity=100, hp=100))
    defender_guard = CombatEntity(name="Raider", stats=CharacterStats(shield_integrity=100, hp=100))

    normal = resolve_exchange(attacker, defender_no_guard, "heavy", None)
    guarded = resolve_exchange(attacker, defender_guard, "heavy", "guard")

    normal_total = normal.shield_damage + normal.hp_damage
    guarded_total = guarded.shield_damage + guarded.hp_damage
    assert guarded_total < normal_total


def test_feint_partially_bypasses_defense():
    attacker = CombatEntity(name="P1", stats=CharacterStats(stamina=100))
    defender = CombatEntity(name="Raider", stats=CharacterStats(shield_integrity=30, hp=100))

    result = resolve_exchange(attacker, defender, "feint", "parry")
    assert "feint_bypass" in result.note


# ---------------------------------------------------------------------------
# resolve_attack_passive tests
# ---------------------------------------------------------------------------

def _rng_that_always_hits_and_no_defense():
    """Always hit (roll=1 <= any hit_chance), never defend (roll=100 > any threshold)."""
    seq = iter([1, 100])  # hit roll=1 (hits), def roll=100 (no defense)

    class FixedRandom:
        def randint(self, a, b):
            try:
                return next(seq)
            except StopIteration:
                return 100

    return FixedRandom()


def _rng_that_misses():
    class FixedRandom:
        def randint(self, a, b):
            return 100  # always 100 → miss (100 > any hit_chance ≤ 90)

    return FixedRandom()


def _rng_sequence(*values):
    seq = iter(values)

    class FixedRandom:
        def randint(self, a, b):
            return next(seq)

    return FixedRandom()


def test_passive_resolve_full_hit_when_no_defense():
    attacker = CombatEntity(name="P1", stats=CharacterStats(stamina=100, skill_melee=50))
    defender = CombatEntity(name="Raider", stats=CharacterStats(shield_integrity=100, hp=100,
                                                                  skill_dodge=0, skill_parry=0))
    rng = _rng_that_always_hits_and_no_defense()
    result = resolve_attack_passive(attacker, defender, "attack", rng=rng)

    assert result.note not in ("miss", "avoided", "dodged", "insufficient_stamina")
    assert not result.note.startswith("parried")
    assert result.shield_damage + result.hp_damage > 0


def test_passive_resolve_miss_when_roll_too_high():
    attacker = CombatEntity(name="P1", stats=CharacterStats(stamina=100, skill_melee=10))
    defender = CombatEntity(name="Raider", stats=CharacterStats(shield_integrity=100, hp=100))
    rng = _rng_that_misses()
    result = resolve_attack_passive(attacker, defender, "attack", rng=rng)

    assert result.note == "miss"
    assert result.shield_damage == 0
    assert result.hp_damage == 0


def test_passive_resolve_dodge_triggered():
    attacker = CombatEntity(name="P1", stats=CharacterStats(stamina=100, skill_melee=100))
    # Give defender a high dodge skill so the dodge threshold is wide.
    defender = CombatEntity(name="Raider", stats=CharacterStats(
        shield_integrity=100, hp=100, stamina=100, focus=50, skill_dodge=60, skill_parry=0
    ))
    # hit roll=1 (always hits), def roll=15 (should land in dodge bucket since t_avoid≈9, t_dodge=9+30=39)
    rng = _rng_sequence(1, 15)
    result = resolve_attack_passive(attacker, defender, "attack", rng=rng)

    assert result.note == "dodged"
    assert result.shield_damage == 0
    assert result.hp_damage == 0


def test_passive_resolve_parry_reduces_damage():
    attacker = CombatEntity(name="P1", stats=CharacterStats(stamina=100, skill_melee=100))
    defender = CombatEntity(name="Raider", stats=CharacterStats(
        shield_integrity=100, hp=100, stamina=100, focus=50, skill_dodge=0, skill_parry=60
    ))
    # hit roll=1, def roll=50 (beyond avoid+dodge, into parry bucket: t_avoid≈9, t_dodge=9, t_parry=9+25=34 → need 35-59)
    # With skill_dodge=0: t_dodge = 9 + min(30, 0+4) = 9+4 = 13; t_parry = 13 + min(25, 60+4) = 13+25 = 38
    rng = _rng_sequence(1, 35)
    result = resolve_attack_passive(attacker, defender, "attack", rng=rng)

    assert result.note.startswith("parried")
    # Parried damage should be roughly half of full attack (14 base // 2 = 7)
    total = result.shield_damage + result.hp_damage
    assert total <= 10  # half of 14, some may spill as hp


def test_passive_resolve_insufficient_stamina():
    attacker = CombatEntity(name="P1", stats=CharacterStats(stamina=0))
    defender = CombatEntity(name="Raider", stats=CharacterStats())
    # "heavy" costs 22 stamina; attacker has 0 → should be blocked.
    result = resolve_attack_passive(attacker, defender, "heavy")

    assert result.note == "insufficient_stamina"
    assert result.stamina_spent == 0


def test_skill_soft_cap_value():
    assert SKILL_SOFT_CAP == 60


# ---------------------------------------------------------------------------
# Combat style tests
# ---------------------------------------------------------------------------

def test_offhand_hit_penalty_reduces_effective_hit_chance():
    """With OFFHAND_HIT_PENALTY applied, what would be a hit becomes a miss."""
    # Attacker hit chance = 65 + 10//2 + 100//15 = 65 + 5 + 6 = 76.
    # Normal hit: roll 76 → hits (need def roll too → supply 100 = no defense).
    # With penalty 15 → effective = max(5, 76-15)=61 → roll 76 > 61 → miss (no def roll needed).
    attacker = CombatEntity(name="P1", stats=CharacterStats(stamina=100, skill_melee=10))
    defender = CombatEntity(name="Raider", stats=CharacterStats())

    result_no_penalty = resolve_attack_passive(
        attacker, defender, "attack", rng=_rng_sequence(76, 100)
    )
    assert result_no_penalty.note != "miss", "roll 76 should hit without penalty"

    attacker2 = CombatEntity(name="P1", stats=CharacterStats(stamina=100, skill_melee=10))
    defender2 = CombatEntity(name="Raider", stats=CharacterStats())
    result_with_penalty = resolve_attack_passive(
        attacker2, defender2, "attack", rng=_rng_sequence(76), hit_penalty=OFFHAND_HIT_PENALTY
    )
    assert result_with_penalty.note == "miss", "roll 76 should miss with 15-point penalty"


def test_shield_parry_bonus_raises_parry_threshold():
    """A shield in off_hand (shield_parry_bonus=15) widens the parry window."""
    # Defender: skill_dodge=0, skill_parry=10, focus=0 → focus_bonus=0.
    # Without shield: t_avoid=5, t_dodge=5, t_parry=5+10=15.
    # With shield (+15): t_parry=5+min(35, 10+15)=5+25=30.
    # Roll of 20: no shield → hits (20 > 15); with shield → parried (20 ≤ 30).
    attacker = CombatEntity(name="P1", stats=CharacterStats(stamina=100, skill_melee=100))

    defender_no_shield = CombatEntity(name="Raider", stats=CharacterStats(
        shield_integrity=100, hp=100, stamina=100, focus=0,
        skill_dodge=0, skill_parry=10, shield_parry_bonus=0,
    ))
    defender_with_shield = CombatEntity(name="Raider", stats=CharacterStats(
        shield_integrity=100, hp=100, stamina=100, focus=0,
        skill_dodge=0, skill_parry=10, shield_parry_bonus=15,
    ))

    # hit roll=1 (always hits), def roll=20
    result_no_shield = resolve_attack_passive(
        attacker, defender_no_shield, "attack", rng=_rng_sequence(1, 20)
    )
    attacker2 = CombatEntity(name="P1", stats=CharacterStats(stamina=100, skill_melee=100))
    result_with_shield = resolve_attack_passive(
        attacker2, defender_with_shield, "attack", rng=_rng_sequence(1, 20)
    )

    assert not result_no_shield.note.startswith("parried"), "roll 20 should not parry without shield"
    assert result_with_shield.note.startswith("parried"), "roll 20 should parry with shield bonus"


def test_unarmed_bonus_is_negative():
    """UNARMED_BONUS is negative so unarmed damage is notably less than any weapon."""
    assert UNARMED_BONUS < 0


# ---------------------------------------------------------------------------
# Weapon-type skill tests
# ---------------------------------------------------------------------------

def test_weapon_type_skill_increases_hit_chance():
    """Higher weapon_type_skill meaningfully raises the hit% ceiling."""
    # Base hit chance (skill_melee=10, stamina=100, weapon_type_skill=0):
    #   65 + 10//2 + 100//15 + 0//4 = 65 + 5 + 6 + 0 = 76
    # With weapon_type_skill=80:
    #   65 + 5 + 6 + 80//4 = 76 + 20 = 96 → capped at 90
    # Roll of 85: misses at skill=0 (76 < 85), hits at skill=80 (90 >= 85).
    defender = CombatEntity(name="Target", stats=CharacterStats())

    attacker_no_spec = CombatEntity(
        name="P1", stats=CharacterStats(stamina=100, skill_melee=10, weapon_type_skill=0)
    )
    result_no_spec = resolve_attack_passive(
        attacker_no_spec, defender, "attack", rng=_rng_sequence(85, 100)
    )
    assert result_no_spec.note == "miss"

    defender2 = CombatEntity(name="Target", stats=CharacterStats())
    attacker_spec = CombatEntity(
        name="P1", stats=CharacterStats(stamina=100, skill_melee=10, weapon_type_skill=80)
    )
    result_spec = resolve_attack_passive(
        attacker_spec, defender2, "attack", rng=_rng_sequence(85, 100)
    )
    assert result_spec.note != "miss", "high weapon_type_skill should turn a miss into a hit"


def test_weapon_type_skill_capped_at_90_hit_chance():
    """Hit chance never exceeds 90% regardless of weapon_type_skill."""
    # Even with max everything, _hit_chance caps at 90.
    attacker = CombatEntity(
        name="P1", stats=CharacterStats(stamina=100, skill_melee=100, weapon_type_skill=100)
    )
    from mudgame.systems.combat import _hit_chance
    assert _hit_chance(attacker) == 90


# ---------------------------------------------------------------------------
# Physical damage reduction (phys_reduction) tests
# ---------------------------------------------------------------------------

def test_phys_reduction_reduces_incoming_melee_damage():
    """phys_reduction on defender reduces raw melee damage before shield split."""
    # Attacker does a 14-base attack. Defender has phys_reduction=5 → effective raw = 14-5 = 9.
    # Shield absorbs 75% of raw: 9 * 0.75 = 6 (int). No overflow since shield >> raw.
    attacker = CombatEntity(name="P1", stats=CharacterStats(stamina=100))
    defender_no_dr = CombatEntity(name="Target", stats=CharacterStats(shield_integrity=100, hp=100, phys_reduction=0))
    defender_with_dr = CombatEntity(name="Target", stats=CharacterStats(shield_integrity=100, hp=100, phys_reduction=5))

    sh_no, hp_no, _ = apply_hit(defender_no_dr, raw_damage=14, damage_type="melee")
    sh_dr, hp_dr, _ = apply_hit(defender_with_dr, raw_damage=14, damage_type="melee")

    assert sh_dr < sh_no, "phys_reduction should reduce shield damage"
    assert (sh_no + hp_no) > (sh_dr + hp_dr), "total damage should be lower with DR"


def test_phys_reduction_floors_at_1():
    """Even massive DR never reduces damage below 1."""
    defender = CombatEntity(name="Target", stats=CharacterStats(shield_integrity=100, hp=100, phys_reduction=999))

    sh, hp, _ = apply_hit(defender, raw_damage=5, damage_type="melee")

    assert sh + hp >= 1, "damage should never be reduced to 0 by phys_reduction"


def test_phys_reduction_does_not_apply_to_ranged():
    """phys_reduction only reduces melee damage, not ranged."""
    defender_melee = CombatEntity(name="T", stats=CharacterStats(shield_integrity=100, hp=100, phys_reduction=5))
    defender_ranged = CombatEntity(name="T", stats=CharacterStats(shield_integrity=100, hp=100, phys_reduction=5))

    sh_melee, _, _ = apply_hit(defender_melee, raw_damage=10, damage_type="melee")
    sh_ranged, _, _ = apply_hit(defender_ranged, raw_damage=10, damage_type="ranged")

    # Ranged with shield: raw_damage//3 = 3. Melee with DR 5: (10-5)=5 * 0.75 = 3 (same by coincidence).
    # More reliably: check ranged ignores DR by using a large raw_damage.
    defender_r2 = CombatEntity(name="T", stats=CharacterStats(shield_integrity=100, hp=100, phys_reduction=0))
    sh_ranged_no_dr, _, _ = apply_hit(defender_r2, raw_damage=10, damage_type="ranged")
    assert sh_ranged == sh_ranged_no_dr, "phys_reduction must not affect ranged damage"


def test_resolve_attack_passive_supports_ranged_damage_type():
    """Passive resolver should route hits through ranged shield behavior when requested."""

    class _FixedRng:
        def __init__(self):
            self._calls = 0

        @staticmethod
        def _next_roll(calls: int) -> int:
            return 1 if calls == 0 else 100

        def randint(self, _a, _b):
            value = self._next_roll(self._calls)
            self._calls += 1
            return value

    attacker = CombatEntity(
        name="Shooter",
        stats=CharacterStats(stamina=100, skill_melee=100, weapon_damage_bonus=7),
    )
    defender = CombatEntity(
        name="Target",
        stats=CharacterStats(shield_integrity=100, hp=100, phys_reduction=10),
    )

    # attack base raw = 14 + 7 = 21. Ranged against shield => 21//3 = 7 shield damage.
    result = resolve_attack_passive(
        attacker,
        defender,
        "attack",
        damage_type="ranged",
        rng=_FixedRng(),
    )

    assert result.shield_damage == 7
    assert result.hp_damage == 0


# ---------------------------------------------------------------------------
# stats_from_level tests
# ---------------------------------------------------------------------------

def test_stats_from_level_level1():
    """Level 1 mob returns minimum baseline stats."""
    from mudgame.systems.mobs import stats_from_level
    s = stats_from_level(1)
    assert s["hp"] == 27       # 14 + 1*13
    assert s["shield"] == 17   # 4  + 1*13
    assert s["melee"] == 10    # 5  + 1*5
    assert s["dodge"] == 5     # 2  + 1*3
    assert s["parry"] == 3     # 1  + 1*2
    assert s["xp"] == 15       # 1  * 15


def test_stats_from_level_level5():
    """Level 5 should match expected values for glass_stalker tier."""
    from mudgame.systems.mobs import stats_from_level
    s = stats_from_level(5)
    assert s["hp"] == 79       # 14 + 5*13
    assert s["shield"] == 69   # 4  + 5*13
    assert s["melee"] == 30    # 5  + 5*5
    assert s["dodge"] == 17    # 2  + 5*3
    assert s["parry"] == 11    # 1  + 5*2
    assert s["xp"] == 75       # 5  * 15


def test_stats_from_level_clamps_below_1():
    """Levels below 1 are treated as level 1."""
    from mudgame.systems.mobs import stats_from_level
    s0 = stats_from_level(0)
    sm = stats_from_level(-5)
    s1 = stats_from_level(1)
    assert s0 == s1
    assert sm == s1


def test_stats_from_level_scales_linearly():
    """Each level adds a fixed increment to every stat."""
    from mudgame.systems.mobs import stats_from_level
    s2 = stats_from_level(2)
    s3 = stats_from_level(3)
    assert s3["hp"] - s2["hp"] == 13
    assert s3["shield"] - s2["shield"] == 13
    assert s3["melee"] - s2["melee"] == 5
    assert s3["dodge"] - s2["dodge"] == 3
    assert s3["parry"] - s2["parry"] == 2
    assert s3["xp"] - s2["xp"] == 15


# ---------------------------------------------------------------------------
# LUCK stat wiring tests
# ---------------------------------------------------------------------------

def test_luck_bonus_increases_hit_chance():
    """LUCK above 10 adds to hit chance (+1 per 5 LUCK above 10)."""
    from mudgame.systems.combat import _hit_chance

    # Base: skill_melee=10, stamina=100, weapon_type_skill=0, luck_attr=10
    # _hit_chance = min(90, 65 + 5 + 6 + 0 + 0) = 76
    base_attacker = CombatEntity(
        name="P1", stats=CharacterStats(stamina=100, skill_melee=10, weapon_type_skill=0, luck_attr=10)
    )
    # LUCK 15: luck_bonus = (15-10)//5 = 1 → hit chance = 77
    lucky_attacker = CombatEntity(
        name="P2", stats=CharacterStats(stamina=100, skill_melee=10, weapon_type_skill=0, luck_attr=15)
    )
    # LUCK 20: luck_bonus = (20-10)//5 = 2 → hit chance = 78
    very_lucky_attacker = CombatEntity(
        name="P3", stats=CharacterStats(stamina=100, skill_melee=10, weapon_type_skill=0, luck_attr=20)
    )

    base_hit = _hit_chance(base_attacker)
    lucky_hit = _hit_chance(lucky_attacker)
    very_lucky_hit = _hit_chance(very_lucky_attacker)

    assert base_hit == 76
    assert lucky_hit == 77
    assert very_lucky_hit == 78
    assert lucky_hit == base_hit + 1
    assert very_lucky_hit == base_hit + 2


def test_luck_baseline_no_bonus():
    """LUCK at exactly 10 (base) gives zero hit-chance bonus."""
    from mudgame.systems.combat import _hit_chance

    attacker = CombatEntity(
        name="P1", stats=CharacterStats(stamina=100, skill_melee=10, weapon_type_skill=0, luck_attr=10)
    )
    # Should be same as without luck_attr (defaults to 10)
    attacker_default = CombatEntity(
        name="P2", stats=CharacterStats(stamina=100, skill_melee=10, weapon_type_skill=0)
    )
    assert _hit_chance(attacker) == _hit_chance(attacker_default)


def test_luck_avoid_raises_defense_threshold():
    """LUCK above 10 adds to the avoid threshold (+1 at LUCK 20)."""
    from mudgame.systems.combat import _passive_defense_threshold

    # Base: focus=0, luck_attr=10 → focus_bonus=0, luck_avoid=0
    # t_avoid = min(10, 5 + 0 + 0) = 5
    base_defender = CombatEntity(
        name="D1", stats=CharacterStats(focus=0, skill_dodge=0, skill_parry=0, luck_attr=10)
    )
    # LUCK 20: luck_avoid = (20-10)//10 = 1 → t_avoid = min(10, 5+0+1) = 6
    lucky_defender = CombatEntity(
        name="D2", stats=CharacterStats(focus=0, skill_dodge=0, skill_parry=0, luck_attr=20)
    )
    # LUCK 15: luck_avoid = (15-10)//10 = 0 → t_avoid still 5
    mid_defender = CombatEntity(
        name="D3", stats=CharacterStats(focus=0, skill_dodge=0, skill_parry=0, luck_attr=15)
    )

    base_t_avoid, _, _ = _passive_defense_threshold(base_defender)
    lucky_t_avoid, _, _ = _passive_defense_threshold(lucky_defender)
    mid_t_avoid, _, _ = _passive_defense_threshold(mid_defender)

    assert base_t_avoid == 5
    assert mid_t_avoid == 5    # no bonus below LUCK 20
    assert lucky_t_avoid == 6  # +1 at LUCK 20
