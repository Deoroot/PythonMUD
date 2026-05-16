"""Shared helper functions for all MUD command modules.

This module is the single import point for command helpers.  Implementations
are split across focused sub-modules:

  level_utils.py — level / skill progression helpers
  quest_utils.py — quest, reputation, epoch, and ledger helpers
  ui_utils.py    — combat display and prompt helpers

Everything from those modules is re-exported here so that existing
``from commands.cmd_utils import ...`` statements continue to work.

Functions that remain in this file directly:
  * Path / Evennia object lookup  (_find_object_by_id, _load_world_data, …)
  * Economy helpers               (_cha_adjusted_buy_price, …)
  * Guild helpers                 (_guild_skill_cap, _apply_guild_rank_passives, …)
  * Background perks              (_get_background_perks, SLEEP_DURATION)
  * Loot / credit helpers         (_drop_mob_loot, _award_mob_credits)
  * Mob respawn helpers           (RESPAWN_DELAY, _respawn_mob, repop_dead_mobs)
  * Shared deferred registries    (_SETUP_DEFERREDS, _SLEEP_DEFERREDS)
"""

from __future__ import annotations

import sys
from pathlib import Path

from evennia import search_object


def _ensure_project_root_on_path() -> None:
    root = str(Path(__file__).resolve().parents[2])
    if root not in sys.path:
        sys.path.insert(0, root)


_ensure_project_root_on_path()

from mudgame.contracts import EQUIPMENT_SLOTS, default_equipped as _default_equipped  # noqa: E402
from mudgame.systems.guilds import (  # noqa: E402
    guild_skill_cap as _guild_skill_cap_pure,
    apply_guild_stat_passives as _apply_guild_stat_passives,
    resolve_guild_join as _resolve_guild_join,
    resolve_guild_advance as _resolve_guild_advance,
)
from mudgame.systems.loot import (  # noqa: E402
    resolve_loot_drops as _resolve_loot_drops,
    resolve_credit_drop as _resolve_credit_drop,
)

# ---------------------------------------------------------------------------
# Re-exports from sub-modules
# (keeps all existing `from commands.cmd_utils import ...` working)
# ---------------------------------------------------------------------------

from commands.level_utils import (  # noqa: E402,F401
    _SKILL_SOFT_CAP,
    _SKILL_GROW_CHANCE,
    _maybe_grow_skill,
    _check_level_up,
)
from commands.ui_utils import (  # noqa: E402,F401
    _pretty_name,
    _damage_bar,
    _hit_verb,
    _mob_health_label,
    _val_color,
    _format_prompt,
    _send_prompt,
    _send_room_oob,
    _send_stats_oob,
)
from commands.quest_utils import (  # noqa: E402,F401
    _get_or_init_ledger,
    _get_or_init_reputation,
    _faction_for_quest,
    _adjust_reputation,
    _rep_tier,
    _CACHED_EPOCH,
    _get_server_epoch,
    _get_quest_state,
    _quest_by_key,
    _resolve_quest_alias,
    _initialize_quest_progress,
    _update_kill_objectives,
    _update_location_objectives,
    _is_quest_complete,
    _format_quest_progress,
    _apply_quest_rewards,
    _accept_contract,
    _turnin_contract,
)


# ---------------------------------------------------------------------------
# Basic data helpers
# ---------------------------------------------------------------------------

def _find_object_by_id(obj_id: int):
    found = search_object(f"#{obj_id}", exact=True)
    return found[0] if found else None


def _load_world_data() -> dict:
    _ensure_project_root_on_path()
    from mudgame.data.world_data import WORLD_DATA
    return WORLD_DATA


def _get_item_data(item_key: str) -> dict | None:
    """Return item definition dict from the items catalog, or None."""
    return _load_world_data().get("items", {}).get(item_key)


# ---------------------------------------------------------------------------
# Economy helpers
# ---------------------------------------------------------------------------

def _cha_adjusted_buy_price(base_price: int, cha: int, discount: float = 0.0) -> int:
    """Return buy price adjusted by CHA and optional background discount."""
    _ensure_project_root_on_path()
    from mudgame.systems.economy import adjusted_buy_price
    return adjusted_buy_price(base_price, cha, discount)


def _cha_adjusted_sell_price(base_price: int, cha: int, sell_bonus: float = 0.0) -> int:
    """Return sell payout adjusted by CHA and optional background sell bonus."""
    _ensure_project_root_on_path()
    from mudgame.systems.economy import adjusted_sell_price
    return adjusted_sell_price(base_price, cha, sell_bonus)


# ---------------------------------------------------------------------------
# Guild helpers
# ---------------------------------------------------------------------------

_GUILD_MAX_RANK = 10  # global cap; increase if world expands


def _guild_skill_cap(guild_key: str, skill_key: str, rank: int) -> int:
    """Return the maximum % trainable for a guild skill at the given rank."""
    guilds = _load_world_data().get("guilds", {})
    return _guild_skill_cap_pure(guild_key, skill_key, rank, guilds)


def _apply_guild_rank_passives(caller, guild_key: str) -> None:
    """Apply per-rank passive stat bonuses when a player joins or advances.

    Idempotent: tracks how many ranks' passives have already been applied in
    ``db.guild_passives_applied`` and only applies the delta, so calling this
    twice at the same rank is safe and has no effect.
    """
    guilds = _load_world_data().get("guilds", {})
    target_rank = (caller.db.guild_levels or {}).get(guild_key, 0)
    applied = caller.db.guild_passives_applied or {}
    already_applied = applied.get(guild_key, 0)
    delta = target_rank - already_applied
    if delta <= 0:
        return  # Already up to date; nothing to do.

    attrs = caller.db.attrs or {}
    hp_max = caller.db.hp_max or 100
    psi_max = caller.db.psi_max or 60
    for _ in range(delta):
        attrs, hp_max, psi_max = _apply_guild_stat_passives(
            attrs=attrs,
            hp_max=hp_max,
            psi_max=psi_max,
            guild_key=guild_key,
            guilds_data=guilds,
        )
    caller.db.attrs = attrs
    caller.db.hp_max = hp_max
    caller.db.psi_max = psi_max
    new_applied = dict(applied)
    new_applied[guild_key] = target_rank
    caller.db.guild_passives_applied = new_applied


def _remove_guild_rank_passives(caller, guild_key: str, n_ranks: int) -> None:
    """Reverse *n_ranks* worth of guild passive stat bonuses.

    Used by ``leaveguild`` to undo all passives accumulated through joining
    and advancing.  Clamps all values to their level-1 floor so the stats
    cannot go below baseline even if the data is somehow inconsistent.
    """
    if n_ranks <= 0:
        return
    guilds = _load_world_data().get("guilds", {})
    passives = guilds.get(guild_key, {}).get("passive_per_rank", {})
    if not passives:
        return

    attrs = dict(caller.db.attrs or {})
    hp_max = caller.db.hp_max or 100
    psi_max = caller.db.psi_max or 60

    for stat, gain in passives.items():
        total = gain * n_ranks
        if stat == "hp_max":
            hp_max = max(100, hp_max - total)
        elif stat == "psi_max":
            psi_max = max(60, psi_max - total)
        elif stat in attrs:
            attrs[stat] = max(10, attrs[stat] - total)

    caller.db.attrs = attrs
    caller.db.hp_max = hp_max
    caller.db.psi_max = psi_max
    # Clamp live values so they don't exceed the reduced maxima.
    if (caller.db.hp or 0) > hp_max:
        caller.db.hp = hp_max
    if (caller.db.psi or 0) > psi_max:
        caller.db.psi = psi_max

    # Clear the applied-passives tracking for this guild.
    applied = dict(caller.db.guild_passives_applied or {})
    applied.pop(guild_key, None)
    caller.db.guild_passives_applied = applied


def _get_guild_skill_bonuses(caller) -> dict:
    """Compute passive guild skill bonuses for the caller.

    Returns a dict:
      phys_reduction  — flat HP damage reduction (iron_stance, bulwark, mind_fortress)
      weapon_damage   — flat weapon damage bonus (throw_weight)
      crit_chance     — additive crit% (find_weakness, battle_mastery) (0.0–1.0)
      crit_damage     — extra raw damage on a crit (enhanced_criticals, battle_mastery)
      psi_heal_bonus  — extra HP restored by PSI Heal (focused_channel, psi_surge)
      stamina_max     — bonus Stamina pool (iron_will)
      psi_max         — bonus PSI pool (deep_resonance)
    """
    bonuses = {
        "phys_reduction": 0,
        "weapon_damage": 0,
        "crit_chance": 0.0,
        "crit_damage": 0,
        "psi_heal_bonus": 0,
        "stamina_max": 0,
        "psi_max": 0,
    }
    guild_levels = caller.db.guild_levels or {}
    guild_skills = caller.db.guild_skills or {}
    guilds = _load_world_data().get("guilds", {})

    for guild_key, guild_data in guilds.items():
        rank = guild_levels.get(guild_key, 0)
        if rank <= 0:
            continue
        p_skills = guild_skills.get(guild_key, {})
        for skill_key, skill_data in guild_data.get("skills", {}).items():
            if skill_data.get("type") != "passive":
                continue
            pct = p_skills.get(skill_key, 0)
            if pct <= 0:
                continue
            effect = skill_data.get("effect", "")

            # Determine the primary scalar — skills declare whichever step size
            # matches their design (per-10pct, per-20pct, or per-25pct).
            if "bonus_per_10pct" in skill_data:
                scalar = pct // 10 * skill_data["bonus_per_10pct"]
            elif "bonus_per_20pct" in skill_data:
                scalar = pct // 20 * skill_data["bonus_per_20pct"]
            elif "bonus_per_25pct" in skill_data:
                scalar = pct // 25 * skill_data["bonus_per_25pct"]
            else:
                scalar = 0

            if effect in bonuses:
                bonuses[effect] += scalar

            # battle_mastery grants crit_damage as a secondary effect alongside
            # crit_chance — handled via an explicit extra field.
            if "crit_damage_per_25pct" in skill_data:
                bonuses["crit_damage"] += pct // 25 * skill_data["crit_damage_per_25pct"]

    return bonuses


# ---------------------------------------------------------------------------
# Background perks
# ---------------------------------------------------------------------------

SLEEP_DURATION = 20  # seconds of rest before waking with full lump-sum recovery


def _get_background_perks(caller) -> dict:
    """Return passive perk values granted by the caller's starting background.

    Returns a dict with keys:
      vendor_discount         — float subtracted from the CHA buy multiplier
                                (Colonial Recruit: 0.05 → 5% cheaper at vendors)
      sleep_duration          — int seconds for the rest timer
                                (Warrens Scavenger: 14 instead of 20)
      stalker_damage_bonus    — float fraction of extra damage vs Glass Stalkers
                                (Clan Initiate: 0.25 → +25%)
      sell_bonus              — float added to sell multiplier after CHA clamp
                                (Frontier Contractor: 0.05 → raises cap to 0.65)
      psi_heal_cost_reduction — int PSI cost reduction for PSI Heal
                                (Compact Remnant: 5 → costs 15 instead of 20)
    """
    perks = {
        "vendor_discount": 0.0,
        "sleep_duration": SLEEP_DURATION,
        "stalker_damage_bonus": 0.0,
        "sell_bonus": 0.0,
        "psi_heal_cost_reduction": 0,
    }
    background = caller.db.background if hasattr(caller, "db") else None
    if background == "colonial_recruit":
        perks["vendor_discount"] = 0.05
    elif background == "warrens_scavenger":
        perks["sleep_duration"] = 14
    elif background == "clan_initiate":
        perks["stalker_damage_bonus"] = 0.25
    elif background == "frontier_contractor":
        perks["sell_bonus"] = 0.05
    elif background == "compact_remnant":
        perks["psi_heal_cost_reduction"] = 5
    return perks


# ---------------------------------------------------------------------------
# Loot / credit helpers
# ---------------------------------------------------------------------------

def _drop_mob_loot(caller, mob_key: str) -> list[str]:
    """Roll the mob's loot table and place any dropped items on the room floor.

    Each entry in ``loot_table`` is ``{"item": str, "chance": float}`` where
    ``chance`` is a 0.0–1.0 probability.  Items that pass their roll are
    appended to ``caller.location.db.floor_items`` (a list of item-key strings).

    Returns the list of item keys that were actually dropped (may be empty).
    """
    mob_def = next(
        (m for m in _load_world_data().get("mobs", []) if m["key"] == mob_key),
        None,
    )
    if not mob_def or "loot_table" not in mob_def:
        return []

    dropped = _resolve_loot_drops(mob_def["loot_table"])

    if dropped and caller.location:
        floor_items = list(caller.location.db.floor_items or [])
        floor_items.extend(dropped)
        caller.location.db.floor_items = floor_items

    return dropped


def _award_mob_credits(caller, mob_key: str) -> int:
    """Roll and award a credit drop for a mob kill.

    Looks up the mob's ``credit_drop`` range in WORLD_DATA and awards a random
    amount within that range to the caller's ledger.  Returns the amount
    awarded (0 if the mob has no credit_drop defined).
    """
    mob_def = next(
        (m for m in _load_world_data().get("mobs", []) if m["key"] == mob_key),
        None,
    )
    if not mob_def or "credit_drop" not in mob_def:
        return 0
    amount = _resolve_credit_drop(mob_def["credit_drop"])
    ledger = _get_or_init_ledger(caller)
    ledger["credits"] = int(ledger.get("credits", 0)) + amount
    caller.db.ledger = ledger
    return amount


# ---------------------------------------------------------------------------
# Mob respawn helpers (shared by combat, PSI, and admin commands)
# ---------------------------------------------------------------------------

RESPAWN_DELAY = 120  # seconds - fallback if mob has no respawn_time attribute


def _respawn_mob(mob_id: int) -> None:
    """Called by delay() after respawn time; restores mob to its spawn room.

    Skips if a mob with the same key already occupies the target room (e.g.
    because the server was restarted and the mob was re-seeded by bootstrap).
    """
    mob = _find_object_by_id(mob_id)
    if not mob:
        return
    spawn_room_key = mob.db.spawn_room_key
    if not spawn_room_key:
        return
    rooms = search_object(spawn_room_key, exact=True)
    if not rooms:
        return
    target_room = rooms[0]

    # Duplicate guard - skip if a mob with the same key is already present.
    duplicate = any(
        obj.key == mob.key
        and hasattr(obj, "db")
        and obj.db.actor_type == "mob"
        and obj.id != mob_id
        for obj in target_room.contents
    )
    if duplicate:
        return

    mob.db.hp = mob.db.hp_max or 40
    mob.db.shield_integrity = mob.db.shield_max or 20
    mob.db.mob_stamina = 80
    mob.location = target_room
    for obj in target_room.contents:
        if obj.has_account:
            obj.msg(f"|y{_pretty_name(mob.key)} materializes from the shadows.|n")


def repop_dead_mobs() -> int:
    """Scan all mob objects and schedule a respawn for any that are not in a room.

    Should be called at server start-up after the world has been built.

    Returns the number of mobs queued for respawn.
    """
    from evennia import utils as ev_utils

    count = 0
    for obj in search_object("", global_search=True):
        if not (hasattr(obj, "db") and obj.db.actor_type == "mob"):
            continue
        if obj.location is not None:
            continue  # alive and in a room
        delay = int(obj.db.respawn_time or RESPAWN_DELAY)
        ev_utils.delay(delay, _respawn_mob, obj.id)
        count += 1
    return count


# ---------------------------------------------------------------------------
# Shared deferred-handle registries
# (cancellable sleep/setup delays keyed by caller.id)
# ---------------------------------------------------------------------------

# Maps caller_id -> deferred handle for the 2-second pre-sleep setup delay.
_SETUP_DEFERREDS: dict = {}

# Maps caller_id -> deferred handle for the full sleep recovery delay.
_SLEEP_DEFERREDS: dict = {}
