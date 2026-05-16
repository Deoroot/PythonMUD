"""Tests for PSI ability definitions and pure resolution functions."""

from __future__ import annotations

import pytest

from mudgame.systems.psi import (
    PSI_ABILITY_DEFS,
    resolve_psi_heal,
    resolve_psi_shock,
    resolve_psi_ward,
    resolve_psi_bolt,
    resolve_psi_shatter,
    resolve_sleep_psi_restore,
)


# ---------------------------------------------------------------------------
# Schema tests — PSI_ABILITY_DEFS
# ---------------------------------------------------------------------------

class TestPsiAbilityDefs:
    """Validate the shape of PSI_ABILITY_DEFS entries."""

    def test_heal_defined(self):
        assert "heal" in PSI_ABILITY_DEFS

    def test_shock_defined(self):
        assert "shock" in PSI_ABILITY_DEFS

    def test_all_abilities_have_required_keys(self):
        required = {"name", "psi_cost", "target", "combat_only", "desc"}
        for name, defn in PSI_ABILITY_DEFS.items():
            missing = required - defn.keys()
            assert not missing, f"Ability '{name}' missing keys: {missing}"

    def test_heal_psi_cost(self):
        assert PSI_ABILITY_DEFS["heal"]["psi_cost"] == 20

    def test_shock_psi_cost(self):
        assert PSI_ABILITY_DEFS["shock"]["psi_cost"] == 25

    def test_heal_targets_self(self):
        assert PSI_ABILITY_DEFS["heal"]["target"] == "self"

    def test_shock_targets_enemy(self):
        assert PSI_ABILITY_DEFS["shock"]["target"] == "enemy"

    def test_heal_not_combat_only(self):
        assert PSI_ABILITY_DEFS["heal"]["combat_only"] is False

    def test_shock_is_combat_only(self):
        assert PSI_ABILITY_DEFS["shock"]["combat_only"] is True

    def test_all_psi_costs_are_positive(self):
        for name, defn in PSI_ABILITY_DEFS.items():
            assert defn["psi_cost"] > 0, f"'{name}' has non-positive psi_cost"


# ---------------------------------------------------------------------------
# resolve_psi_heal
# ---------------------------------------------------------------------------

class TestResolvePsiHeal:
    """Pure logic tests for PSI Heal."""

    def test_base_mind_heal_amount(self):
        # MIND=10 → heal 10 HP.
        new_psi, gained, note = resolve_psi_heal(
            psi=60, psi_max=60, mind=10, hp=50, hp_max=100
        )
        assert note == "healed"
        assert gained == 10
        assert new_psi == 40   # 60 - 20 cost

    def test_elevated_mind_heal_scales(self):
        # MIND=15 → heal 10 + (15-10)*2 = 20 HP.
        new_psi, gained, note = resolve_psi_heal(
            psi=60, psi_max=60, mind=15, hp=50, hp_max=100
        )
        assert note == "healed"
        assert gained == 20
        assert new_psi == 40

    def test_high_mind_heal_scales(self):
        # MIND=20 → heal 10 + (20-10)*2 = 30 HP.
        new_psi, gained, note = resolve_psi_heal(
            psi=60, psi_max=60, mind=20, hp=30, hp_max=100
        )
        assert note == "healed"
        assert gained == 30

    def test_heal_capped_by_hp_max(self):
        # Only 5 HP missing — can't overheal.
        new_psi, gained, note = resolve_psi_heal(
            psi=60, psi_max=60, mind=10, hp=95, hp_max=100
        )
        assert note == "healed"
        assert gained == 5

    def test_heal_already_full_psi_not_spent(self):
        new_psi, gained, note = resolve_psi_heal(
            psi=60, psi_max=60, mind=10, hp=100, hp_max=100
        )
        assert note == "already_full"
        assert gained == 0
        assert new_psi == 60   # PSI unchanged

    def test_heal_insufficient_psi(self):
        new_psi, gained, note = resolve_psi_heal(
            psi=19, psi_max=60, mind=10, hp=50, hp_max=100
        )
        assert note == "insufficient_psi"
        assert gained == 0
        assert new_psi == 19   # PSI unchanged

    def test_heal_exact_psi_cost(self):
        # Exactly 20 PSI — should succeed.
        new_psi, gained, note = resolve_psi_heal(
            psi=20, psi_max=60, mind=10, hp=50, hp_max=100
        )
        assert note == "healed"
        assert new_psi == 0

    def test_heal_zero_psi(self):
        new_psi, gained, note = resolve_psi_heal(
            psi=0, psi_max=60, mind=10, hp=50, hp_max=100
        )
        assert note == "insufficient_psi"

    def test_heal_does_not_exceed_hp_max(self):
        # Big heal (MIND=30 → 10+(30-10)*2=50) but only 15 HP missing.
        new_psi, gained, note = resolve_psi_heal(
            psi=60, psi_max=60, mind=30, hp=85, hp_max=100
        )
        assert note == "healed"
        assert gained == 15
        assert gained <= 100 - 85  # must not exceed missing HP


# ---------------------------------------------------------------------------
# resolve_psi_shock
# ---------------------------------------------------------------------------

class TestResolvePsiShock:
    """Pure logic tests for PSI Shock."""

    def test_base_mind_total_damage(self):
        # MIND=10 → damage=8. All absorbed by shield (shield=50).
        new_psi, sh, hp, note = resolve_psi_shock(
            psi=60, mind=10, defender_shield=50, defender_hp=40
        )
        assert note == "shocked"
        assert sh + hp == 8
        assert new_psi == 35   # 60 - 25 cost

    def test_elevated_mind_scales_damage(self):
        # MIND=15 → 8 + (15-10)*3 = 23 damage.
        new_psi, sh, hp, note = resolve_psi_shock(
            psi=60, mind=15, defender_shield=50, defender_hp=40
        )
        assert note == "shocked"
        assert sh + hp == 23

    def test_high_mind_scales_damage(self):
        # MIND=20 → 8 + (20-10)*3 = 38 damage.
        new_psi, sh, hp, note = resolve_psi_shock(
            psi=60, mind=20, defender_shield=50, defender_hp=40
        )
        assert note == "shocked"
        assert sh + hp == 38

    def test_shield_absorbs_first(self):
        # shield=5, damage=8 → sh_dmg=5, hp_dmg=3.
        new_psi, sh, hp, note = resolve_psi_shock(
            psi=60, mind=10, defender_shield=5, defender_hp=40
        )
        assert note == "shocked"
        assert sh == 5
        assert hp == 3

    def test_no_shield_all_damage_to_hp(self):
        # shield=0, damage=8 → sh_dmg=0, hp_dmg=8.
        new_psi, sh, hp, note = resolve_psi_shock(
            psi=60, mind=10, defender_shield=0, defender_hp=40
        )
        assert note == "shocked"
        assert sh == 0
        assert hp == 8

    def test_shield_fully_absorbs(self):
        # Large shield — all damage absorbed, no HP damage.
        new_psi, sh, hp, note = resolve_psi_shock(
            psi=60, mind=10, defender_shield=100, defender_hp=40
        )
        assert note == "shocked"
        assert sh == 8
        assert hp == 0

    def test_insufficient_psi_nothing_changes(self):
        new_psi, sh, hp, note = resolve_psi_shock(
            psi=24, mind=10, defender_shield=50, defender_hp=40
        )
        assert note == "insufficient_psi"
        assert sh == 0
        assert hp == 0
        assert new_psi == 24   # unchanged

    def test_zero_psi_blocked(self):
        new_psi, sh, hp, note = resolve_psi_shock(
            psi=0, mind=10, defender_shield=50, defender_hp=40
        )
        assert note == "insufficient_psi"

    def test_exact_psi_cost_succeeds(self):
        new_psi, sh, hp, note = resolve_psi_shock(
            psi=25, mind=10, defender_shield=50, defender_hp=40
        )
        assert note == "shocked"
        assert new_psi == 0

    def test_damage_distribution_sums_correctly(self):
        # sh_dmg + hp_dmg must always equal total raw damage.
        for mind in [10, 12, 15, 18, 20]:
            for shield in [0, 4, 8, 50]:
                _, sh, hp, note = resolve_psi_shock(
                    psi=100, mind=mind, defender_shield=shield, defender_hp=100
                )
                if note == "shocked":
                    expected_raw = 8 + max(0, (mind - 10) * 3)
                    assert sh + hp == expected_raw, (
                        f"mind={mind} shield={shield}: sh+hp={sh+hp} != {expected_raw}"
                    )


# ---------------------------------------------------------------------------
# resolve_psi_heal — heal_bonus (Focused Channel)
# ---------------------------------------------------------------------------

class TestResolvePsiHealBonus:
    """Tests for the optional heal_bonus parameter added for Focused Channel."""

    def test_heal_bonus_added_to_amount(self):
        # MIND=10 base=10, bonus=4 → heal 14 HP.
        new_psi, gained, note = resolve_psi_heal(
            psi=60, psi_max=60, mind=10, hp=50, hp_max=100, heal_bonus=4
        )
        assert note == "healed"
        assert gained == 14

    def test_heal_bonus_capped_by_hp_max(self):
        # base 10 + bonus 8 = 18, but only 5 HP missing.
        new_psi, gained, note = resolve_psi_heal(
            psi=60, psi_max=60, mind=10, hp=95, hp_max=100, heal_bonus=8
        )
        assert note == "healed"
        assert gained == 5

    def test_zero_bonus_unchanged_behaviour(self):
        new_psi, gained, note = resolve_psi_heal(
            psi=60, psi_max=60, mind=10, hp=50, hp_max=100, heal_bonus=0
        )
        assert note == "healed"
        assert gained == 10

    def test_bonus_still_blocked_by_insufficient_psi(self):
        new_psi, gained, note = resolve_psi_heal(
            psi=10, psi_max=60, mind=10, hp=50, hp_max=100, heal_bonus=8
        )
        assert note == "insufficient_psi"
        assert gained == 0


# ---------------------------------------------------------------------------
# resolve_psi_ward
# ---------------------------------------------------------------------------

class TestResolvePsiWard:
    """Pure logic tests for Resonance Shield (PSI Ward)."""

    def test_ward_basic_rank_1(self):
        new_psi, absorption, note = resolve_psi_ward(psi=60, guild_rank=1)
        assert note == "warded"
        assert absorption == 22   # 20 + 1*2
        assert new_psi == 30      # 60 - 30 cost

    def test_ward_rank_5(self):
        new_psi, absorption, note = resolve_psi_ward(psi=60, guild_rank=5)
        assert note == "warded"
        assert absorption == 30   # 20 + 5*2

    def test_ward_rank_10(self):
        new_psi, absorption, note = resolve_psi_ward(psi=60, guild_rank=10)
        assert note == "warded"
        assert absorption == 40   # 20 + 10*2

    def test_ward_insufficient_psi(self):
        new_psi, absorption, note = resolve_psi_ward(psi=29, guild_rank=5)
        assert note == "insufficient_psi"
        assert absorption == 0
        assert new_psi == 29      # unchanged

    def test_ward_exact_cost_succeeds(self):
        new_psi, absorption, note = resolve_psi_ward(psi=30, guild_rank=1)
        assert note == "warded"
        assert new_psi == 0

    def test_ward_zero_psi_blocked(self):
        new_psi, absorption, note = resolve_psi_ward(psi=0, guild_rank=3)
        assert note == "insufficient_psi"


# ---------------------------------------------------------------------------
# resolve_psi_bolt
# ---------------------------------------------------------------------------

class TestResolvePsiBolt:
    """Pure logic tests for PSI Bolt."""

    def test_base_mind_damage(self):
        # MIND=10 → 15 base damage.
        new_psi, sh, hp, note = resolve_psi_bolt(
            psi=60, mind=10, defender_shield=0, defender_hp=40
        )
        assert note == "hit"
        assert sh + hp == 15
        assert new_psi == 25   # 60 - 35 cost

    def test_elevated_mind_scales(self):
        # MIND=15 → 15 + (15-10)*4 = 35 damage.
        new_psi, sh, hp, note = resolve_psi_bolt(
            psi=60, mind=15, defender_shield=0, defender_hp=40
        )
        assert note == "hit"
        assert sh + hp == 35

    def test_shield_absorbs_first(self):
        new_psi, sh, hp, note = resolve_psi_bolt(
            psi=60, mind=10, defender_shield=10, defender_hp=40
        )
        assert note == "hit"
        assert sh == 10
        assert hp == 5

    def test_insufficient_psi(self):
        new_psi, sh, hp, note = resolve_psi_bolt(
            psi=34, mind=10, defender_shield=0, defender_hp=40
        )
        assert note == "insufficient_psi"
        assert sh == 0
        assert hp == 0
        assert new_psi == 34

    def test_stronger_than_shock_at_same_mind(self):
        # PSI Bolt base=15 vs PSI Shock base=8 at MIND=10.
        _, _, hp_bolt, note_b = resolve_psi_bolt(psi=100, mind=10, defender_shield=0, defender_hp=100)
        _, _, hp_shock, note_s = resolve_psi_shock(psi=100, mind=10, defender_shield=0, defender_hp=100)
        assert hp_bolt > hp_shock


# ---------------------------------------------------------------------------
# resolve_psi_shatter
# ---------------------------------------------------------------------------

class TestResolvePsiShatter:
    """Pure logic tests for Mind Shatter."""

    def test_base_mind_damage(self):
        # MIND=10 → 20 base damage.
        new_psi, sh, hp, stuns, note = resolve_psi_shatter(
            psi=60, mind=10, defender_shield=0, defender_hp=40
        )
        assert note == "shattered"
        assert sh + hp == 20
        assert stuns is True
        assert new_psi == 10   # 60 - 50 cost

    def test_elevated_mind_scales(self):
        # MIND=15 → 20 + (15-10)*6 = 50 damage.
        new_psi, sh, hp, stuns, note = resolve_psi_shatter(
            psi=60, mind=15, defender_shield=0, defender_hp=100
        )
        assert note == "shattered"
        assert sh + hp == 50
        assert stuns is True

    def test_shield_absorbs_first(self):
        new_psi, sh, hp, stuns, note = resolve_psi_shatter(
            psi=60, mind=10, defender_shield=12, defender_hp=40
        )
        assert note == "shattered"
        assert sh == 12
        assert hp == 8

    def test_insufficient_psi(self):
        new_psi, sh, hp, stuns, note = resolve_psi_shatter(
            psi=49, mind=10, defender_shield=0, defender_hp=40
        )
        assert note == "insufficient_psi"
        assert sh == 0
        assert hp == 0
        assert stuns is False
        assert new_psi == 49

    def test_stuns_always_true_on_hit(self):
        for mind in [10, 15, 20]:
            _, _, _, stuns, note = resolve_psi_shatter(
                psi=100, mind=mind, defender_shield=0, defender_hp=100
            )
            assert note == "shattered"
            assert stuns is True

    def test_stronger_than_bolt_at_same_mind(self):
        _, _, hp_s, _, _ = resolve_psi_shatter(psi=100, mind=10, defender_shield=0, defender_hp=100)
        _, _, hp_b, _ = resolve_psi_bolt(psi=100, mind=10, defender_shield=0, defender_hp=100)
        assert hp_s > hp_b


# ---------------------------------------------------------------------------
# resolve_sleep_psi_restore
# ---------------------------------------------------------------------------

class TestResolveSleepPsiRestore:
    """PSI lump-sum recovery granted by a sleep cycle."""

    def test_base_mind_restore(self):
        # MIND=10 → base 15 PSI.
        new_psi, gained = resolve_sleep_psi_restore(psi=0, psi_max=60, mind=10)
        assert gained == 15
        assert new_psi == 15

    def test_elevated_mind_scales(self):
        # MIND=15 → 15 + (15-10)*2 = 25 PSI.
        new_psi, gained = resolve_sleep_psi_restore(psi=0, psi_max=60, mind=15)
        assert gained == 25
        assert new_psi == 25

    def test_high_mind_scales(self):
        # MIND=20 → 15 + (20-10)*2 = 35 PSI.
        new_psi, gained = resolve_sleep_psi_restore(psi=0, psi_max=60, mind=20)
        assert gained == 35

    def test_below_base_mind_still_gives_base(self):
        # MIND < 10 should not go negative; clamp at 15.
        new_psi, gained = resolve_sleep_psi_restore(psi=0, psi_max=60, mind=5)
        assert gained == 15

    def test_capped_by_psi_max(self):
        # Only 10 PSI missing — can't overheal.
        new_psi, gained = resolve_sleep_psi_restore(psi=50, psi_max=60, mind=10)
        assert new_psi == 60
        assert gained == 10

    def test_already_full_gives_zero(self):
        new_psi, gained = resolve_sleep_psi_restore(psi=60, psi_max=60, mind=15)
        assert gained == 0
        assert new_psi == 60

    def test_partial_halves_restore(self):
        # MIND=10 → base 15; halved → 7 (floor).
        new_psi, gained = resolve_sleep_psi_restore(psi=0, psi_max=60, mind=10, partial=True)
        assert gained == 7
        assert new_psi == 7

    def test_partial_elevated_mind(self):
        # MIND=15 → 25; halved → 12.
        new_psi, gained = resolve_sleep_psi_restore(psi=0, psi_max=60, mind=15, partial=True)
        assert gained == 12

    def test_partial_still_capped_by_psi_max(self):
        new_psi, gained = resolve_sleep_psi_restore(psi=58, psi_max=60, mind=20, partial=True)
        assert new_psi == 60
        assert gained == 2
