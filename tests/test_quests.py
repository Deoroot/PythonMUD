"""Tests for mudgame/systems/quests.py — pure quest engine functions.

All tests are free of Evennia imports; they operate only on QUEST_DEFS and
the pure functions exported from quests.py.
"""

from __future__ import annotations

import sys
import os

# Point sys.path so mudgame packages resolve.
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

import pytest
from mudgame.systems.quests import (
    QUEST_DEFS,
    QUEST_ALIASES,
    resolve_alias,
    init_quest_progress,
    is_quest_complete,
    update_kill_progress,
    update_location_progress,
    set_event_progress,
    format_quest_objectives,
)

# ---------------------------------------------------------------------------
# QUEST_DEFS schema
# ---------------------------------------------------------------------------

class TestQuestDefsSchema:
    """QUEST_DEFS must have the expected keys and objective shapes."""

    ALL_KEYS = [
        "helion_intro_colony_defense",
        "vanta_expedition_artifact_recovery",
        "kess_clear_scrapforge",
        "thorne_blade_trial",
        "lyros_vault_recon",
    ]

    def test_all_five_quests_present(self):
        for key in self.ALL_KEYS:
            assert key in QUEST_DEFS, f"Missing quest: {key}"

    def test_each_quest_has_name(self):
        for key, defn in QUEST_DEFS.items():
            assert "name" in defn, f"{key} missing 'name'"

    def test_each_quest_has_giver(self):
        for key, defn in QUEST_DEFS.items():
            assert "giver" in defn, f"{key} missing 'giver'"

    def test_each_quest_has_objectives_list(self):
        for key, defn in QUEST_DEFS.items():
            assert isinstance(defn.get("objectives"), list), f"{key}: objectives must be a list"
            assert len(defn["objectives"]) > 0, f"{key}: objectives must not be empty"

    def test_kill_objectives_have_mob_key_and_count(self):
        for qkey, defn in QUEST_DEFS.items():
            for obj in defn.get("objectives", []):
                if obj["type"] == "kill":
                    assert "mob_key" in obj, f"{qkey}/{obj['id']} kill missing mob_key"
                    assert obj.get("count", 0) > 0, f"{qkey}/{obj['id']} kill count must be > 0"

    def test_location_objectives_have_room_key(self):
        for qkey, defn in QUEST_DEFS.items():
            for obj in defn.get("objectives", []):
                if obj["type"] == "location":
                    assert "room_key" in obj, f"{qkey}/{obj['id']} location missing room_key"

    def test_each_quest_has_rewards(self):
        for key, defn in QUEST_DEFS.items():
            assert "rewards" in defn, f"{key} missing rewards"
            rewards = defn["rewards"]
            assert rewards.get("xp", 0) > 0, f"{key} rewards.xp must be > 0"

    def test_aliases_cover_all_quests(self):
        for alias, key in QUEST_ALIASES.items():
            assert key in QUEST_DEFS, f"Alias '{alias}' → '{key}' not in QUEST_DEFS"


# ---------------------------------------------------------------------------
# resolve_alias
# ---------------------------------------------------------------------------

class TestResolveAlias:
    def test_short_alias_intro(self):
        assert resolve_alias("intro") == "helion_intro_colony_defense"

    def test_short_alias_vanta(self):
        assert resolve_alias("vanta") == "vanta_expedition_artifact_recovery"

    def test_short_alias_kess(self):
        assert resolve_alias("kess") == "kess_clear_scrapforge"

    def test_short_alias_thorne(self):
        assert resolve_alias("thorne") == "thorne_blade_trial"

    def test_short_alias_lyros(self):
        assert resolve_alias("lyros") == "lyros_vault_recon"

    def test_full_key_passthrough(self):
        assert resolve_alias("helion_intro_colony_defense") == "helion_intro_colony_defense"

    def test_unknown_key_returns_none(self):
        assert resolve_alias("completely_unknown") is None

    def test_empty_string_returns_none(self):
        assert resolve_alias("") is None


# ---------------------------------------------------------------------------
# init_quest_progress
# ---------------------------------------------------------------------------

class TestInitQuestProgress:
    def test_intro_kill_counter_starts_zero(self):
        prog = init_quest_progress("helion_intro_colony_defense")
        assert prog["kills_warren_raider"] == 0

    def test_intro_kill_req_matches_def(self):
        prog = init_quest_progress("helion_intro_colony_defense")
        assert prog["kills_warren_raider_req"] == 2

    def test_intro_talk_event_pre_set_true(self):
        prog = init_quest_progress("helion_intro_colony_defense")
        assert prog["talk_kaine"] is True

    def test_intro_report_flag_starts_false(self):
        prog = init_quest_progress("helion_intro_colony_defense")
        assert prog["report_kaine"] is False

    def test_vanta_event_flags_start_false(self):
        prog = init_quest_progress("vanta_expedition_artifact_recovery")
        assert prog["boarded_shuttle"] is False
        assert prog["arrived_vanta"] is False
        assert prog["returned_helion"] is False

    def test_vanta_kill_counters_start_zero(self):
        prog = init_quest_progress("vanta_expedition_artifact_recovery")
        assert prog["kills_glass_stalker"] == 0
        assert prog["kills_vault_guardian"] == 0

    def test_vanta_kill_reqs_match_defs(self):
        prog = init_quest_progress("vanta_expedition_artifact_recovery")
        assert prog["kills_glass_stalker_req"] == 3
        assert prog["kills_vault_guardian_req"] == 1

    def test_lyros_location_flag_starts_false(self):
        prog = init_quest_progress("lyros_vault_recon")
        assert prog["vault_reached"] is False

    def test_lyros_talk_event_pre_set_true(self):
        prog = init_quest_progress("lyros_vault_recon")
        assert prog["talk_lyros"] is True

    def test_unknown_quest_returns_empty_dict(self):
        assert init_quest_progress("nonexistent_quest") == {}

    def test_does_not_mutate_between_calls(self):
        prog1 = init_quest_progress("helion_intro_colony_defense")
        prog2 = init_quest_progress("helion_intro_colony_defense")
        prog1["kills_warren_raider"] = 99
        assert prog2["kills_warren_raider"] == 0


# ---------------------------------------------------------------------------
# is_quest_complete
# ---------------------------------------------------------------------------

class TestIsQuestComplete:
    def _fresh(self, key: str) -> dict:
        return init_quest_progress(key)

    def test_fresh_progress_not_complete(self):
        prog = self._fresh("helion_intro_colony_defense")
        assert is_quest_complete("helion_intro_colony_defense", prog) is False

    def test_intro_complete_when_kills_met(self):
        prog = self._fresh("helion_intro_colony_defense")
        prog["kills_warren_raider"] = 2
        assert is_quest_complete("helion_intro_colony_defense", prog) is True

    def test_intro_not_complete_with_one_kill(self):
        prog = self._fresh("helion_intro_colony_defense")
        prog["kills_warren_raider"] = 1
        assert is_quest_complete("helion_intro_colony_defense", prog) is False

    def test_report_flag_not_required_for_complete(self):
        # report objectives are NOT checked by is_quest_complete.
        prog = self._fresh("helion_intro_colony_defense")
        prog["kills_warren_raider"] = 2
        prog["report_kaine"] = False  # still complete
        assert is_quest_complete("helion_intro_colony_defense", prog) is True

    def test_vanta_incomplete_missing_events(self):
        prog = self._fresh("vanta_expedition_artifact_recovery")
        prog["kills_glass_stalker"] = 3
        prog["kills_vault_guardian"] = 1
        # boarded_shuttle and arrived_vanta and returned_helion still False
        assert is_quest_complete("vanta_expedition_artifact_recovery", prog) is False

    def test_vanta_complete_all_objectives_met(self):
        prog = self._fresh("vanta_expedition_artifact_recovery")
        prog["boarded_shuttle"] = True
        prog["arrived_vanta"] = True
        prog["kills_glass_stalker"] = 3
        prog["kills_vault_guardian"] = 1
        prog["returned_helion"] = True
        assert is_quest_complete("vanta_expedition_artifact_recovery", prog) is True

    def test_kess_complete(self):
        prog = self._fresh("kess_clear_scrapforge")
        prog["kills_slag_hound"] = 2
        assert is_quest_complete("kess_clear_scrapforge", prog) is True

    def test_thorne_complete(self):
        prog = self._fresh("thorne_blade_trial")
        prog["kills_glass_stalker"] = 2
        assert is_quest_complete("thorne_blade_trial", prog) is True

    def test_lyros_complete_when_vault_reached(self):
        prog = self._fresh("lyros_vault_recon")
        prog["vault_reached"] = True
        assert is_quest_complete("lyros_vault_recon", prog) is True

    def test_none_progress_returns_false(self):
        assert is_quest_complete("helion_intro_colony_defense", None) is False

    def test_unknown_quest_returns_false(self):
        assert is_quest_complete("no_such_quest", {}) is False


# ---------------------------------------------------------------------------
# update_kill_progress
# ---------------------------------------------------------------------------

class TestUpdateKillProgress:
    def test_kills_warren_raider_increments_intro(self):
        prog = init_quest_progress("helion_intro_colony_defense")
        active = {"helion_intro_colony_defense": prog}
        update_kill_progress(active, "warren_raider")
        assert prog["kills_warren_raider"] == 1

    def test_kills_capped_at_req(self):
        prog = init_quest_progress("helion_intro_colony_defense")
        active = {"helion_intro_colony_defense": prog}
        for _ in range(10):
            update_kill_progress(active, "warren_raider")
        assert prog["kills_warren_raider"] == 2  # capped at req=2

    def test_wrong_mob_key_does_nothing(self):
        prog = init_quest_progress("helion_intro_colony_defense")
        active = {"helion_intro_colony_defense": prog}
        update_kill_progress(active, "slag_hound")
        assert prog["kills_warren_raider"] == 0

    def test_glass_stalker_updates_both_vanta_and_thorne(self):
        vanta = init_quest_progress("vanta_expedition_artifact_recovery")
        thorne = init_quest_progress("thorne_blade_trial")
        active = {
            "vanta_expedition_artifact_recovery": vanta,
            "thorne_blade_trial": thorne,
        }
        update_kill_progress(active, "glass_stalker")
        assert vanta["kills_glass_stalker"] == 1
        assert thorne["kills_glass_stalker"] == 1

    def test_vault_guardian_kill_updates_vanta(self):
        prog = init_quest_progress("vanta_expedition_artifact_recovery")
        active = {"vanta_expedition_artifact_recovery": prog}
        update_kill_progress(active, "vault_guardian")
        assert prog["kills_vault_guardian"] == 1

    def test_inactive_quest_not_updated(self):
        active = {}  # no active quests
        update_kill_progress(active, "warren_raider")
        # no crash, no state change


# ---------------------------------------------------------------------------
# update_location_progress
# ---------------------------------------------------------------------------

class TestUpdateLocationProgress:
    def test_vault_reached_on_entry(self):
        prog = init_quest_progress("lyros_vault_recon")
        active = {"lyros_vault_recon": prog}
        msgs = update_location_progress(active, "vanta_ruins_vault")
        assert prog["vault_reached"] is True
        assert len(msgs) == 1
        assert "vault" in msgs[0].lower() or "reach" in msgs[0].lower()

    def test_location_not_set_in_wrong_room(self):
        prog = init_quest_progress("lyros_vault_recon")
        active = {"lyros_vault_recon": prog}
        msgs = update_location_progress(active, "helion_gate")
        assert prog["vault_reached"] is False
        assert msgs == []

    def test_second_entry_does_not_duplicate_message(self):
        prog = init_quest_progress("lyros_vault_recon")
        active = {"lyros_vault_recon": prog}
        update_location_progress(active, "vanta_ruins_vault")
        msgs2 = update_location_progress(active, "vanta_ruins_vault")
        assert msgs2 == []  # already set, no second notification

    def test_non_location_quests_not_affected(self):
        prog = init_quest_progress("helion_intro_colony_defense")
        active = {"helion_intro_colony_defense": prog}
        msgs = update_location_progress(active, "vanta_ruins_vault")
        assert msgs == []


# ---------------------------------------------------------------------------
# set_event_progress
# ---------------------------------------------------------------------------

class TestSetEventProgress:
    def test_set_boarded_shuttle(self):
        prog = init_quest_progress("vanta_expedition_artifact_recovery")
        active = {"vanta_expedition_artifact_recovery": prog}
        set_event_progress(active, "vanta_expedition_artifact_recovery", "boarded_shuttle")
        assert prog["boarded_shuttle"] is True

    def test_set_on_inactive_quest_does_nothing(self):
        active = {}
        # Must not raise.
        set_event_progress(active, "helion_intro_colony_defense", "talk_kaine")

    def test_set_unknown_key_does_not_crash(self):
        prog = init_quest_progress("helion_intro_colony_defense")
        active = {"helion_intro_colony_defense": prog}
        set_event_progress(active, "helion_intro_colony_defense", "nonexistent_flag")
        # Key is added (silently) — that's acceptable; main requirement is no crash.


# ---------------------------------------------------------------------------
# format_quest_objectives
# ---------------------------------------------------------------------------

class TestFormatQuestObjectives:
    def test_returns_list_of_strings(self):
        prog = init_quest_progress("helion_intro_colony_defense")
        lines = format_quest_objectives("helion_intro_colony_defense", prog)
        assert isinstance(lines, list)
        assert all(isinstance(l, str) for l in lines)

    def test_number_of_lines_matches_objectives(self):
        for key, defn in QUEST_DEFS.items():
            prog = init_quest_progress(key)
            lines = format_quest_objectives(key, prog)
            assert len(lines) == len(defn["objectives"]), (
                f"{key}: expected {len(defn['objectives'])} lines, got {len(lines)}"
            )

    def test_kill_objective_shows_count_fraction(self):
        prog = init_quest_progress("helion_intro_colony_defense")
        prog["kills_warren_raider"] = 1
        lines = format_quest_objectives("helion_intro_colony_defense", prog)
        kill_line = next(l for l in lines if "Warren" in l)
        assert "1/2" in kill_line

    def test_done_event_shows_done_tag(self):
        prog = init_quest_progress("helion_intro_colony_defense")
        # talk_kaine is pre-set True
        lines = format_quest_objectives("helion_intro_colony_defense", prog)
        talk_line = next(l for l in lines if "Kaine" in l and "Marshal" in l)
        assert "done" in talk_line

    def test_pending_event_shows_pending_tag(self):
        prog = init_quest_progress("helion_intro_colony_defense")
        lines = format_quest_objectives("helion_intro_colony_defense", prog)
        report_line = next(l for l in lines if "Return" in l)
        assert "pending" in report_line

    def test_unknown_quest_returns_empty(self):
        assert format_quest_objectives("no_such_quest", {}) == []

    def test_none_progress_returns_empty(self):
        assert format_quest_objectives("helion_intro_colony_defense", None) == []
