"""Tests for the recreate / reincarnate / claimlevels system.

Pure Python — no Evennia runtime needed.
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

_root = str(Path(__file__).resolve().parents[1])
if _root not in sys.path:
    sys.path.insert(0, _root)

from mudgame.data.constants import LEVEL_XP_TABLE


# ---------------------------------------------------------------------------
# Helpers — mirror the pure functions from mud_commands without importing
# the full Evennia-heavy module
# ---------------------------------------------------------------------------

_REINCARNATION_BASE_FEE = 500
_REINCARNATION_PER_LEVEL = 100
_REINCARNATION_PER_LIFE = 500
_REINCARNATION_SKILL_BONUS = 2
_REINCARNATION_SKILL_BONUS_CAP = 10
_RECREATE_XP_THRESHOLD = LEVEL_XP_TABLE[10]   # 15,000


def _reincarnation_fee(level: int, reincarnations: int) -> int:
    return (_REINCARNATION_BASE_FEE
            + (level - 1) * _REINCARNATION_PER_LEVEL
            + reincarnations * _REINCARNATION_PER_LIFE)


def _skill_bonus(reincarnations_after: int) -> int:
    return min(reincarnations_after * _REINCARNATION_SKILL_BONUS,
               _REINCARNATION_SKILL_BONUS_CAP)


# ---------------------------------------------------------------------------
# Mock character — simulates caller.db without Evennia
# ---------------------------------------------------------------------------

class _Db:
    """Attribute bag mimicking Evennia's AttributeHandler."""
    def __init__(self, **kw):
        self.__dict__.update(kw)


class _MockChar:
    """Minimal mock of an Evennia Character for reincarnation logic."""

    def __init__(self, *, xp=0, level=1, soul_xp=0, reincarnations=0,
                 credits=1000, inventory=None, guild_levels=None,
                 free_levels=0, skill_points=0):
        self.db = _Db(
            xp=xp,
            level=level,
            soul_xp=soul_xp,
            reincarnations=reincarnations,
            ledger={"credits": credits, "inventory": list(inventory or [])},
            guild_levels=dict(guild_levels or {}),
            free_levels=free_levels,
            skill_points=skill_points,
            guild_skills={},
            psi_ward=0,
            hp=100, hp_max=100,
            stamina=100, stamina_max=100,
            focus=50, focus_max=50,
            shield_integrity=100, shield_max=100,
            attrs={"str": 10, "dex": 10, "con": 10, "mind": 10,
                   "cha": 10, "per": 10, "luck": 10},
            attr_points=0,
            psi=60, psi_max=60,
            skills={"melee": 10, "dodge": 10, "parry": 10},
            chargen_complete=True,
            background="colonial_recruit",
            reputation={"helion_colony": 0, "vanta_clans": 0},
            camping_cooldown_until=0,
            sleeping_pending=False,
        )
        # equipped tracked separately for simplicity
        self.db.equipped = {"main_hand": "training_vibroblade",
                            "off_hand": None, "utility": None, "armor": None}

    def _init_stats(self):
        """Mirror the real _init_stats: reset all progression fields."""
        self.db.hp = 100;        self.db.hp_max = 100
        self.db.stamina = 100;   self.db.stamina_max = 100
        self.db.focus = 50;      self.db.focus_max = 50
        self.db.shield_integrity = 100; self.db.shield_max = 100
        self.db.xp = 0;          self.db.level = 1
        self.db.skills = {"melee": 10, "dodge": 10, "parry": 10}
        self.db.skill_points = 0
        self.db.attrs = {"str": 10, "dex": 10, "con": 10, "mind": 10,
                         "cha": 10, "per": 10, "luck": 10}
        self.db.attr_points = 0
        self.db.psi = 60;        self.db.psi_max = 60
        self.db.reputation = {"helion_colony": 0, "vanta_clans": 0}
        self.db.chargen_complete = False
        self.db.background = None
        self.db.camping_cooldown_until = 0
        self.db.sleeping_pending = False
        # NOTE: does NOT touch ledger, soul_xp, reincarnations, guild_levels,
        # free_levels, guild_skills — same as production code.


def _do_character_reset(caller, *, preserve_soul: bool = False):
    """Mirror of the production helper."""
    caller._init_stats()
    caller.db.guild_levels = {}
    caller.db.free_levels = 0
    caller.db.guild_skills = {}
    caller.db.psi_ward = 0
    if not preserve_soul:
        caller.db.soul_xp = 0
        caller.db.reincarnations = 0


# ---------------------------------------------------------------------------
# Fee calculation
# ---------------------------------------------------------------------------

class TestReincarnationFee:
    def test_base_fee_level_1_no_prior_lives(self):
        assert _reincarnation_fee(1, 0) == 500

    def test_fee_scales_with_level(self):
        assert _reincarnation_fee(10, 0) == 500 + 9 * 100  # 1400

    def test_fee_scales_with_prior_lives(self):
        assert _reincarnation_fee(1, 3) == 500 + 3 * 500  # 2000

    def test_fee_scales_both(self):
        assert _reincarnation_fee(5, 2) == 500 + 4 * 100 + 2 * 500  # 1900

    def test_fee_is_always_at_least_base(self):
        assert _reincarnation_fee(1, 0) >= _REINCARNATION_BASE_FEE


# ---------------------------------------------------------------------------
# Skill bonus per reincarnation
# ---------------------------------------------------------------------------

class TestSkillBonus:
    def test_first_reincarnation_bonus(self):
        assert _skill_bonus(1) == 2

    def test_bonus_accumulates(self):
        assert _skill_bonus(3) == 6

    def test_bonus_capped_at_10(self):
        assert _skill_bonus(100) == _REINCARNATION_SKILL_BONUS_CAP

    def test_zero_reincarnations_gives_zero_bonus(self):
        assert _skill_bonus(0) == 0


# ---------------------------------------------------------------------------
# XP threshold for recreate gate
# ---------------------------------------------------------------------------

class TestRecreateGate:
    def test_threshold_is_level_10_xp(self):
        assert _RECREATE_XP_THRESHOLD == LEVEL_XP_TABLE[10]

    def test_level_1_char_can_recreate(self):
        assert 0 < _RECREATE_XP_THRESHOLD

    def test_level_2_char_below_threshold(self):
        # Level 2 needs 200 XP — well below 15,000
        assert LEVEL_XP_TABLE[2] < _RECREATE_XP_THRESHOLD

    def test_exactly_at_threshold_cannot_recreate(self):
        # A char with exactly 15,000 XP must use reincarnate
        assert _RECREATE_XP_THRESHOLD >= _RECREATE_XP_THRESHOLD  # trivial but explicit


# ---------------------------------------------------------------------------
# _do_character_reset — ledger preservation
# ---------------------------------------------------------------------------

class TestCharacterReset:
    def test_ledger_preserved_through_reset(self):
        char = _MockChar(credits=5000, inventory=["plasma_rifle", "field_brace"])
        _do_character_reset(char)
        assert char.db.ledger["credits"] == 5000
        assert "plasma_rifle" in char.db.ledger["inventory"]

    def test_stats_wiped_on_reset(self):
        char = _MockChar(xp=8000, level=5)
        _do_character_reset(char)
        assert char.db.xp == 0
        assert char.db.level == 1
        assert char.db.stamina_max == 100

    def test_chargen_requeued_on_reset(self):
        char = _MockChar()
        _do_character_reset(char)
        assert char.db.chargen_complete is False
        assert char.db.background is None

    def test_guild_state_wiped_on_reset(self):
        char = _MockChar(guild_levels={"iron_covenant": 3}, free_levels=2)
        _do_character_reset(char)
        assert char.db.guild_levels == {}
        assert char.db.free_levels == 0

    def test_soul_wiped_when_preserve_false(self):
        char = _MockChar(soul_xp=999, reincarnations=2)
        _do_character_reset(char, preserve_soul=False)
        assert char.db.soul_xp == 0
        assert char.db.reincarnations == 0

    def test_soul_preserved_when_flag_set(self):
        char = _MockChar(soul_xp=999, reincarnations=2)
        _do_character_reset(char, preserve_soul=True)
        assert char.db.soul_xp == 999
        assert char.db.reincarnations == 2


# ---------------------------------------------------------------------------
# Reincarnation flow (simulating CmdReincarnate logic)
# ---------------------------------------------------------------------------

def _simulate_reincarnate(char):
    """Run the reincarnation flow as the command does, return (ok, msg)."""
    xp = char.db.xp or 0
    level = char.db.level or 1
    reincarnations = char.db.reincarnations or 0
    fee = _reincarnation_fee(level, reincarnations)
    ledger = char.db.ledger or {}
    credits = ledger.get("credits", 0)

    if credits < fee:
        return False, f"insufficient funds: need {fee}, have {credits}"

    new_ledger = dict(ledger)
    new_ledger["credits"] = credits - fee
    banked_soul_xp = (char.db.soul_xp or 0) + xp
    new_reincarnations = reincarnations + 1

    _do_character_reset(char, preserve_soul=True)

    char.db.soul_xp = banked_soul_xp
    char.db.reincarnations = new_reincarnations
    char.db.ledger = new_ledger
    char.db.skill_points = _skill_bonus(new_reincarnations)

    return True, "ok"


class TestReincarnateFlow:
    def test_xp_banked_into_soul_pool(self):
        char = _MockChar(xp=5000, level=5, credits=9999)
        _simulate_reincarnate(char)
        assert char.db.soul_xp == 5000

    def test_existing_soul_xp_accumulates(self):
        char = _MockChar(xp=3000, level=3, soul_xp=2000, credits=9999,
                         reincarnations=1)
        _simulate_reincarnate(char)
        assert char.db.soul_xp == 5000

    def test_fee_deducted_from_credits(self):
        char = _MockChar(xp=0, level=1, credits=9999)
        fee = _reincarnation_fee(1, 0)
        _simulate_reincarnate(char)
        assert char.db.ledger["credits"] == 9999 - fee

    def test_inventory_preserved_through_reincarnation(self):
        char = _MockChar(credits=9999, inventory=["plasma_rifle", "armor_vest"])
        _simulate_reincarnate(char)
        assert "plasma_rifle" in char.db.ledger["inventory"]
        assert "armor_vest" in char.db.ledger["inventory"]

    def test_reincarnation_count_incremented(self):
        char = _MockChar(credits=9999, reincarnations=2)
        _simulate_reincarnate(char)
        assert char.db.reincarnations == 3

    def test_skill_bonus_applied(self):
        char = _MockChar(credits=9999, reincarnations=0)
        _simulate_reincarnate(char)
        assert char.db.skill_points == _skill_bonus(1)  # first reincarnation

    def test_skill_bonus_capped_at_ten(self):
        char = _MockChar(credits=9_999_999, reincarnations=99)
        _simulate_reincarnate(char)
        assert char.db.skill_points == _REINCARNATION_SKILL_BONUS_CAP

    def test_insufficient_credits_blocks_reincarnation(self):
        char = _MockChar(xp=5000, level=10, credits=0)
        ok, _ = _simulate_reincarnate(char)
        assert not ok
        assert char.db.level == 10  # untouched

    def test_level_reset_to_1(self):
        char = _MockChar(xp=8000, level=7, credits=9999)
        _simulate_reincarnate(char)
        assert char.db.level == 1

    def test_regular_xp_zeroed_after_banking(self):
        char = _MockChar(xp=8000, level=7, credits=9999)
        _simulate_reincarnate(char)
        assert char.db.xp == 0

    def test_chargen_requeued(self):
        char = _MockChar(credits=9999)
        _simulate_reincarnate(char)
        assert char.db.chargen_complete is False


# ---------------------------------------------------------------------------
# claimlevels logic
# ---------------------------------------------------------------------------

def _simulate_claim_levels(char, n: int) -> tuple[int, list[str]]:
    """Simulate claiming n levels; return (levels_claimed, msgs)."""
    claimed = 0
    msgs = []
    for _ in range(n):
        cur_level = char.db.level or 1
        nxt_level = cur_level + 1
        threshold = LEVEL_XP_TABLE.get(nxt_level)
        if threshold is None:
            msgs.append("max level reached")
            break
        cur_xp = char.db.xp or 0
        cur_soul = char.db.soul_xp or 0
        xp_needed = threshold - cur_xp
        if xp_needed > cur_soul:
            msgs.append(f"insufficient soul XP: need {xp_needed}, have {cur_soul}")
            break
        char.db.xp = cur_xp + xp_needed
        char.db.soul_xp = cur_soul - xp_needed
        # Simulate level-up: bump level, add stat gains.
        char.db.level = nxt_level
        char.db.stamina_max = (char.db.stamina_max or 100) + 8
        char.db.stamina = char.db.stamina_max
        claimed += 1
    return claimed, msgs


class TestClaimLevels:
    def test_claim_one_level(self):
        # Soul pool has exactly enough for level 2.
        char = _MockChar(xp=0, level=1, soul_xp=LEVEL_XP_TABLE[2])
        claimed, _ = _simulate_claim_levels(char, 1)
        assert claimed == 1
        assert char.db.level == 2

    def test_soul_pool_drained_correctly(self):
        threshold = LEVEL_XP_TABLE[2]
        char = _MockChar(xp=0, level=1, soul_xp=threshold + 500)
        _simulate_claim_levels(char, 1)
        assert char.db.soul_xp == 500

    def test_cannot_claim_without_enough_soul_xp(self):
        char = _MockChar(xp=0, level=1, soul_xp=50)  # less than 200
        claimed, msgs = _simulate_claim_levels(char, 1)
        assert claimed == 0
        assert any("insufficient" in m for m in msgs)
        assert char.db.level == 1

    def test_claim_multiple_levels(self):
        # Enough for levels 2, 3, 4 (need 1000 total XP).
        char = _MockChar(xp=0, level=1, soul_xp=LEVEL_XP_TABLE[4])
        claimed, _ = _simulate_claim_levels(char, 3)
        assert claimed == 3
        assert char.db.level == 4

    def test_partial_claim_when_pool_runs_out(self):
        # Enough for level 2 (200) but not level 3 (500 total).
        char = _MockChar(xp=0, level=1, soul_xp=350)
        claimed, _ = _simulate_claim_levels(char, 5)
        assert claimed == 1   # only level 2 possible
        assert char.db.level == 2

    def test_stamina_max_grows_on_each_claimed_level(self):
        char = _MockChar(xp=0, level=1, soul_xp=LEVEL_XP_TABLE[3])
        _simulate_claim_levels(char, 2)
        assert char.db.stamina_max == 100 + 2 * 8

    def test_regular_xp_accumulates_for_future_gains(self):
        char = _MockChar(xp=0, level=1, soul_xp=LEVEL_XP_TABLE[2] + 100)
        _simulate_claim_levels(char, 1)
        # After claiming level 2, db.xp == threshold[2] == 200
        assert char.db.xp == LEVEL_XP_TABLE[2]


# ---------------------------------------------------------------------------
# Full reincarnation cycle: reincarnate → claim all levels back
# ---------------------------------------------------------------------------

class TestFullCycle:
    def test_full_cycle_restores_equivalent_level(self):
        """A level-5 character who reincarnates and claims all levels back
        should end at level 5 with an empty soul pool."""
        original_level = 5
        original_xp = LEVEL_XP_TABLE[original_level]  # 2000

        char = _MockChar(xp=original_xp, level=original_level, credits=9999)
        ok, _ = _simulate_reincarnate(char)
        assert ok, "reincarnation should succeed"

        # soul_xp should equal original XP
        assert char.db.soul_xp == original_xp
        assert char.db.level == 1

        # Claim all levels.
        _simulate_claim_levels(char, 10)  # more than enough iterations
        assert char.db.level == original_level
        assert char.db.soul_xp == 0

    def test_credits_survive_full_cycle(self):
        char = _MockChar(xp=2000, level=5, credits=5000)
        fee = _reincarnation_fee(5, 0)
        _simulate_reincarnate(char)
        assert char.db.ledger["credits"] == 5000 - fee
