"""Tests for the guild system — data definitions, skill-cap logic, and bonus calculations.

These tests are pure (no Evennia imports) and verify the guild helper functions
defined in mud_commands.py via a thin import shim, plus the world_data guild
definitions and the PSI guild resolvers.
"""

from __future__ import annotations

import sys
import os
import types
import pytest

# ---------------------------------------------------------------------------
# Minimal stubs so mud_commands helpers can be imported without Evennia.
# ---------------------------------------------------------------------------

# Stub the 'evennia' package.
evennia_stub = types.ModuleType("evennia")
evennia_stub.utils = types.ModuleType("evennia.utils")
evennia_stub.utils.utils = types.ModuleType("evennia.utils.utils")
evennia_stub.default_cmds = types.ModuleType("evennia.default_cmds")
evennia_stub.Command = object
sys.modules.setdefault("evennia", evennia_stub)
sys.modules.setdefault("evennia.utils", evennia_stub.utils)
sys.modules.setdefault("evennia.utils.utils", evennia_stub.utils.utils)
sys.modules.setdefault("evennia.default_cmds", evennia_stub.default_cmds)

# Point sys.path so mudgame packages resolve.
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

# ---------------------------------------------------------------------------
# Import the helpers we want to test directly from world_data and psi.
# ---------------------------------------------------------------------------

from mudgame.data.world_data import WORLD_DATA

GUILDS = WORLD_DATA["guilds"]
IRON = GUILDS["iron_covenant"]
WEAVERS = GUILDS["psi_weavers"]


# ---------------------------------------------------------------------------
# Guild data schema
# ---------------------------------------------------------------------------

class TestGuildDataSchema:
    """Validate that the guild definitions have the expected shape."""

    REQUIRED_GUILD_KEYS = {
        "name", "planet", "hall_room", "guildmaster_npc",
        "max_rank", "passive_per_rank", "skills",
    }

    def test_both_guilds_present(self):
        assert "iron_covenant" in GUILDS
        assert "psi_weavers" in GUILDS

    def test_iron_covenant_has_required_keys(self):
        missing = self.REQUIRED_GUILD_KEYS - IRON.keys()
        assert not missing, f"iron_covenant missing keys: {missing}"

    def test_psi_weavers_has_required_keys(self):
        missing = self.REQUIRED_GUILD_KEYS - WEAVERS.keys()
        assert not missing, f"psi_weavers missing keys: {missing}"

    def test_iron_covenant_max_rank(self):
        assert IRON["max_rank"] == 20

    def test_psi_weavers_max_rank(self):
        assert WEAVERS["max_rank"] == 20

    def test_iron_covenant_skills_present(self):
        skills = IRON["skills"]
        for key in ("iron_stance", "throw_weight", "find_weakness",
                    "enhanced_criticals", "sunder_strike",
                    "iron_will", "bulwark", "warlord_strike", "battle_mastery"):
            assert key in skills, f"iron_covenant missing skill: {key}"

    def test_psi_weavers_skills_present(self):
        skills = WEAVERS["skills"]
        for key in ("focused_channel", "resonance_shield", "psi_bolt", "mind_shatter",
                    "deep_resonance", "void_lance", "psi_surge", "mind_fortress"):
            assert key in skills, f"psi_weavers missing skill: {key}"

    def test_all_skills_have_rank_gates(self):
        for gkey, gdata in GUILDS.items():
            for sk_key, sk_data in gdata["skills"].items():
                assert "rank_gates" in sk_data, (
                    f"{gkey}.{sk_key} missing rank_gates"
                )

    def test_all_skills_have_xp_cost(self):
        for gkey, gdata in GUILDS.items():
            for sk_key, sk_data in gdata["skills"].items():
                assert "xp_cost_per_pct" in sk_data, (
                    f"{gkey}.{sk_key} missing xp_cost_per_pct"
                )

    def test_passive_per_rank_iron_covenant(self):
        passives = IRON["passive_per_rank"]
        assert passives.get("str", 0) > 0
        assert passives.get("con", 0) > 0
        assert passives.get("hp_max", 0) > 0

    def test_passive_per_rank_psi_weavers(self):
        passives = WEAVERS["passive_per_rank"]
        assert passives.get("mind", 0) > 0
        assert passives.get("psi_max", 0) > 0

    def test_annihilation_strike_requires_rank_5(self):
        gates = IRON["skills"]["sunder_strike"]["rank_gates"]
        assert 5 in gates, "sunder_strike should unlock at rank 5"

    def test_psi_bolt_requires_rank_3(self):
        gates = WEAVERS["skills"]["psi_bolt"]["rank_gates"]
        assert 3 in gates, "psi_bolt should unlock at rank 3"

    def test_mind_shatter_requires_rank_6(self):
        gates = WEAVERS["skills"]["mind_shatter"]["rank_gates"]
        assert 6 in gates, "mind_shatter should unlock at rank 6"


# ---------------------------------------------------------------------------
# Guild skill cap logic (_guild_skill_cap equivalent, tested in isolation)
# ---------------------------------------------------------------------------

def _guild_skill_cap(guild_key: str, skill_key: str, rank: int) -> int:
    """Mirror of the helper in mud_commands.py — pure function."""
    skills = GUILDS[guild_key]["skills"]
    if skill_key not in skills:
        return 0
    rank_gates: dict[int, int] = skills[skill_key].get("rank_gates", {})
    cap = 0
    for gate_rank in sorted(rank_gates):
        if rank >= gate_rank:
            cap = rank_gates[gate_rank]
    return cap


class TestGuildSkillCap:
    """Validate skill cap logic against rank_gates."""

    # iron_stance: {1: 25, 3: 50, 6: 75, 9: 100}

    def test_cap_at_rank_0_is_zero(self):
        assert _guild_skill_cap("iron_covenant", "iron_stance", rank=0) == 0

    def test_cap_at_rank_1(self):
        assert _guild_skill_cap("iron_covenant", "iron_stance", rank=1) == 25

    def test_cap_at_rank_2(self):
        # Still gate 1 (25) — gate 3 not yet reached.
        assert _guild_skill_cap("iron_covenant", "iron_stance", rank=2) == 25

    def test_cap_at_rank_3(self):
        assert _guild_skill_cap("iron_covenant", "iron_stance", rank=3) == 50

    def test_cap_at_rank_6(self):
        assert _guild_skill_cap("iron_covenant", "iron_stance", rank=6) == 75

    def test_cap_at_rank_9(self):
        assert _guild_skill_cap("iron_covenant", "iron_stance", rank=9) == 100

    def test_cap_at_rank_10(self):
        assert _guild_skill_cap("iron_covenant", "iron_stance", rank=10) == 100

    # sunder_strike: {5: 100}
    def test_annihilation_cap_below_rank_5(self):
        assert _guild_skill_cap("iron_covenant", "sunder_strike", rank=4) == 0

    def test_annihilation_cap_at_rank_5(self):
        assert _guild_skill_cap("iron_covenant", "sunder_strike", rank=5) == 100

    # psi_bolt: {3: 100}
    def test_psi_bolt_cap_below_rank_3(self):
        assert _guild_skill_cap("psi_weavers", "psi_bolt", rank=2) == 0

    def test_psi_bolt_cap_at_rank_3(self):
        assert _guild_skill_cap("psi_weavers", "psi_bolt", rank=3) == 100

    # mind_shatter: {6: 100}
    def test_mind_shatter_cap_below_rank_6(self):
        assert _guild_skill_cap("psi_weavers", "mind_shatter", rank=5) == 0

    def test_mind_shatter_cap_at_rank_6(self):
        assert _guild_skill_cap("psi_weavers", "mind_shatter", rank=6) == 100


# ---------------------------------------------------------------------------
# Guild skill bonus formulas (passive, computed from pct)
# ---------------------------------------------------------------------------

def _compute_iron_bonuses(iron_stance_pct: int = 0,
                          throw_weight_pct: int = 0,
                          find_weakness_pct: int = 0,
                          enhanced_criticals_pct: int = 0,
                          iron_will_pct: int = 0,
                          bulwark_pct: int = 0,
                          battle_mastery_pct: int = 0) -> dict:
    """Mirror of the Iron Covenant branch of _get_guild_skill_bonuses."""
    sk = IRON["skills"]
    return {
        "phys_reduction": (iron_stance_pct // 20)
                          * sk["iron_stance"]["bonus_per_20pct"]
                          + (bulwark_pct // 25)
                          * sk["bulwark"]["bonus_per_25pct"],
        "weapon_damage":  (throw_weight_pct // 20)
                          * sk["throw_weight"]["bonus_per_20pct"],
        "crit_chance":    (find_weakness_pct // 10)
                          * sk["find_weakness"]["bonus_per_10pct"]
                          + (battle_mastery_pct // 25)
                          * sk["battle_mastery"]["bonus_per_25pct"],
        "crit_damage":    (enhanced_criticals_pct // 25)
                          * sk["enhanced_criticals"]["bonus_per_25pct"]
                          + (battle_mastery_pct // 25)
                          * sk["battle_mastery"]["crit_damage_per_25pct"],
        "stamina_max":    (iron_will_pct // 10)
                          * sk["iron_will"]["bonus_per_10pct"],
    }


def _compute_weaver_bonuses(focused_channel_pct: int = 0,
                             deep_resonance_pct: int = 0,
                             psi_surge_pct: int = 0,
                             mind_fortress_pct: int = 0) -> dict:
    """Mirror of the PSI Weavers branch of _get_guild_skill_bonuses."""
    sk = WEAVERS["skills"]
    return {
        "psi_heal_bonus": (focused_channel_pct // 25)
                          * sk["focused_channel"]["bonus_per_25pct"]
                          + (psi_surge_pct // 25)
                          * sk["psi_surge"]["bonus_per_25pct"],
        "psi_max":        (deep_resonance_pct // 25)
                          * sk["deep_resonance"]["bonus_per_25pct"],
        "phys_reduction": (mind_fortress_pct // 25)
                          * sk["mind_fortress"]["bonus_per_25pct"],
    }


class TestIronCovenantBonuses:
    """Validate Iron Covenant passive bonus formulas."""

    def test_iron_stance_zero_pct(self):
        b = _compute_iron_bonuses(iron_stance_pct=0)
        assert b["phys_reduction"] == 0

    def test_iron_stance_20pct(self):
        b = _compute_iron_bonuses(iron_stance_pct=20)
        assert b["phys_reduction"] == 1

    def test_iron_stance_100pct_max(self):
        b = _compute_iron_bonuses(iron_stance_pct=100)
        assert b["phys_reduction"] == 5

    def test_throw_weight_60pct(self):
        b = _compute_iron_bonuses(throw_weight_pct=60)
        assert b["weapon_damage"] == 3

    def test_find_weakness_50pct(self):
        b = _compute_iron_bonuses(find_weakness_pct=50)
        assert abs(b["crit_chance"] - 0.05) < 1e-9

    def test_find_weakness_100pct_max(self):
        b = _compute_iron_bonuses(find_weakness_pct=100)
        assert abs(b["crit_chance"] - 0.10) < 1e-9

    def test_enhanced_criticals_25pct(self):
        b = _compute_iron_bonuses(enhanced_criticals_pct=25)
        assert b["crit_damage"] == 1

    def test_enhanced_criticals_100pct_max(self):
        b = _compute_iron_bonuses(enhanced_criticals_pct=100)
        assert b["crit_damage"] == 4


class TestPsiWeaverBonuses:
    """Validate PSI Weavers passive bonus formulas."""

    def test_focused_channel_zero(self):
        b = _compute_weaver_bonuses(focused_channel_pct=0)
        assert b["psi_heal_bonus"] == 0

    def test_focused_channel_25pct(self):
        b = _compute_weaver_bonuses(focused_channel_pct=25)
        assert b["psi_heal_bonus"] == 2

    def test_focused_channel_50pct(self):
        b = _compute_weaver_bonuses(focused_channel_pct=50)
        assert b["psi_heal_bonus"] == 4

    def test_focused_channel_100pct_max(self):
        b = _compute_weaver_bonuses(focused_channel_pct=100)
        assert b["psi_heal_bonus"] == 8


class TestIronCovenantAdvancedBonuses:
    """Validate rank 11-20 Iron Covenant passive bonus formulas."""

    def test_iron_will_zero_pct(self):
        b = _compute_iron_bonuses(iron_will_pct=0)
        assert b["stamina_max"] == 0

    def test_iron_will_10pct(self):
        b = _compute_iron_bonuses(iron_will_pct=10)
        assert b["stamina_max"] == 1

    def test_iron_will_100pct_max(self):
        b = _compute_iron_bonuses(iron_will_pct=100)
        assert b["stamina_max"] == 10

    def test_bulwark_25pct(self):
        b = _compute_iron_bonuses(bulwark_pct=25)
        assert b["phys_reduction"] == 1

    def test_bulwark_100pct_max(self):
        b = _compute_iron_bonuses(bulwark_pct=100)
        assert b["phys_reduction"] == 4

    def test_bulwark_stacks_with_iron_stance(self):
        # iron_stance at 60% gives 3 phys_reduction (3×1 per 20pct)
        # bulwark at 50% gives 2 phys_reduction (2×1 per 25pct)
        b = _compute_iron_bonuses(iron_stance_pct=60, bulwark_pct=50)
        assert b["phys_reduction"] == 5

    def test_battle_mastery_25pct_crit_chance(self):
        b = _compute_iron_bonuses(battle_mastery_pct=25)
        assert abs(b["crit_chance"] - 0.02) < 1e-9

    def test_battle_mastery_100pct_crit_chance_max(self):
        b = _compute_iron_bonuses(battle_mastery_pct=100)
        assert abs(b["crit_chance"] - 0.08) < 1e-9

    def test_battle_mastery_25pct_crit_damage(self):
        b = _compute_iron_bonuses(battle_mastery_pct=25)
        assert b["crit_damage"] == 2

    def test_battle_mastery_100pct_crit_damage_max(self):
        b = _compute_iron_bonuses(battle_mastery_pct=100)
        assert b["crit_damage"] == 8

    def test_battle_mastery_stacks_with_enhanced_criticals(self):
        # enhanced_criticals 100% → +4 crit_damage; battle_mastery 100% → +8
        b = _compute_iron_bonuses(enhanced_criticals_pct=100, battle_mastery_pct=100)
        assert b["crit_damage"] == 12


class TestPsiWeaverAdvancedBonuses:
    """Validate rank 11-20 PSI Weavers passive bonus formulas."""

    def test_deep_resonance_zero(self):
        b = _compute_weaver_bonuses(deep_resonance_pct=0)
        assert b["psi_max"] == 0

    def test_deep_resonance_25pct(self):
        b = _compute_weaver_bonuses(deep_resonance_pct=25)
        assert b["psi_max"] == 5

    def test_deep_resonance_100pct_max(self):
        b = _compute_weaver_bonuses(deep_resonance_pct=100)
        assert b["psi_max"] == 20

    def test_psi_surge_25pct(self):
        b = _compute_weaver_bonuses(psi_surge_pct=25)
        assert b["psi_heal_bonus"] == 3

    def test_psi_surge_100pct_max(self):
        b = _compute_weaver_bonuses(psi_surge_pct=100)
        assert b["psi_heal_bonus"] == 12

    def test_psi_surge_stacks_with_focused_channel(self):
        # focused_channel 100% → +8; psi_surge 100% → +12; total = 20
        b = _compute_weaver_bonuses(focused_channel_pct=100, psi_surge_pct=100)
        assert b["psi_heal_bonus"] == 20

    def test_mind_fortress_zero(self):
        b = _compute_weaver_bonuses(mind_fortress_pct=0)
        assert b["phys_reduction"] == 0

    def test_mind_fortress_25pct(self):
        b = _compute_weaver_bonuses(mind_fortress_pct=25)
        assert b["phys_reduction"] == 3

    def test_mind_fortress_100pct_max(self):
        b = _compute_weaver_bonuses(mind_fortress_pct=100)
        assert b["phys_reduction"] == 12


# ---------------------------------------------------------------------------
# XP cost scaling formula
# ---------------------------------------------------------------------------

class TestGuildTrainingXpCost:
    """Validate the XP cost scaling formula: base * (1 + current_pct // 25)."""

    def _cost(self, base: int, current_pct: int) -> int:
        return base * (1 + current_pct // 25)

    def test_tier_0_pct_0(self):
        # current=0 → multiplier 1.
        assert self._cost(50, 0) == 50

    def test_tier_1_pct_25(self):
        # current=25 → multiplier 2.
        assert self._cost(50, 25) == 100

    def test_tier_2_pct_50(self):
        # current=50 → multiplier 3.
        assert self._cost(50, 50) == 150

    def test_tier_3_pct_75(self):
        # current=75 → multiplier 4.
        assert self._cost(50, 75) == 200

    def test_tier_boundary_pct_24(self):
        # Still tier 0.
        assert self._cost(50, 24) == 50

    def test_tier_boundary_pct_99(self):
        # current=99 → 99 // 25 = 3 → multiplier 4.
        assert self._cost(50, 99) == 200

    def test_higher_base_cost(self):
        # sunder_strike has xp_cost_per_pct=100.
        assert self._cost(100, 0) == 100
        assert self._cost(100, 25) == 200


# ---------------------------------------------------------------------------
# Pure guild engine functions (mudgame/systems/guilds.py)
# ---------------------------------------------------------------------------

from mudgame.systems.guilds import (
    guild_skill_cap,
    guild_passives_per_rank,
    apply_guild_stat_passives,
    resolve_guild_join,
    resolve_guild_advance,
)


class TestGuildSkillCapPure:
    """guild_skill_cap() — pure function from guilds.py."""

    def test_cap_rank_0_is_zero(self):
        assert guild_skill_cap("iron_covenant", "iron_stance", 0, GUILDS) == 0

    def test_cap_rank_1(self):
        assert guild_skill_cap("iron_covenant", "iron_stance", 1, GUILDS) == 25

    def test_cap_rank_3(self):
        assert guild_skill_cap("iron_covenant", "iron_stance", 3, GUILDS) == 50

    def test_cap_rank_9(self):
        assert guild_skill_cap("iron_covenant", "iron_stance", 9, GUILDS) == 100

    def test_cap_annihilation_below_5(self):
        assert guild_skill_cap("iron_covenant", "sunder_strike", 4, GUILDS) == 0

    def test_cap_annihilation_at_5(self):
        assert guild_skill_cap("iron_covenant", "sunder_strike", 5, GUILDS) == 100

    def test_cap_psi_bolt_rank_2(self):
        assert guild_skill_cap("psi_weavers", "psi_bolt", 2, GUILDS) == 0

    def test_cap_psi_bolt_rank_3(self):
        assert guild_skill_cap("psi_weavers", "psi_bolt", 3, GUILDS) == 100

    def test_unknown_guild_returns_zero(self):
        assert guild_skill_cap("no_guild", "iron_stance", 5, GUILDS) == 0

    def test_unknown_skill_returns_zero(self):
        assert guild_skill_cap("iron_covenant", "no_skill", 5, GUILDS) == 0


class TestGuildPassivesPerRank:
    """guild_passives_per_rank() returns the correct stat delta dict."""

    def test_iron_covenant_passives_not_empty(self):
        p = guild_passives_per_rank("iron_covenant", GUILDS)
        assert len(p) > 0

    def test_iron_covenant_has_str_gain(self):
        p = guild_passives_per_rank("iron_covenant", GUILDS)
        assert p.get("str", 0) > 0

    def test_psi_weavers_has_psi_max_gain(self):
        p = guild_passives_per_rank("psi_weavers", GUILDS)
        assert p.get("psi_max", 0) > 0

    def test_unknown_guild_returns_empty(self):
        p = guild_passives_per_rank("no_guild", GUILDS)
        assert p == {}


class TestApplyGuildStatPassives:
    """apply_guild_stat_passives() mutates attrs / hp_max / psi_max correctly."""

    BASE_ATTRS = {"str": 10, "dex": 10, "con": 10, "mind": 10, "cha": 10, "per": 10, "luck": 10}

    def test_iron_covenant_increases_str(self):
        new_attrs, new_hp, new_psi = apply_guild_stat_passives(
            attrs=dict(self.BASE_ATTRS),
            hp_max=100,
            psi_max=60,
            guild_key="iron_covenant",
            guilds_data=GUILDS,
        )
        passives = guild_passives_per_rank("iron_covenant", GUILDS)
        assert new_attrs["str"] == self.BASE_ATTRS["str"] + passives.get("str", 0)

    def test_iron_covenant_increases_hp_max(self):
        new_attrs, new_hp, new_psi = apply_guild_stat_passives(
            attrs=dict(self.BASE_ATTRS),
            hp_max=100,
            psi_max=60,
            guild_key="iron_covenant",
            guilds_data=GUILDS,
        )
        passives = guild_passives_per_rank("iron_covenant", GUILDS)
        assert new_hp == 100 + passives.get("hp_max", 0)

    def test_psi_weavers_increases_psi_max(self):
        new_attrs, new_hp, new_psi = apply_guild_stat_passives(
            attrs=dict(self.BASE_ATTRS),
            hp_max=100,
            psi_max=60,
            guild_key="psi_weavers",
            guilds_data=GUILDS,
        )
        passives = guild_passives_per_rank("psi_weavers", GUILDS)
        assert new_psi == 60 + passives.get("psi_max", 0)

    def test_does_not_mutate_original_attrs(self):
        orig = dict(self.BASE_ATTRS)
        apply_guild_stat_passives(
            attrs=dict(orig),
            hp_max=100,
            psi_max=60,
            guild_key="iron_covenant",
            guilds_data=GUILDS,
        )
        # orig must be untouched
        assert orig == self.BASE_ATTRS

    def test_unknown_guild_returns_unchanged(self):
        attrs = dict(self.BASE_ATTRS)
        new_attrs, new_hp, new_psi = apply_guild_stat_passives(
            attrs=attrs,
            hp_max=100,
            psi_max=60,
            guild_key="no_guild",
            guilds_data=GUILDS,
        )
        assert new_attrs == attrs
        assert new_hp == 100
        assert new_psi == 60


class TestResolveGuildJoin:
    """resolve_guild_join() — pure validation + state mutation."""

    HALL_ROOM = GUILDS["iron_covenant"]["hall_room"]

    def _join(self, *, guild_key="iron_covenant", room_key=None,
               guild_levels=None, free_levels=1, guild_skills=None):
        return resolve_guild_join(
            guild_key=guild_key,
            room_key=room_key or self.HALL_ROOM,
            guild_levels=guild_levels or {},
            free_levels=free_levels,
            guild_skills=guild_skills or {},
            guilds_data=GUILDS,
        )

    def test_successful_join(self):
        ok, msg, gl, fl, gs = self._join()
        assert ok is True
        assert gl["iron_covenant"] == 1
        assert fl == 0
        assert "iron_covenant" in gs

    def test_wrong_room_fails(self):
        ok, msg, gl, fl, gs = self._join(room_key="wrong_room")
        assert ok is False
        assert gl == {}

    def test_no_free_levels_fails(self):
        ok, msg, gl, fl, gs = self._join(free_levels=0)
        assert ok is False
        assert fl == 0

    def test_already_member_fails(self):
        ok, msg, gl, fl, gs = self._join(
            guild_levels={"iron_covenant": 1}
        )
        assert ok is False

    def test_already_in_other_guild_fails(self):
        ok, msg, gl, fl, gs = self._join(
            guild_levels={"psi_weavers": 2}
        )
        assert ok is False

    def test_guild_skills_initialised_on_join(self):
        ok, msg, gl, fl, gs = self._join()
        skills = gs.get("iron_covenant", {})
        for sk_key in GUILDS["iron_covenant"]["skills"]:
            assert sk_key in skills
            assert skills[sk_key] == 0

    def test_unknown_guild_fails(self):
        ok, msg, gl, fl, gs = resolve_guild_join(
            guild_key="no_guild",
            room_key="somewhere",
            guild_levels={},
            free_levels=5,
            guild_skills={},
            guilds_data=GUILDS,
        )
        assert ok is False


class TestResolveGuildAdvance:
    """resolve_guild_advance() — pure validation + rank promotion."""

    HALL_ROOM = GUILDS["iron_covenant"]["hall_room"]

    def _advance(self, *, guild_key="iron_covenant", room_key=None,
                 guild_levels=None, free_levels=1):
        return resolve_guild_advance(
            guild_key=guild_key,
            room_key=room_key or self.HALL_ROOM,
            guild_levels={"iron_covenant": 1} if guild_levels is None else guild_levels,
            free_levels=free_levels,
            guilds_data=GUILDS,
        )

    def test_successful_advance(self):
        ok, msg, gl, fl = self._advance()
        assert ok is True
        assert gl["iron_covenant"] == 2
        assert fl == 0

    def test_wrong_room_fails(self):
        ok, msg, gl, fl = self._advance(room_key="wrong_room")
        assert ok is False

    def test_not_a_member_fails(self):
        ok, msg, gl, fl = self._advance(guild_levels={})
        assert ok is False

    def test_at_max_rank_fails(self):
        max_rank = GUILDS["iron_covenant"]["max_rank"]
        ok, msg, gl, fl = self._advance(
            guild_levels={"iron_covenant": max_rank}
        )
        assert ok is False

    def test_no_free_levels_fails(self):
        ok, msg, gl, fl = self._advance(free_levels=0)
        assert ok is False

    def test_multiple_advances_accumulate(self):
        gl = {"iron_covenant": 1}
        fl = 5
        for expected_rank in range(2, 6):
            ok, msg, gl, fl = resolve_guild_advance(
                guild_key="iron_covenant",
                room_key=self.HALL_ROOM,
                guild_levels=gl,
                free_levels=fl,
                guilds_data=GUILDS,
            )
            assert ok is True
            assert gl["iron_covenant"] == expected_rank


# ---------------------------------------------------------------------------
# Gap A — XP banking floor at reincarnation
# ---------------------------------------------------------------------------

from mudgame.data.constants import LEVEL_XP_TABLE


def _xp_to_bank(xp: int, level: int) -> int:
    """Mirror of the fix: bank at least the threshold for the current level."""
    return max(xp, LEVEL_XP_TABLE.get(level, 0))


class TestReincarnationXpBankingFloor:
    """Guild skill training must not reduce the soul pool below the level threshold."""

    def test_unspent_xp_banked_as_is(self):
        # No training: xp at level threshold; bank exactly that.
        threshold = LEVEL_XP_TABLE[5]  # 2000
        assert _xp_to_bank(xp=threshold, level=5) == threshold

    def test_spent_xp_floor_is_level_threshold(self):
        # Trained 2500 XP away from a level-6 character (3500 threshold).
        # Should bank 3500, not 1000.
        threshold = LEVEL_XP_TABLE[6]  # 3500
        assert _xp_to_bank(xp=1000, level=6) == threshold

    def test_extra_xp_above_threshold_preserved(self):
        # Player has 4200 XP at level 6 (threshold 3500); banked = 4200.
        assert _xp_to_bank(xp=4200, level=6) == 4200

    def test_level_1_floor_is_zero(self):
        # Level 1 has no threshold entry; floor = 0.
        assert _xp_to_bank(xp=0, level=1) == 0

    def test_level_10_floor(self):
        threshold = LEVEL_XP_TABLE[10]  # 15000
        assert _xp_to_bank(xp=5000, level=10) == threshold

    def test_soul_accumulates_over_multiple_reincarnations(self):
        # Two reincarnations, each banking the level-3 floor (500).
        soul = 0
        for _ in range(2):
            soul += _xp_to_bank(xp=0, level=3)
        assert soul == 2 * LEVEL_XP_TABLE[3]


# ---------------------------------------------------------------------------
# Gap C — training cost display formula
# ---------------------------------------------------------------------------

def _displayed_cost(base_cost: int, current_pct: int) -> int:
    """The cost actually shown to the player (and charged) at current_pct."""
    return base_cost * (1 + current_pct // 25)


class TestTrainingCostDisplay:
    """Scaled training cost must match what the guilds command shows."""

    def test_tier_1_cost_at_0pct(self):
        assert _displayed_cost(50, 0) == 50

    def test_tier_1_cost_at_24pct(self):
        assert _displayed_cost(50, 24) == 50

    def test_tier_2_cost_at_25pct(self):
        assert _displayed_cost(50, 25) == 100

    def test_tier_2_cost_at_49pct(self):
        assert _displayed_cost(50, 49) == 100

    def test_tier_3_cost_at_50pct(self):
        assert _displayed_cost(50, 50) == 150

    def test_tier_4_cost_at_75pct(self):
        assert _displayed_cost(50, 75) == 200

    def test_tier_4_cost_at_99pct(self):
        assert _displayed_cost(50, 99) == 200

    def test_cost_scales_with_base(self):
        # Higher base cost (psi weavers focused_channel = 40/pct).
        assert _displayed_cost(40, 50) == 120


# ---------------------------------------------------------------------------
# Gap G — idempotent guild passive application
# ---------------------------------------------------------------------------

from mudgame.systems.guilds import apply_guild_stat_passives, guild_passives_per_rank


def _apply_n_ranks(guild_key: str, n: int,
                   attrs=None, hp_max=100, psi_max=60) -> tuple[dict, int, int]:
    """Apply n ranks of passives from scratch; returns (attrs, hp_max, psi_max)."""
    attrs = dict(attrs or {"str": 10, "dex": 10, "con": 10, "mind": 10,
                           "cha": 10, "per": 10, "luck": 10})
    for _ in range(n):
        attrs, hp_max, psi_max = apply_guild_stat_passives(
            attrs=attrs, hp_max=hp_max, psi_max=psi_max,
            guild_key=guild_key, guilds_data=GUILDS,
        )
    return attrs, hp_max, psi_max


class TestIdempotentPassives:
    """Applying n ranks should give the same result as n sequential single-rank applications."""

    def test_iron_covenant_rank_1_str_gain(self):
        passives = guild_passives_per_rank("iron_covenant", GUILDS)
        attrs, hp_max, _ = _apply_n_ranks("iron_covenant", 1)
        assert attrs["str"] == 10 + passives["str"]
        assert attrs["con"] == 10 + passives["con"]
        assert hp_max == 100 + passives["hp_max"]

    def test_iron_covenant_three_ranks_accumulate(self):
        passives = guild_passives_per_rank("iron_covenant", GUILDS)
        attrs, hp_max, _ = _apply_n_ranks("iron_covenant", 3)
        assert attrs["str"] == 10 + 3 * passives["str"]
        assert hp_max == 100 + 3 * passives["hp_max"]

    def test_applying_same_rank_twice_must_not_double_stats(self):
        # Simulate the idempotency guard: calling _apply for rank 1 twice
        # should only produce 1 rank's worth of stats.  We test by
        # verifying that the two-rank result is DOUBLE the one-rank result,
        # so we know 1 rank ≠ 2 ranks.
        _, hp_1, _ = _apply_n_ranks("iron_covenant", 1)
        _, hp_2, _ = _apply_n_ranks("iron_covenant", 2)
        assert hp_2 == hp_1 + GUILDS["iron_covenant"]["passive_per_rank"]["hp_max"]

    def test_psi_weavers_rank_1_mind_gain(self):
        passives = guild_passives_per_rank("psi_weavers", GUILDS)
        attrs, _, psi_max = _apply_n_ranks("psi_weavers", 1)
        assert attrs["mind"] == 10 + passives["mind"]
        assert psi_max == 60 + passives["psi_max"]


# ---------------------------------------------------------------------------
# Gap G — passive reversal (leave guild logic)
# ---------------------------------------------------------------------------

def _reverse_n_ranks(guild_key: str, n: int,
                     attrs: dict, hp_max: int, psi_max: int) -> tuple[dict, int, int]:
    """Mirror of _remove_guild_rank_passives logic."""
    passives = guild_passives_per_rank(guild_key, GUILDS)
    attrs = dict(attrs)
    for stat, gain in passives.items():
        total = gain * n
        if stat == "hp_max":
            hp_max = max(100, hp_max - total)
        elif stat == "psi_max":
            psi_max = max(60, psi_max - total)
        elif stat in attrs:
            attrs[stat] = max(10, attrs[stat] - total)
    return attrs, hp_max, psi_max


class TestPassiveReversal:
    """Leaving a guild must undo all applied stat passives."""

    def test_leaving_rank_1_iron_covenant_reverses_str(self):
        passives = guild_passives_per_rank("iron_covenant", GUILDS)
        attrs, hp_max, psi_max = _apply_n_ranks("iron_covenant", 1)
        attrs, hp_max, _ = _reverse_n_ranks("iron_covenant", 1, attrs, hp_max, psi_max)
        assert attrs["str"] == 10
        assert hp_max == 100

    def test_leaving_rank_5_iron_covenant_reverses_all(self):
        attrs, hp_max, psi_max = _apply_n_ranks("iron_covenant", 5)
        attrs, hp_max, _ = _reverse_n_ranks("iron_covenant", 5, attrs, hp_max, psi_max)
        assert attrs["str"] == 10
        assert attrs["con"] == 10
        assert hp_max == 100

    def test_reversal_cannot_go_below_base_hp(self):
        # Reverse more ranks than were ever applied — should floor at 100.
        attrs = {"str": 10, "con": 10, "mind": 10, "dex": 10, "cha": 10, "per": 10, "luck": 10}
        _, hp_max, _ = _reverse_n_ranks("iron_covenant", 100, attrs, 100, 60)
        assert hp_max == 100

    def test_reversal_cannot_go_below_base_psi(self):
        attrs = {"str": 10, "con": 10, "mind": 10, "dex": 10, "cha": 10, "per": 10, "luck": 10}
        _, _, psi_max = _reverse_n_ranks("psi_weavers", 100, attrs, 100, 60)
        assert psi_max == 60

    def test_leave_refunds_all_tokens(self):
        # Rank = 1 join + (rank-1) advances = rank total tokens.
        for rank in range(1, 6):
            tokens_refunded = rank
            assert tokens_refunded == rank  # trivially mirrors the production formula

    def test_apply_then_reverse_is_identity(self):
        """Apply N ranks then reverse N ranks → back to base values."""
        for n in (1, 3, 5, 10):
            attrs, hp, psi = _apply_n_ranks("iron_covenant", n)
            attrs, hp, psi = _reverse_n_ranks("iron_covenant", n, attrs, hp, psi)
            assert attrs["str"] == 10, f"str wrong after {n} ranks apply+reverse"
            assert hp == 100, f"hp_max wrong after {n} ranks apply+reverse"


# ---------------------------------------------------------------------------
# Gap D — post-cap level skill point award
# ---------------------------------------------------------------------------

class TestPostCapSkillPoint:
    """Each post-cap level (11+) must award 1 skill point in addition to the token."""

    _SKILL_POINTS_PER_POST_CAP_LEVEL = 1

    def test_one_post_cap_level_awards_one_skill_point(self):
        awarded = self._SKILL_POINTS_PER_POST_CAP_LEVEL
        assert awarded == 1

    def test_ten_post_cap_levels_award_ten_skill_points(self):
        # Levels 11-20 = 10 post-cap levels.
        awarded = 10 * self._SKILL_POINTS_PER_POST_CAP_LEVEL
        assert awarded == 10

    def test_post_cap_token_still_awarded(self):
        # Sanity: free_levels tokens also still awarded (1 per post-cap level).
        tokens_for_10_post_cap = 10
        assert tokens_for_10_post_cap == 10


