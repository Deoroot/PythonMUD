"""Tests for stat→pool wiring, off_balance status, and kick damage formula.

All tests are pure Python — no Evennia required.
"""

import sys
from pathlib import Path

_ROOT = str(Path(__file__).resolve().parents[1])
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from mudgame.contracts import CharacterStats
from mudgame.systems.combat import CombatEntity, _passive_defense_threshold
from mudgame.systems.status_effects import STATUS_DEFS, apply_effect, tick_effects


# ---------------------------------------------------------------------------
# CharacterStats — off_balance default
# ---------------------------------------------------------------------------

class TestOffBalanceDefault:
    def test_off_balance_defaults_to_false(self):
        stats = CharacterStats()
        assert stats.off_balance is False

    def test_off_balance_can_be_set_true(self):
        stats = CharacterStats(off_balance=True)
        assert stats.off_balance is True


# ---------------------------------------------------------------------------
# STATUS_DEFS — off_balance entry
# ---------------------------------------------------------------------------

class TestOffBalanceStatusDef:
    def test_off_balance_in_status_defs(self):
        assert "off_balance" in STATUS_DEFS

    def test_off_balance_has_no_hp_drain(self):
        assert STATUS_DEFS["off_balance"]["hp_drain"] == 0

    def test_off_balance_does_not_skip_action(self):
        assert STATUS_DEFS["off_balance"]["skip_action"] is False

    def test_off_balance_has_no_defense_penalty(self):
        # defense_penalty handled separately via CharacterStats.off_balance
        assert STATUS_DEFS["off_balance"]["defense_penalty"] == 0

    def test_off_balance_apply_effect_sets_one_tick(self):
        effects = apply_effect({}, "off_balance", 1)
        assert effects["off_balance"] == 1

    def test_off_balance_expires_after_tick(self):
        effects = {"off_balance": 1}
        updated, drained, msgs = tick_effects(effects, current_hp=100)
        assert "off_balance" not in updated
        assert drained == 0


# ---------------------------------------------------------------------------
# _passive_defense_threshold — off_balance halves dodge+parry windows
# ---------------------------------------------------------------------------

def _make_defender(skill_dodge=20, skill_parry=20, focus=50, shield_parry_bonus=0,
                   off_balance=False):
    return CombatEntity(
        name="Defender",
        stats=CharacterStats(
            skill_dodge=skill_dodge,
            skill_parry=skill_parry,
            focus=focus,
            shield_parry_bonus=shield_parry_bonus,
            off_balance=off_balance,
        ),
    )


class TestPassiveDefenseThresholdOffBalance:
    def test_off_balance_false_produces_normal_thresholds(self):
        normal = _make_defender(skill_dodge=20, skill_parry=20, focus=0)
        t_avoid, t_dodge, t_parry = _passive_defense_threshold(normal)
        # focus=0 → focus_bonus=0; avoid=5; dodge window=min(30,20)=20 → t_dodge=25
        # parry window=min(25,20)=20 → t_parry=45
        assert t_avoid == 5
        assert t_dodge == 25
        assert t_parry == 45

    def test_off_balance_true_halves_dodge_window(self):
        off = _make_defender(skill_dodge=20, skill_parry=20, focus=0, off_balance=True)
        t_avoid, t_dodge, t_parry = _passive_defense_threshold(off)
        # dodge window normally 20, halved → 10; avoid=5 → t_dodge=15
        assert t_dodge == t_avoid + 10

    def test_off_balance_true_halves_parry_window(self):
        off = _make_defender(skill_dodge=20, skill_parry=20, focus=0, off_balance=True)
        t_avoid, t_dodge, t_parry = _passive_defense_threshold(off)
        # parry window normally 20, halved → 10
        assert t_parry == t_dodge + 10

    def test_off_balance_does_not_affect_avoid_threshold(self):
        normal = _make_defender(focus=0)
        off = _make_defender(focus=0, off_balance=True)
        t_avoid_n, _, _ = _passive_defense_threshold(normal)
        t_avoid_o, _, _ = _passive_defense_threshold(off)
        assert t_avoid_n == t_avoid_o

    def test_off_balance_combined_with_shield(self):
        """Shield parry bonus is still halved when off_balance."""
        off = _make_defender(
            skill_dodge=20, skill_parry=20, focus=0,
            shield_parry_bonus=15, off_balance=True,
        )
        t_avoid, t_dodge, t_parry = _passive_defense_threshold(off)
        # parry window = min(35, 20+15) = 35; halved → 17
        assert t_parry == t_dodge + 17

    def test_off_balance_total_is_lower_than_normal(self):
        normal = _make_defender(skill_dodge=30, skill_parry=25, focus=60)
        off = _make_defender(skill_dodge=30, skill_parry=25, focus=60, off_balance=True)
        _, _, t_parry_n = _passive_defense_threshold(normal)
        _, _, t_parry_o = _passive_defense_threshold(off)
        assert t_parry_o < t_parry_n

    def test_off_balance_zero_skill_stays_zero(self):
        """off_balance on a 0-skill defender doesn't produce negative windows."""
        off = _make_defender(skill_dodge=0, skill_parry=0, focus=0, off_balance=True)
        t_avoid, t_dodge, t_parry = _passive_defense_threshold(off)
        assert t_dodge >= t_avoid
        assert t_parry >= t_dodge


# ---------------------------------------------------------------------------
# Kick damage formula (pure math, no Evennia)
# ---------------------------------------------------------------------------

def _kick_damage(str_attr: int) -> int:
    """Mirror the CmdKick damage formula for testing."""
    return 5 + max(0, (str_attr - 10) // 3)


class TestKickDamageFormula:
    def test_base_str_10_deals_5_damage(self):
        assert _kick_damage(10) == 5

    def test_str_13_deals_6_damage(self):
        assert _kick_damage(13) == 6  # (13-10)//3 = 1

    def test_str_16_deals_7_damage(self):
        assert _kick_damage(16) == 7  # (16-10)//3 = 2

    def test_str_below_10_still_deals_base_5(self):
        assert _kick_damage(8) == 5   # max(0, ...) clamps negative

    def test_str_25_deals_10_damage(self):
        assert _kick_damage(25) == 10  # (25-10)//3 = 5


# ---------------------------------------------------------------------------
# Regen gain formulas (pure math, no Evennia)
# ---------------------------------------------------------------------------

def _stamina_regen(dex: int) -> int:
    return 3 + max(0, (dex - 10) // 4)


def _shield_regen(mind: int) -> int:
    return 1 + max(0, (mind - 10) // 5)


class TestRegenFormulas:
    def test_stamina_regen_base_dex_10(self):
        assert _stamina_regen(10) == 3

    def test_stamina_regen_dex_14(self):
        assert _stamina_regen(14) == 4  # (14-10)//4=1

    def test_stamina_regen_dex_18(self):
        assert _stamina_regen(18) == 5  # (18-10)//4=2

    def test_stamina_regen_dex_below_10(self):
        assert _stamina_regen(8) == 3   # clamped at base

    def test_shield_regen_base_mind_10(self):
        assert _shield_regen(10) == 1

    def test_shield_regen_mind_15(self):
        assert _shield_regen(15) == 2   # (15-10)//5=1

    def test_shield_regen_mind_20(self):
        assert _shield_regen(20) == 3   # (20-10)//5=2

    def test_shield_regen_mind_below_10(self):
        assert _shield_regen(8) == 1    # clamped at base


# ---------------------------------------------------------------------------
# Pool max bonus formulas (pure math, no Evennia)
# ---------------------------------------------------------------------------

def _hp_max(level: int, con: int) -> int:
    return 100 + (level - 1) * 10 + max(0, con - 10) * 3


def _stamina_max(level: int, dex: int, con: int) -> int:
    return 100 + (level - 1) * 8 + max(0, dex - 10) * 3 + max(0, con - 10) * 2


def _shield_max(level: int, mind: int) -> int:
    return 100 + (level - 1) * 10 + max(0, mind - 10) * 4


def _focus_max(level: int, per: int) -> int:
    return 50 + (level - 1) * 5 + max(0, per - 10) * 2


class TestPoolMaxFormulas:
    def test_hp_max_base_at_level1_con10(self):
        assert _hp_max(1, 10) == 100

    def test_hp_max_level5_con10(self):
        assert _hp_max(5, 10) == 140  # 100 + 4*10

    def test_hp_max_level1_con14(self):
        assert _hp_max(1, 14) == 112  # 100 + 4*3

    def test_hp_max_level5_con14(self):
        assert _hp_max(5, 14) == 152  # 100 + 40 + 12

    def test_stamina_max_base(self):
        assert _stamina_max(1, 10, 10) == 100

    def test_stamina_max_level5_all10(self):
        assert _stamina_max(5, 10, 10) == 132  # 100 + 4*8

    def test_stamina_max_dex14_con12(self):
        # 100 + 3*(14-10) + 2*(12-10) = 100 + 12 + 4 = 116
        assert _stamina_max(1, 14, 12) == 116

    def test_shield_max_base(self):
        assert _shield_max(1, 10) == 100

    def test_shield_max_mind15(self):
        assert _shield_max(1, 15) == 120  # 100 + 5*4

    def test_focus_max_base(self):
        assert _focus_max(1, 10) == 50

    def test_focus_max_per12(self):
        assert _focus_max(1, 12) == 54   # 50 + 2*2

    def test_con_below_10_no_hp_bonus(self):
        assert _hp_max(1, 8) == 100

    def test_dex_below_10_no_stamina_bonus(self):
        assert _stamina_max(1, 8, 10) == 100
