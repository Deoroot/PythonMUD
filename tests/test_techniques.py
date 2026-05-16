"""Tests for technique definitions and the weapon-type/skill gate."""

import random

import pytest

from mudgame.contracts import CharacterStats
from mudgame.systems.combat import CombatEntity
from mudgame.systems.techniques import (
    TECHNIQUE_DEFS,
    check_technique_requirements,
    resolve_technique,
)


# ---------------------------------------------------------------------------
# check_technique_requirements
# ---------------------------------------------------------------------------

class TestCheckTechniqueRequirements:
    """Gate checks for technique availability."""

    def test_slash_allowed_with_blades_and_sufficient_skill(self):
        allowed, reason = check_technique_requirements(
            "slash", "blades", {"blades": 20}
        )
        assert allowed is True
        assert reason == ""

    def test_slash_blocked_wrong_weapon_type(self):
        allowed, reason = check_technique_requirements(
            "slash", "bludgeons", {"bludgeons": 30}
        )
        assert allowed is False
        assert "blades" in reason

    def test_slash_blocked_unarmed(self):
        allowed, reason = check_technique_requirements(
            "slash", "", {"blades": 25}
        )
        assert allowed is False
        assert "blades" in reason

    def test_slash_blocked_skill_too_low(self):
        allowed, reason = check_technique_requirements(
            "slash", "blades", {"blades": 19}
        )
        assert allowed is False
        assert "19" in reason or "20" in reason

    def test_slash_allowed_at_exact_threshold(self):
        allowed, _ = check_technique_requirements(
            "slash", "blades", {"blades": 20}
        )
        assert allowed is True

    def test_concussion_requires_bludgeons(self):
        allowed, reason = check_technique_requirements(
            "concussion", "blades", {"blades": 40}
        )
        assert allowed is False
        assert "bludgeons" in reason

    def test_concussion_allowed(self):
        allowed, _ = check_technique_requirements(
            "concussion", "bludgeons", {"bludgeons": 20}
        )
        assert allowed is True

    def test_lunge_allowed_with_polearms(self):
        allowed, _ = check_technique_requirements(
            "lunge", "polearms", {"polearms": 20}
        )
        assert allowed is True

    def test_lunge_allowed_with_blades(self):
        allowed, _ = check_technique_requirements(
            "lunge", "blades", {"blades": 20}
        )
        assert allowed is True

    def test_lunge_blocked_wrong_type(self):
        allowed, reason = check_technique_requirements(
            "lunge", "bludgeons", {"bludgeons": 40}
        )
        assert allowed is False

    def test_lunge_uses_best_qualifying_skill(self):
        """If lunge allows polearms+blades, best of both must meet threshold."""
        # blades=15, polearms=22 — polearms satisfies
        allowed, _ = check_technique_requirements(
            "lunge", "polearms", {"polearms": 22, "blades": 15}
        )
        assert allowed is True

    def test_unknown_technique_returns_false(self):
        allowed, reason = check_technique_requirements(
            "nonexistent", "blades", {"blades": 30}
        )
        assert allowed is False
        assert "nonexistent" in reason

    def test_missing_skill_key_treated_as_zero(self):
        """Skills dict with no entry for the weapon type defaults to 0."""
        allowed, reason = check_technique_requirements(
            "slash", "blades", {}
        )
        assert allowed is False


# ---------------------------------------------------------------------------
# TECHNIQUE_DEFS schema
# ---------------------------------------------------------------------------

class TestTechniqueDefsSchema:
    """Each technique entry must have required keys and sensible values."""

    @pytest.mark.parametrize("name", list(TECHNIQUE_DEFS))
    def test_required_keys_present(self, name):
        defn = TECHNIQUE_DEFS[name]
        for key in ("name", "wind_up", "stamina_cost", "damage_scale",
                    "shield_pierce", "applies", "weapon_type_req", "skill_req", "desc"):
            assert key in defn, f"{name} missing key '{key}'"

    @pytest.mark.parametrize("name", list(TECHNIQUE_DEFS))
    def test_skill_req_positive(self, name):
        assert TECHNIQUE_DEFS[name]["skill_req"] > 0

    @pytest.mark.parametrize("name", list(TECHNIQUE_DEFS))
    def test_weapon_type_req_nonempty(self, name):
        assert len(TECHNIQUE_DEFS[name]["weapon_type_req"]) > 0


# ---------------------------------------------------------------------------
# resolve_technique — quick smoke tests
# ---------------------------------------------------------------------------

class _AlwaysHitRng:
    """Returns 1 for the hit roll (always hits) and 100 for defense (no defense)."""
    _seq = [1, 100]
    _i = 0

    def randint(self, a, b):
        v = self._seq[self._i % 2]
        self._i += 1
        return v


def _make_entities(attacker_stamina=80, defender_hp=100, defender_shield=50):
    a_stats = CharacterStats(stamina=attacker_stamina, weapon_damage_bonus=5)
    d_stats = CharacterStats(hp=defender_hp, shield_integrity=defender_shield, stamina=50)
    return (
        CombatEntity(name="Player", stats=a_stats),
        CombatEntity(name="Mob", stats=d_stats),
    )


def test_slash_applies_bleed_on_hit():
    attacker, defender = _make_entities()
    _, effects = resolve_technique(attacker, defender, "slash", rng=_AlwaysHitRng())
    assert any(name == "bleed" for name, _ in effects)


def test_concussion_applies_stun_on_hit():
    attacker, defender = _make_entities()
    _, effects = resolve_technique(attacker, defender, "concussion", rng=_AlwaysHitRng())
    assert any(name == "stun" for name, _ in effects)


def test_lunge_applies_weakened_on_hit():
    attacker, defender = _make_entities()
    _, effects = resolve_technique(attacker, defender, "lunge", rng=_AlwaysHitRng())
    assert any(name == "weakened" for name, _ in effects)


def test_technique_insufficient_stamina_returns_note():
    attacker, defender = _make_entities(attacker_stamina=5)
    result, effects = resolve_technique(attacker, defender, "slash")
    assert result.note == "insufficient_stamina"
    assert effects == []
