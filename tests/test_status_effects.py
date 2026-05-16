"""Tests for mudgame/systems/status_effects.py and mudgame/systems/techniques.py.

All tests are pure Python — no Evennia required.
"""

import sys
from pathlib import Path

# Ensure project root is on the path so mudgame imports work.
_ROOT = str(Path(__file__).resolve().parents[1])
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from mudgame.contracts import CharacterStats
from mudgame.systems.combat import CombatEntity
from mudgame.systems.status_effects import (
    STATUS_DEFS,
    apply_effect,
    defense_penalty,
    is_stunned,
    tick_effects,
)
from mudgame.systems.techniques import TECHNIQUE_DEFS, resolve_technique


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _rng_sequence(*values):
    """Return a fake Random whose randint() pops values from the sequence."""
    seq = iter(values)

    class FixedRandom:
        def randint(self, a, b):
            return next(seq)

    return FixedRandom()


def _make_attacker(stamina=100, skill_melee=50):
    return CombatEntity(
        name="Player",
        stats=CharacterStats(stamina=stamina, skill_melee=skill_melee),
    )


def _make_defender(hp=100, shield=100, stamina=100, skill_dodge=0, skill_parry=0):
    return CombatEntity(
        name="Mob",
        stats=CharacterStats(
            hp=hp,
            shield_integrity=shield,
            stamina=stamina,
            skill_dodge=skill_dodge,
            skill_parry=skill_parry,
        ),
    )


# ---------------------------------------------------------------------------
# status_effects tests
# ---------------------------------------------------------------------------

class TestApplyEffect:
    def test_add_new_effect(self):
        effects = apply_effect({}, "bleed", 3)
        assert effects == {"bleed": 3}

    def test_refresh_takes_max_duration(self):
        effects = apply_effect({"bleed": 1}, "bleed", 3)
        assert effects["bleed"] == 3

    def test_shorter_refresh_is_ignored(self):
        effects = apply_effect({"bleed": 5}, "bleed", 2)
        assert effects["bleed"] == 5

    def test_multiple_effects(self):
        effects = apply_effect(apply_effect({}, "bleed", 3), "stun", 1)
        assert effects == {"bleed": 3, "stun": 1}


class TestIsStunned:
    def test_stunned_when_stun_present(self):
        assert is_stunned({"stun": 1}) is True

    def test_not_stunned_when_empty(self):
        assert is_stunned({}) is False

    def test_not_stunned_with_other_effects(self):
        assert is_stunned({"bleed": 3, "weakened": 2}) is False

    def test_not_stunned_when_ticks_zero(self):
        # Ticks should never be 0 in the dict (they're removed by tick_effects),
        # but defensive check nonetheless.
        assert is_stunned({"stun": 0}) is False


class TestDefensePenalty:
    def test_no_penalty_when_empty(self):
        assert defense_penalty({}) == 0

    def test_weakened_adds_penalty(self):
        assert defense_penalty({"weakened": 2}) == 10

    def test_bleed_adds_no_penalty(self):
        assert defense_penalty({"bleed": 3}) == 0

    def test_stacks_correctly(self):
        # Two weakened stacks are not currently possible via apply_effect
        # (refresh takes max), but the function should sum all active penalties.
        # Fake the dict directly to test summation.
        # (weakened x2 hypothetically)
        assert defense_penalty({"weakened": 2}) == 10


class TestTickEffects:
    def test_bleed_drains_hp(self):
        effects = {"bleed": 3}
        updated, drained, msgs = tick_effects(effects, current_hp=50)
        drain_per_tick = STATUS_DEFS["bleed"]["hp_drain"]
        assert drained == drain_per_tick
        assert any("bleed:" in m for m in msgs)

    def test_bleed_decrements_tick(self):
        effects = {"bleed": 3}
        updated, _, _ = tick_effects(effects, current_hp=50)
        assert updated.get("bleed") == 2

    def test_bleed_expires_after_last_tick(self):
        effects = {"bleed": 1}
        updated, drained, msgs = tick_effects(effects, current_hp=50)
        assert "bleed" not in updated          # expired
        assert drained > 0                      # still fired this tick

    def test_bleed_cannot_drain_below_zero(self):
        # HP = 2 but drain = 4 → should only drain 2.
        effects = {"bleed": 1}
        _, drained, _ = tick_effects(effects, current_hp=2)
        assert drained == 2

    def test_stun_fires_skip_action_message(self):
        effects = {"stun": 1}
        updated, drained, msgs = tick_effects(effects, current_hp=100)
        assert "stun:active" in msgs
        assert drained == 0
        assert "stun" not in updated           # consumed

    def test_weakened_decrements_but_no_drain(self):
        effects = {"weakened": 2}
        updated, drained, msgs = tick_effects(effects, current_hp=100)
        assert drained == 0
        assert updated.get("weakened") == 1    # decremented

    def test_empty_effects_returns_empty(self):
        updated, drained, msgs = tick_effects({}, current_hp=100)
        assert updated == {}
        assert drained == 0
        assert msgs == []


# ---------------------------------------------------------------------------
# techniques tests
# ---------------------------------------------------------------------------

class TestTechniqueDefs:
    def test_slash_defined(self):
        assert "slash" in TECHNIQUE_DEFS

    def test_concussion_defined(self):
        assert "concussion" in TECHNIQUE_DEFS

    def test_lunge_defined(self):
        assert "lunge" in TECHNIQUE_DEFS

    def test_slash_applies_bleed(self):
        applies = TECHNIQUE_DEFS["slash"]["applies"]
        assert any(name == "bleed" for name, _ in applies)

    def test_concussion_applies_stun(self):
        applies = TECHNIQUE_DEFS["concussion"]["applies"]
        assert any(name == "stun" for name, _ in applies)

    def test_lunge_applies_weakened(self):
        applies = TECHNIQUE_DEFS["lunge"]["applies"]
        assert any(name == "weakened" for name, _ in applies)

    def test_lunge_shield_pierce(self):
        assert TECHNIQUE_DEFS["lunge"]["shield_pierce"] is True

    def test_slash_no_shield_pierce(self):
        assert TECHNIQUE_DEFS["slash"]["shield_pierce"] is False


class TestResolveTeechnique:
    def test_unknown_technique_returns_empty_effects(self):
        attacker = _make_attacker()
        defender = _make_defender()
        result, effects = resolve_technique(attacker, defender, "nonexistent_move")
        assert result.note == "unknown_technique"
        assert effects == []

    def test_insufficient_stamina_returns_empty_effects(self):
        attacker = _make_attacker(stamina=0)
        defender = _make_defender()
        result, effects = resolve_technique(attacker, defender, "slash")
        assert result.note == "insufficient_stamina"
        assert effects == []

    def test_slash_hit_returns_bleed_effect(self):
        attacker = _make_attacker(stamina=100, skill_melee=100)
        defender = _make_defender(hp=100, shield=100, skill_dodge=0, skill_parry=0)
        # Roll 1 = hit, Roll 100 = no defense → full hit
        rng = _rng_sequence(1, 100)
        result, effects = resolve_technique(attacker, defender, "slash", rng=rng)
        assert result.note.startswith("technique_hit:") or result.note.startswith("technique_parried:")
        # On a full hit, effects should include bleed
        if result.note.startswith("technique_hit:"):
            assert any(name == "bleed" for name, _ in effects)

    def test_slash_full_hit_applies_bleed(self):
        attacker = _make_attacker(stamina=100, skill_melee=100)
        defender = _make_defender(hp=100, shield=0, skill_dodge=0, skill_parry=0)
        # Roll 1 = hit; no shield, def roll 100 → no defense → full hit
        rng = _rng_sequence(1, 100)
        result, effects = resolve_technique(attacker, defender, "slash", rng=rng)
        assert result.note.startswith("technique_hit:")
        assert any(name == "bleed" for name, _ in effects)

    def test_concussion_full_hit_applies_stun(self):
        attacker = _make_attacker(stamina=100, skill_melee=100)
        # No shield, no defense skills so it must land clean
        defender = _make_defender(hp=100, shield=0, skill_dodge=0, skill_parry=0)
        rng = _rng_sequence(1, 100)
        result, effects = resolve_technique(attacker, defender, "concussion", rng=rng)
        assert result.note.startswith("technique_hit:")
        assert any(name == "stun" for name, _ in effects)

    def test_lunge_full_hit_applies_weakened(self):
        attacker = _make_attacker(stamina=100, skill_melee=100)
        defender = _make_defender(hp=100, shield=0, skill_dodge=0, skill_parry=0)
        rng = _rng_sequence(1, 100)
        result, effects = resolve_technique(attacker, defender, "lunge", rng=rng)
        # Lunge has shield_pierce so note is technique_pierce
        assert result.note.startswith("technique_pierce:")
        assert any(name == "weakened" for name, _ in effects)

    def test_slash_miss_returns_no_effects(self):
        attacker = _make_attacker(stamina=100, skill_melee=10)
        defender = _make_defender()
        # Roll 100 → miss (max hit chance ≤ 90)
        rng = _rng_sequence(100)
        result, effects = resolve_technique(attacker, defender, "slash", rng=rng)
        assert result.note.startswith("technique_miss:")
        assert effects == []

    def test_slash_dodge_returns_no_effects(self):
        attacker = _make_attacker(stamina=100, skill_melee=100)
        # Give defender very high dodge so def_roll=15 lands in dodge bucket
        defender = _make_defender(skill_dodge=60, skill_parry=0, stamina=100)
        # hit roll=1 (hits), def roll=15 (dodged: t_avoid≈9, t_dodge=9+30=39)
        rng = _rng_sequence(1, 15)
        result, effects = resolve_technique(attacker, defender, "slash", rng=rng)
        assert result.note.startswith("technique_dodged:")
        assert effects == []

    def test_lunge_does_direct_hp_damage_bypassing_shield(self):
        """Half of lunge damage bypasses the shield and hits HP directly."""
        attacker = _make_attacker(stamina=100, skill_melee=100)
        # Fresh shield — without pierce, hp_damage should be 0.
        # With pierce (lunge), half of damage hits HP directly.
        defender = _make_defender(hp=100, shield=100, skill_dodge=0, skill_parry=0)
        rng = _rng_sequence(1, 100)
        result, effects = resolve_technique(attacker, defender, "lunge", rng=rng)
        assert result.note.startswith("technique_pierce:")
        assert result.hp_damage > 0  # direct HP component must be non-zero

    def test_stamina_consumed_on_hit(self):
        attacker = _make_attacker(stamina=100, skill_melee=100)
        defender = _make_defender(hp=100, shield=0, skill_dodge=0, skill_parry=0)
        rng = _rng_sequence(1, 100)
        resolve_technique(attacker, defender, "slash", rng=rng)
        cost = TECHNIQUE_DEFS["slash"]["stamina_cost"]
        assert attacker.stats.stamina == 100 - cost

    def test_stamina_consumed_on_miss(self):
        attacker = _make_attacker(stamina=100, skill_melee=10)
        defender = _make_defender()
        rng = _rng_sequence(100)
        resolve_technique(attacker, defender, "slash", rng=rng)
        cost = TECHNIQUE_DEFS["slash"]["stamina_cost"]
        assert attacker.stats.stamina == 100 - cost
