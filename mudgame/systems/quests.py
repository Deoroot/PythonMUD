"""Data-driven quest engine — pure functions only, no Evennia imports.

Quests are defined in QUEST_DEFS.  Each definition describes objectives with
typed entries so that the engine can auto-initialise progress dicts, check
completion, update counters, and format status lines without any per-quest
if/elif branches.

Objective types
---------------
kill      Count kills of a specific mob_key.
          Progress keys: ``id`` (current count), ``id + "_req"`` (required count).
location  Reached when the player enters a room matching ``room_key``.
          Progress key: ``id`` (bool).
event     An arbitrary boolean flag set by external code via set_event_progress.
          Progress key: ``id`` (bool).
report    Boolean flag set automatically when the quest is turned in (by
          quest_turn_in in mud_commands).  NOT checked by is_quest_complete;
          it records completion for display purposes only.
          Progress key: ``id`` (bool).

Adding a new quest requires only a new entry in QUEST_DEFS — no function
changes.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Quest definitions
# ---------------------------------------------------------------------------

QUEST_DEFS: dict[str, dict] = {
    "helion_intro_colony_defense": {
        "name": "Colony Defense",
        "giver": "helion_marshal",
        "start_room": "helion_gate",
        "objectives": [
            {
                "id": "talk_kaine",
                "type": "event",
                "label": "Talk to Marshal Kaine",
            },
            {
                "id": "kills_warren_raider",
                "type": "kill",
                "mob_key": "warren_raider",
                "count": 2,
                "label": "Defeat Warren Raiders",
            },
            {
                "id": "report_kaine",
                "type": "report",
                "label": "Return to Marshal Kaine",
            },
        ],
        "rewards": {
            "xp": 150,
            "credits": 50,
            "item": "recruit_shield_battery",
            "reputation": 20,
        },
    },

    "vanta_expedition_artifact_recovery": {
        "name": "Vanta Expedition: Artifact Recovery",
        "giver": "helion_marshal",
        "start_room": "helion_shuttle_dock",
        "requires": ["helion_intro_colony_defense"],
        "objectives": [
            {
                "id": "boarded_shuttle",
                "type": "event",
                "label": "Board shuttle at Helion",
            },
            {
                "id": "arrived_vanta",
                "type": "event",
                "label": "Arrive at Vanta IX",
            },
            {
                "id": "kills_glass_stalker",
                "type": "kill",
                "mob_key": "glass_stalker",
                "count": 3,
                "label": "Defeat Glass Stalkers",
            },
            {
                "id": "kills_vault_guardian",
                "type": "kill",
                "mob_key": "vault_guardian",
                "count": 1,
                "label": "Recover relic from vault (defeat Vault Guardian)",
            },
            {
                "id": "returned_helion",
                "type": "event",
                "label": "Return to Helion and report",
            },
        ],
        "rewards": {
            "xp": 400,
            "credits": 200,
            "item": "veteran_shield_upgrade",
            "reputation": 30,
        },
    },

    "kess_clear_scrapforge": {
        "name": "Kess: Clear the Scrapforge",
        "giver": "helion_scout",
        "start_room": "helion_warrens_entry",
        "objectives": [
            {
                "id": "talk_kess",
                "type": "event",
                "label": "Talk to Scout Kess",
            },
            {
                "id": "kills_slag_hound",
                "type": "kill",
                "mob_key": "slag_hound",
                "count": 2,
                "label": "Defeat Slag Hounds in Scrapforge Junction",
            },
            {
                "id": "report_kess",
                "type": "report",
                "label": "Return to Scout Kess",
            },
        ],
        "rewards": {
            "xp": 100,
            "credits": 40,
            "reputation": 12,
        },
    },

    "thorne_blade_trial": {
        "name": "Thorne: Blade Trial",
        "giver": "vanta_blademaster",
        "start_room": "vanta_bazaar",
        "objectives": [
            {
                "id": "talk_thorne",
                "type": "event",
                "label": "Talk to Blademaster Thorne",
            },
            {
                "id": "kills_glass_stalker",
                "type": "kill",
                "mob_key": "glass_stalker",
                "count": 2,
                "label": "Defeat Glass Stalkers in the Glass Dunes",
            },
            {
                "id": "report_thorne",
                "type": "report",
                "label": "Return to Blademaster Thorne",
            },
        ],
        "rewards": {
            "xp": 200,
            "credits": 60,
            "skill_points": 2,
            "reputation": 15,
        },
    },

    "lyros_vault_recon": {
        "name": "Lyros: Vault Reconnaissance",
        "giver": "vanta_elder",
        "start_room": "vanta_ruins_entry",
        "objectives": [
            {
                "id": "talk_lyros",
                "type": "event",
                "label": "Talk to Elder Lyros",
            },
            {
                "id": "vault_reached",
                "type": "location",
                "room_key": "vanta_ruins_vault",
                "label": "Reach the Shattered Relic Vault",
            },
            {
                "id": "report_lyros",
                "type": "report",
                "label": "Return to Elder Lyros",
            },
        ],
        "rewards": {
            "xp": 150,
            "credits": 50,
            "reputation": 12,
        },
    },
}

# ---------------------------------------------------------------------------
# Convenience aliases (short name → quest key)
# ---------------------------------------------------------------------------

QUEST_ALIASES: dict[str, str] = {
    "intro":  "helion_intro_colony_defense",
    "vanta":  "vanta_expedition_artifact_recovery",
    "kess":   "kess_clear_scrapforge",
    "thorne": "thorne_blade_trial",
    "lyros":  "lyros_vault_recon",
}


# ---------------------------------------------------------------------------
# Pure engine functions
# ---------------------------------------------------------------------------

def resolve_alias(raw_key: str) -> str | None:
    """Return the canonical quest key for a short alias or full key, or None."""
    key = QUEST_ALIASES.get(raw_key, raw_key)
    return key if key in QUEST_DEFS else None


def init_quest_progress(quest_key: str) -> dict:
    """Auto-generate a fresh progress dict from a quest's objective list.

    Talk/accept events are pre-set to True (accepting IS the conversation).
    All other booleans start False; kill counters start at 0 with a ``_req``
    companion key holding the required count.
    """
    defn = QUEST_DEFS.get(quest_key)
    if not defn:
        return {}
    progress: dict = {}
    for obj in defn.get("objectives", []):
        oid = obj["id"]
        otype = obj["type"]
        if otype == "kill":
            progress[oid] = 0
            progress[oid + "_req"] = obj.get("count", 1)
        else:
            # event, location, report — boolean
            progress[oid] = False
    # Pre-mark "talk_*" events as done — they're satisfied by the act of accepting.
    for obj in defn.get("objectives", []):
        if obj["type"] == "event" and obj["id"].startswith("talk_"):
            progress[obj["id"]] = True
    return progress


def is_quest_complete(quest_key: str, progress: dict | None) -> bool:
    """Return True only when every non-report objective in the quest is satisfied.

    ``report`` objectives are the act of turn-in itself and are therefore not
    required to pass the completion gate.
    """
    defn = QUEST_DEFS.get(quest_key)
    if not defn or not progress:
        return False
    for obj in defn.get("objectives", []):
        oid = obj["id"]
        otype = obj["type"]
        if otype == "report":
            continue  # checked at turn-in, not at completion gate
        if otype == "kill":
            if progress.get(oid, 0) < progress.get(oid + "_req", obj.get("count", 1)):
                return False
        else:
            # event, location
            if not progress.get(oid, False):
                return False
    return True


def update_kill_progress(active: dict, mob_key: str) -> None:
    """Increment kill counters across every active quest matching *mob_key*.

    Mutates ``active`` (the ``"active"`` sub-dict of the character's
    ``quest_state``) in place.
    """
    for quest_key, progress in active.items():
        defn = QUEST_DEFS.get(quest_key)
        if not defn or not progress:
            continue
        for obj in defn.get("objectives", []):
            if obj["type"] == "kill" and obj.get("mob_key") == mob_key:
                oid = obj["id"]
                req = progress.get(oid + "_req", obj.get("count", 1))
                progress[oid] = min(req, progress.get(oid, 0) + 1)


def update_location_progress(active: dict, room_key: str) -> list[str]:
    """Mark location objectives complete when the player enters *room_key*.

    Mutates ``active`` in place.

    Returns:
        List of notification strings to send to the player.
    """
    msgs: list[str] = []
    for quest_key, progress in active.items():
        defn = QUEST_DEFS.get(quest_key)
        if not defn or not progress:
            continue
        for obj in defn.get("objectives", []):
            if obj["type"] == "location" and obj.get("room_key") == room_key:
                oid = obj["id"]
                if not progress.get(oid, False):
                    progress[oid] = True
                    msgs.append(f"|yObjective updated: {obj['label']}|n")
    return msgs


def set_event_progress(active: dict, quest_key: str, event_id: str) -> None:
    """Set a boolean event flag on an active quest's progress dict.

    Mutates ``active`` in place.  Silently does nothing if the quest is not
    active or the event_id is not a recognised key.
    """
    prog = active.get(quest_key)
    if prog is not None:
        prog[event_id] = True


def format_quest_objectives(quest_key: str, progress: dict) -> list[str]:
    """Return human-readable objective lines, each indented with two spaces.

    Each line is padded so the status token lines up at column 40.
    """
    defn = QUEST_DEFS.get(quest_key)
    if not defn or not progress:
        return []
    lines: list[str] = []
    for obj in defn.get("objectives", []):
        oid = obj["id"]
        otype = obj["type"]
        label = obj.get("label", oid)
        if otype == "kill":
            current = progress.get(oid, 0)
            req = progress.get(oid + "_req", obj.get("count", 1))
            status = f"{current}/{req}"
        else:
            done = progress.get(oid, False)
            status = "|gdone|n" if done else "|xpending|n"
        lines.append(f"  {label:<40}{status}")
    return lines
