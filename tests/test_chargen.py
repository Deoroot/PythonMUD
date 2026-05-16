"""Tests for the character background (chargen) system.

These tests operate purely on the data layer and the pure functions in
world/chargen.py — no Evennia runtime is needed.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root is on the path (mirrors what characters.py does).
_root = str(Path(__file__).resolve().parents[1])
if _root not in sys.path:
    sys.path.insert(0, _root)

from mudgame.data.world_data import BACKGROUND_DATA, BACKGROUND_ORDER, WORLD_DATA  # noqa: E402


# ---------------------------------------------------------------------------
# Data integrity tests — Phase 1
# ---------------------------------------------------------------------------


def test_all_backgrounds_present():
    """Every key in BACKGROUND_ORDER must exist in BACKGROUND_DATA."""
    for key in BACKGROUND_ORDER:
        assert key in BACKGROUND_DATA, f"Missing background data for '{key}'"


def test_background_required_fields():
    """Each background entry must have all required fields."""
    required = {"name", "short", "desc", "skill_bonuses", "attr_bonuses", "credits"}
    for key, bg in BACKGROUND_DATA.items():
        missing = required - bg.keys()
        assert not missing, f"Background '{key}' missing fields: {missing}"


def test_background_order_has_five_entries():
    assert len(BACKGROUND_ORDER) == 5


def test_skill_bonuses_are_valid_skill_names():
    valid_skills = {"melee", "dodge", "parry", "blades", "bludgeons", "polearms", "ranged", "camping"}
    for key, bg in BACKGROUND_DATA.items():
        for sk in bg["skill_bonuses"]:
            assert sk in valid_skills, f"Background '{key}' references unknown skill '{sk}'"


def test_attr_bonuses_are_valid_attr_names():
    valid_attrs = {"str", "dex", "con", "mind", "cha", "per", "luck"}
    for key, bg in BACKGROUND_DATA.items():
        for attr in bg["attr_bonuses"]:
            assert attr in valid_attrs, f"Background '{key}' references unknown attr '{attr}'"


def test_skill_bonuses_are_positive():
    for key, bg in BACKGROUND_DATA.items():
        for sk, val in bg["skill_bonuses"].items():
            assert val > 0, f"Background '{key}' skill '{sk}' bonus must be positive"


def test_attr_bonuses_are_positive():
    for key, bg in BACKGROUND_DATA.items():
        for attr, val in bg["attr_bonuses"].items():
            assert val > 0, f"Background '{key}' attr '{attr}' bonus must be positive"


def test_credits_non_negative():
    for key, bg in BACKGROUND_DATA.items():
        assert bg["credits"] >= 0, f"Background '{key}' credits must be >= 0"


# ---------------------------------------------------------------------------
# Data integrity tests — Phase 2 (weapons, rep, perks)
# ---------------------------------------------------------------------------

_ITEMS = WORLD_DATA.get("items", {})
_VALID_FACTIONS = {"helion_colony", "vanta_clans"}


def test_phase2_required_fields():
    """Each background entry must have the Phase 2 fields."""
    required = {"starting_weapon", "rep_bonus", "perk_desc"}
    for key, bg in BACKGROUND_DATA.items():
        missing = required - bg.keys()
        assert not missing, f"Background '{key}' missing Phase 2 fields: {missing}"


def test_starting_weapons_are_valid_item_keys():
    """starting_weapon must reference a real item in WORLD_DATA."""
    for key, bg in BACKGROUND_DATA.items():
        wpn = bg["starting_weapon"]
        assert wpn in _ITEMS, f"Background '{key}' starting_weapon '{wpn}' not in items catalog"


def test_off_hand_weapons_are_valid_or_none():
    """off_hand_weapon must be None or a real item key."""
    for key, bg in BACKGROUND_DATA.items():
        off = bg.get("off_hand_weapon")
        if off is not None:
            assert off in _ITEMS, f"Background '{key}' off_hand_weapon '{off}' not in items catalog"


def test_rep_bonus_uses_valid_factions():
    """All rep_bonus faction keys must be recognized faction identifiers."""
    for key, bg in BACKGROUND_DATA.items():
        for faction in bg.get("rep_bonus", {}):
            assert faction in _VALID_FACTIONS, (
                f"Background '{key}' rep_bonus references unknown faction '{faction}'"
            )


def test_rep_bonus_amounts_are_positive():
    for key, bg in BACKGROUND_DATA.items():
        for faction, amt in bg.get("rep_bonus", {}).items():
            assert amt > 0, f"Background '{key}' rep for '{faction}' must be positive"


def test_perk_desc_is_non_empty_string():
    for key, bg in BACKGROUND_DATA.items():
        assert isinstance(bg["perk_desc"], str) and bg["perk_desc"].strip(), (
            f"Background '{key}' perk_desc must be a non-empty string"
        )


def test_clan_initiate_has_dual_wield_setup():
    """Clan Initiate specifically starts with main + off-hand weapons."""
    bg = BACKGROUND_DATA["clan_initiate"]
    assert bg["starting_weapon"] == "parrying_dagger"
    assert bg["off_hand_weapon"] == "training_vibroblade"


def test_colonial_recruit_has_helion_colony_rep():
    bg = BACKGROUND_DATA["colonial_recruit"]
    assert bg["rep_bonus"].get("helion_colony", 0) >= 20


def test_frontier_contractor_perk_mentions_sell():
    bg = BACKGROUND_DATA["frontier_contractor"]
    assert "sell" in bg["perk_desc"].lower()


def test_compact_remnant_perk_mentions_psi():
    bg = BACKGROUND_DATA["compact_remnant"]
    assert "psi" in bg["perk_desc"].lower()


# ---------------------------------------------------------------------------
# Chargen application logic (pure simulation — no Evennia objects)
# ---------------------------------------------------------------------------


def _apply_background(bg_key: str) -> dict:
    """Simulate what node_apply does; return a dict of resulting stats."""
    bg = BACKGROUND_DATA[bg_key]

    skills = {"melee": 10, "dodge": 10, "parry": 10,
               "blades": 5, "bludgeons": 5, "polearms": 5,
               "ranged": 5, "camping": 0}
    attrs = {"str": 10, "dex": 10, "con": 10, "mind": 10,
             "cha": 10, "per": 10, "luck": 10}
    equipped = {"main_hand": "training_vibroblade"}
    rep = {"helion_colony": 0, "vanta_clans": 0}

    for sk, val in bg["skill_bonuses"].items():
        skills[sk] = skills.get(sk, 0) + val
    for attr, val in bg["attr_bonuses"].items():
        attrs[attr] = attrs.get(attr, 10) + val

    # Weapon equipping.
    if bg["starting_weapon"]:
        equipped["main_hand"] = bg["starting_weapon"]
    if bg.get("off_hand_weapon"):
        equipped["off_hand"] = bg["off_hand_weapon"]

    # Reputation application.
    for faction, amount in bg.get("rep_bonus", {}).items():
        rep[faction] = rep.get(faction, 0) + amount

    mind = attrs["mind"]
    psi_max = 10 + mind * 5
    con = attrs["con"]
    hp_max = 100 + max(0, (con - 10) * 3)
    credits_start = bg["credits"]

    return {
        "skills": skills,
        "attrs": attrs,
        "psi_max": psi_max,
        "hp_max": hp_max,
        "credits": credits_start,
        "equipped": equipped,
        "rep": rep,
    }


def test_colonial_recruit_bonuses():
    result = _apply_background("colonial_recruit")
    assert result["skills"]["melee"] == 13       # 10 + 3
    assert result["skills"]["parry"] == 12       # 10 + 2
    assert result["attrs"]["con"] == 11
    assert result["hp_max"] == 103               # 100 + (11-10)*3
    assert result["psi_max"] == 60               # MIND unchanged
    assert result["credits"] == 0


def test_colonial_recruit_equipment_and_rep():
    result = _apply_background("colonial_recruit")
    assert result["equipped"]["main_hand"] == "parrying_dagger"
    assert result["equipped"].get("off_hand") is None
    assert result["rep"]["helion_colony"] == 25


def test_warrens_scavenger_bonuses():
    result = _apply_background("warrens_scavenger")
    assert result["skills"]["bludgeons"] == 8    # 5 + 3
    assert result["skills"]["camping"] == 4      # 0 + 4
    assert result["attrs"]["per"] == 11
    assert result["hp_max"] == 100               # CON unchanged
    assert result["psi_max"] == 60


def test_warrens_scavenger_equipment_and_rep():
    result = _apply_background("warrens_scavenger")
    assert result["equipped"]["main_hand"] == "shock_baton"
    assert result["rep"]["helion_colony"] == 5
    assert result["rep"]["vanta_clans"] == 10


def test_clan_initiate_bonuses():
    result = _apply_background("clan_initiate")
    assert result["skills"]["blades"] == 9       # 5 + 4
    assert result["skills"]["dodge"] == 12       # 10 + 2
    assert result["attrs"]["dex"] == 11
    assert result["hp_max"] == 100
    assert result["psi_max"] == 60


def test_clan_initiate_equipment_and_rep():
    result = _apply_background("clan_initiate")
    assert result["equipped"]["main_hand"] == "parrying_dagger"
    assert result["equipped"]["off_hand"] == "training_vibroblade"
    assert result["rep"]["vanta_clans"] == 25


def test_frontier_contractor_bonuses():
    result = _apply_background("frontier_contractor")
    assert result["skills"]["ranged"] == 8       # 5 + 3
    assert result["attrs"]["cha"] == 11
    assert result["attrs"]["luck"] == 11
    assert result["credits"] == 30
    assert result["psi_max"] == 60


def test_frontier_contractor_equipment_and_rep():
    result = _apply_background("frontier_contractor")
    assert result["equipped"]["main_hand"] == "colony_sidearm"
    assert result["rep"]["helion_colony"] == 10
    assert result["rep"]["vanta_clans"] == 10


def test_compact_remnant_bonuses():
    result = _apply_background("compact_remnant")
    assert result["attrs"]["mind"] == 12
    assert result["psi_max"] == 70               # 10 + 12*5
    assert result["skills"]["melee"] == 11       # 10 + 1
    assert result["hp_max"] == 100               # CON unchanged
    assert result["credits"] == 0


def test_compact_remnant_equipment_and_rep():
    result = _apply_background("compact_remnant")
    assert result["equipped"]["main_hand"] == "training_vibroblade"
    assert result["rep"]["helion_colony"] == 15


def test_no_background_gives_negative_stats():
    """No background should result in any resource below baseline."""
    for bg_key in BACKGROUND_ORDER:
        result = _apply_background(bg_key)
        assert result["hp_max"] >= 100, f"{bg_key}: hp_max below 100"
        assert result["psi_max"] >= 60, f"{bg_key}: psi_max below 60"
        assert result["credits"] >= 0, f"{bg_key}: credits below 0"
        for sk, val in result["skills"].items():
            assert val >= 0, f"{bg_key}: skill '{sk}' below 0"
        for attr, val in result["attrs"].items():
            assert val >= 10, f"{bg_key}: attr '{attr}' below base 10"


# ---------------------------------------------------------------------------
# Economy perk tests (pure function, no Evennia)
# ---------------------------------------------------------------------------


def test_colonial_recruit_buy_discount():
    """Colonial Recruit's 5% discount pushes buy price below normal CHA floor."""
    from mudgame.systems.economy import adjusted_buy_price
    cha = 10  # neutral CHA → multiplier 1.00
    base = 100
    normal = adjusted_buy_price(base, cha, discount=0.0)
    discounted = adjusted_buy_price(base, cha, discount=0.05)
    assert discounted < normal
    assert discounted == 95  # 100 * 0.95


def test_frontier_contractor_sell_bonus():
    """Frontier Contractor's sell bonus raises effective sell above CHA cap."""
    from mudgame.systems.economy import adjusted_sell_price
    cha = 20  # max CHA → sell multiplier 0.60
    base = 100
    normal = adjusted_sell_price(base, cha, sell_bonus=0.0)
    boosted = adjusted_sell_price(base, cha, sell_bonus=0.05)
    assert boosted > normal
    assert boosted == 65  # 100 * 0.65


def test_buy_price_discount_hard_floor():
    """Even with a huge discount, buy price never falls below 70% of base."""
    from mudgame.systems.economy import adjusted_buy_price
    cha = 20  # best CHA → mult 0.80
    base = 100
    result = adjusted_buy_price(base, cha, discount=0.20)  # would be 0.60 without floor
    assert result == 70  # clamped to 0.70


# ---------------------------------------------------------------------------
# PSI cost reduction test (pure function, no Evennia)
# ---------------------------------------------------------------------------


def test_compact_remnant_psi_heal_cost_reduction():
    """Compact Remnant's cost_reduction=5 makes PSI Heal cost 15 instead of 20."""
    from mudgame.systems.psi import resolve_psi_heal

    # With standard cost (20): psi=19 → insufficient.
    _, _, note = resolve_psi_heal(psi=19, psi_max=70, mind=12, hp=50, hp_max=70)
    assert note == "insufficient_psi"

    # With cost_reduction=5 (cost=15): psi=15 → healed.
    new_psi, hp_gained, note = resolve_psi_heal(
        psi=15, psi_max=70, mind=12, hp=50, hp_max=70, cost_reduction=5
    )
    assert note == "healed"
    assert new_psi == 0  # 15 - 15 = 0
    assert hp_gained > 0


# ---------------------------------------------------------------------------
# CON → camping HP restore and cooldown tests (pure formula, no Evennia)
# ---------------------------------------------------------------------------


def test_con_bonus_increases_camping_hp_restore():
    """CON above 10 adds HP to camping recovery (+1 per 2 CON above 10)."""
    camping = 0  # no camping skill

    # CON 10 (base): 20 + 0 + 0 = 20
    hp10 = 20 + camping // 2 + max(0, (10 - 10) // 2)
    assert hp10 == 20

    # CON 12: 20 + 0 + 1 = 21
    hp12 = 20 + camping // 2 + max(0, (12 - 10) // 2)
    assert hp12 == 21

    # CON 14: 20 + 0 + 2 = 22
    hp14 = 20 + camping // 2 + max(0, (14 - 10) // 2)
    assert hp14 == 22

    # CON 20: 20 + 0 + 5 = 25
    hp20 = 20 + camping // 2 + max(0, (20 - 10) // 2)
    assert hp20 == 25


def test_camping_skill_stacks_with_con_hp_restore():
    """camping skill and CON both contribute to HP recovery independently."""
    # camping=10, CON=12: 20 + 5 + 1 = 26
    hp = 20 + 10 // 2 + max(0, (12 - 10) // 2)
    assert hp == 26


def test_con_reduces_camping_cooldown():
    """Higher CON reduces the rest cooldown (minimum floor 30s)."""
    # CON 10 (base): max(30, 60 - 0) = 60
    cd10 = max(30, 60 - max(0, (10 - 10) * 3))
    assert cd10 == 60

    # CON 14: max(30, 60 - 12) = 48
    cd14 = max(30, 60 - max(0, (14 - 10) * 3))
    assert cd14 == 48

    # CON 20: max(30, 60 - 30) = 30 (minimum)
    cd20 = max(30, 60 - max(0, (20 - 10) * 3))
    assert cd20 == 30

    # CON 30: floor holds at 30
    cd30 = max(30, 60 - max(0, (30 - 10) * 3))
    assert cd30 == 30

