"""Quest, reputation, epoch, and ledger helpers.

Extracted from cmd_utils.py.  No Command subclasses.

Exports
-------
_get_or_init_ledger(caller) -> dict
_get_or_init_reputation(caller) -> dict
_faction_for_quest(quest_key) -> str | None
_adjust_reputation(caller, faction, amount) -> int
_rep_tier(value) -> str
_CACHED_EPOCH
_get_server_epoch() -> int
_get_quest_state(caller) -> dict
_quest_by_key(key) -> dict | None
_resolve_quest_alias(raw_key) -> str | None
_initialize_quest_progress(quest_key) -> dict
_update_kill_objectives(caller, mob_key)
_update_location_objectives(caller)
_is_quest_complete(caller, quest_key) -> bool
_format_quest_progress(quest_key, prog) -> list[str]
_apply_quest_rewards(caller, quest_key) -> str
_accept_contract(caller, quest_key, require_start_room) -> tuple[bool, str]
_turnin_contract(caller, quest_key, require_giver_room) -> tuple[bool, str]
"""

from __future__ import annotations

import sys
import time
from pathlib import Path


def _ensure_project_root_on_path() -> None:
    root = str(Path(__file__).resolve().parents[2])
    if root not in sys.path:
        sys.path.insert(0, root)


_ensure_project_root_on_path()

from mudgame.systems import quests as _quests  # noqa: E402
from commands.level_utils import _check_level_up  # noqa: E402
from commands.ui_utils import _pretty_name  # noqa: E402


def _load_world_data() -> dict:
    _ensure_project_root_on_path()
    from mudgame.data.world_data import WORLD_DATA
    return WORLD_DATA


# ---------------------------------------------------------------------------
# Ledger helpers
# ---------------------------------------------------------------------------

def _get_or_init_ledger(caller) -> dict:
    ledger = caller.db.ledger
    if not ledger:
        # New characters start with their default equipped weapon in pack.
        ledger = {"credits": 0, "inventory": ["training_vibroblade"]}
    ledger.setdefault("credits", 0)
    ledger.setdefault("inventory", [])
    caller.db.ledger = ledger
    return ledger


# ---------------------------------------------------------------------------
# Reputation helpers
# ---------------------------------------------------------------------------

def _get_or_init_reputation(caller) -> dict:
    """Return and initialize faction reputation ledger."""
    rep = caller.db.reputation
    if not isinstance(rep, dict):
        rep = {"helion_colony": 0, "vanta_clans": 0}
    rep.setdefault("helion_colony", 0)
    rep.setdefault("vanta_clans", 0)
    caller.db.reputation = rep
    return rep


def _faction_for_quest(quest_key: str) -> str | None:
    """Resolve faction key from quest giver data."""
    defn = _quests.QUEST_DEFS.get(quest_key)
    if not defn:
        return None
    giver_key = defn.get("giver")
    if not giver_key:
        return None
    for npc in _load_world_data().get("npcs", []):
        if npc.get("key") == giver_key:
            return npc.get("faction")
    return None


def _adjust_reputation(caller, faction: str, amount: int) -> int:
    """Apply clamped faction reputation delta and return new value."""
    rep = _get_or_init_reputation(caller)
    current = int(rep.get(faction, 0))
    updated = max(-1000, min(1000, current + int(amount)))
    rep[faction] = updated
    caller.db.reputation = rep
    return updated


def _rep_tier(value: int) -> str:
    """Return adjective tier for reputation display."""
    if value <= -100:
        return "hostile"
    if value <= -30:
        return "unfriendly"
    if value < 30:
        return "neutral"
    if value < 100:
        return "trusted"
    return "allied"


# ---------------------------------------------------------------------------
# Server epoch / quest state
# ---------------------------------------------------------------------------

_CACHED_EPOCH: int | None = None


def _get_server_epoch() -> int:
    """Return a stable integer identifying the current server process.

    Computed once per module load as the approximate server start time
    (wall-clock seconds).  The value is stable within a process and changes
    on every full restart, so quest state stored under a different epoch is
    treated as stale.  Returns 0 if gametime is unavailable, which disables
    epoch-based clearing.
    """
    global _CACHED_EPOCH
    if _CACHED_EPOCH is not None:
        return _CACHED_EPOCH
    try:
        from evennia.utils import gametime
        _CACHED_EPOCH = int(time.time() - gametime.real_seconds_elapsed())
    except Exception:
        _CACHED_EPOCH = 0
    return _CACHED_EPOCH


def _get_quest_state(caller) -> dict:
    epoch = _get_server_epoch()
    state = caller.db.quest_state
    # If epoch is valid and the stored epoch doesn't match (including no
    # epoch stored at all), this is a new server process — clear all quest
    # progress so quests reset on the daily restart.
    if epoch and (not state or state.get("_epoch") != epoch):
        state = {"active": {}, "completed": [], "_epoch": epoch}
        caller.db.quest_state = state
        return state
    if not state:
        state = {"active": {}, "completed": []}
        caller.db.quest_state = state
    state.setdefault("active", {})
    state.setdefault("completed", [])
    return state


# ---------------------------------------------------------------------------
# Quest helpers
# ---------------------------------------------------------------------------

def _quest_by_key(key: str) -> dict | None:
    """Look up a quest definition by its canonical key."""
    return _quests.QUEST_DEFS.get(key)


def _resolve_quest_alias(raw_key: str) -> str | None:
    """Resolve a short alias or full key to a canonical quest key."""
    return _quests.resolve_alias(raw_key)


def _initialize_quest_progress(quest_key: str) -> dict:
    """Return a fresh progress dict for a quest (delegates to quests.py)."""
    return _quests.init_quest_progress(quest_key)


def _update_kill_objectives(caller, mob_key: str) -> None:
    state = _get_quest_state(caller)
    _quests.update_kill_progress(state.get("active", {}), mob_key)
    caller.db.quest_state = state


def _update_location_objectives(caller) -> None:
    state = _get_quest_state(caller)
    active = state.get("active", {})
    room = caller.location
    if not room:
        return
    room_key = room.db.room_key or room.key

    msgs = _quests.update_location_progress(active, room_key)
    for m in msgs:
        caller.msg(m)

    # UI-only vault arrival notification (not a quest objective).
    vanta = active.get("vanta_expedition_artifact_recovery")
    if vanta and room_key == "vanta_ruins_vault" and not vanta.get("kills_vault_guardian", 0):
        if not vanta.get("vault_arrival_notified"):
            vanta["vault_arrival_notified"] = True
            guardian_here = any(
                obj.key == "vault_guardian"
                for obj in room.contents
                if hasattr(obj, "db") and obj.db.actor_type == "mob"
            )
            if guardian_here:
                caller.msg(
                    "|yObjective: The Vault Guardian stands between you and the relic. "
                    "Defeat it to claim the artifact.|n"
                )
            else:
                caller.msg("|yThe vault. No guardian detected — search for the relic.|n")

    caller.db.quest_state = state


def _is_quest_complete(caller, quest_key: str) -> bool:
    state = _get_quest_state(caller)
    prog = state.get("active", {}).get(quest_key)
    return _quests.is_quest_complete(quest_key, prog)


def _format_quest_progress(quest_key: str, prog: dict) -> list[str]:
    """Return human-readable objective lines (delegates to quests.py)."""
    return _quests.format_quest_objectives(quest_key, prog)


def _apply_quest_rewards(caller, quest_key: str) -> str:
    quest = _quest_by_key(quest_key)
    if not quest:
        return "No rewards found."

    rewards = quest.get("rewards", {})
    xp_gain = int(rewards.get("xp", 0))
    credits_gain = int(rewards.get("credits", 0))
    reward_item = rewards.get("item")
    sp_gain = int(rewards.get("skill_points", 0))
    rep_gain = int(rewards.get("reputation", 10))
    rep_faction = _faction_for_quest(quest_key)

    caller.db.xp = (caller.db.xp or 0) + xp_gain
    ledger = _get_or_init_ledger(caller)
    ledger["credits"] = int(ledger.get("credits", 0)) + credits_gain
    if reward_item and reward_item not in ledger.get("inventory", []):
        ledger.setdefault("inventory", []).append(reward_item)
    caller.db.ledger = ledger

    if sp_gain > 0:
        caller.db.skill_points = (caller.db.skill_points or 0) + sp_gain

    rep_text = ""
    if rep_faction and rep_gain:
        new_rep = _adjust_reputation(caller, rep_faction, rep_gain)
        rep_text = (
            f", +{rep_gain} reputation ({rep_faction}: {new_rep} / {_rep_tier(new_rep)})"
        )

    level_msgs = _check_level_up(caller)

    item_text = f", item: {_pretty_name(reward_item)}" if reward_item else ""
    sp_text = f", +{sp_gain} skill points" if sp_gain > 0 else ""
    result = f"Rewards: +{xp_gain} XP, +{credits_gain} credits{item_text}{sp_text}{rep_text}."
    if level_msgs:
        result += "\n" + "\n".join(level_msgs)
    return result


def _accept_contract(caller, quest_key: str, require_start_room: bool = True) -> tuple[bool, str]:
    quest = _quest_by_key(quest_key)
    if not quest:
        return False, "Unknown quest key."

    state = _get_quest_state(caller)
    if quest_key in state.get("completed", []):
        return False, "You already completed that contract."
    if quest_key in state.get("active", {}):
        return False, "That contract is already active."

    requires = quest.get("requires", [])
    missing = [rq for rq in requires if rq not in state.get("completed", [])]
    if missing:
        return False, f"Contract locked. Missing prerequisite: {', '.join(missing)}"

    if require_start_room:
        room_key = caller.location.db.room_key if caller.location else ""
        if room_key != quest.get("start_room"):
            return False, "You need to be at the quest start location to accept this contract."

    state["active"][quest_key] = _initialize_quest_progress(quest_key)
    caller.db.quest_state = state
    objectives = quest.get("objectives", [])
    obj_str = ""
    if objectives:
        obj_lines = "\n".join(
            f"  |w{i + 1}.|n {obj['label'] if isinstance(obj, dict) else obj}"
            for i, obj in enumerate(objectives)
        )
        obj_str = f"\n|yObjectives:|n\n{obj_lines}"
    return True, f"|gContract accepted: {quest['name']}|n{obj_str}"


def _turnin_contract(caller, quest_key: str, require_giver_room: bool = True) -> tuple[bool, str]:
    quest = _quest_by_key(quest_key)
    if not quest:
        return False, "Unknown quest key."

    state = _get_quest_state(caller)
    if quest_key not in state.get("active", {}):
        return False, "That contract is not active."

    if require_giver_room:
        giver_room = quest.get("start_room")
        room_key = caller.location.db.room_key if caller.location else ""
        if room_key != giver_room:
            return False, "Return to the contract giver's location before turning in."

    if not _is_quest_complete(caller, quest_key):
        return False, "Contract objectives are not complete yet."

    state["active"].pop(quest_key, None)
    completed = state.setdefault("completed", [])
    if quest_key not in completed:
        completed.append(quest_key)
    caller.db.quest_state = state
    reward_text = _apply_quest_rewards(caller, quest_key)
    return True, f"|gContract completed: {quest['name']}|n\n{reward_text}"
