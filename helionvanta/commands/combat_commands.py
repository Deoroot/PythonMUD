"""Combat engine and combat/rest commands.

Contains the full real-time auto-combat loop, passive regen ticker, sleep/wake
system, and the player-facing commands CmdAttack, CmdKick, CmdSleep, CmdWake.
"""

from __future__ import annotations

import random
import time

from evennia import Command, TICKER_HANDLER, search_object, utils

from commands.cmd_utils import (
    _ensure_project_root_on_path,
    _pretty_name,
    _find_object_by_id,
    _load_world_data,
    _get_item_data,
    _maybe_grow_skill,
    _check_level_up,
    _get_background_perks,
    _update_kill_objectives,
    _update_location_objectives,
    _drop_mob_loot,
    _award_mob_credits,
    _get_guild_skill_bonuses,
    _damage_bar,
    _hit_verb,
    _mob_health_label,
    _format_prompt,
    _send_prompt,
    RESPAWN_DELAY,
    _respawn_mob,
    _SETUP_DEFERREDS,
    _SLEEP_DEFERREDS,
)

_ensure_project_root_on_path()

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

COMBAT_TICK_INTERVAL = 3
REGEN_TICK_INTERVAL = 5


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _combat_idstring(caller) -> str:
    return f"combat:{caller.id}"


def _regen_idstring(caller) -> str:
    return f"regen:{caller.id}"


def _ensure_regen_ticker(caller) -> None:
    """Register (or re-register) the passive regen ticker for *caller*.

    TICKER_HANDLER.add() is idempotent — calling it with the same idstring
    simply refreshes the existing entry — so we no longer rely on a DB flag
    that can get stuck True while the actual ticker is dead (e.g. after an
    exception in _regen_tick or an unexpected server event).
    """
    idstring = _regen_idstring(caller)
    TICKER_HANDLER.add(
        REGEN_TICK_INTERVAL,
        _regen_tick,
        idstring=idstring,
        persistent=True,
        caller_id=caller.id,
    )


def _is_at_full_resources(caller) -> bool:
    hp = caller.db.hp or 0
    hp_max = caller.db.hp_max or 100
    stamina = caller.db.stamina or 0
    stamina_max = caller.db.stamina_max or 100
    focus = caller.db.focus or 0
    focus_max = caller.db.focus_max or 50
    shield = caller.db.shield_integrity or 0
    shield_max = caller.db.shield_max or 100
    psi = caller.db.psi or 0
    psi_max = caller.db.psi_max or 60
    return (hp >= hp_max and stamina >= stamina_max and focus >= focus_max
            and shield >= shield_max and psi >= psi_max)


def _regen_tick(caller_id: int):
    """Passive background regeneration — always ticking at a slow rate.

    Sleep/rest recovery is handled as a lump-sum in _wake_up().
    CON scales HP regen; MIND scales PSI regen.
    """
    caller = _find_object_by_id(caller_id)
    if not caller:
        return

    session = caller.db.combat_session or {}
    target_id = session.get("target_id")
    in_combat = False
    if target_id:
        # Validate the target still exists and is in the same room.
        mob = _find_object_by_id(int(target_id))
        if mob and mob.location and mob.location == caller.location:
            in_combat = True
        else:
            # Stale session — target is gone (dead, despawned, or different room).
            # Clear it so regen is no longer suppressed.
            caller.db.combat_session = None

    hp = caller.db.hp or 0
    hp_max = caller.db.hp_max or 100
    stamina = caller.db.stamina or 0
    stamina_max = caller.db.stamina_max or 100
    focus = caller.db.focus or 0
    focus_max = caller.db.focus_max or 50
    shield = caller.db.shield_integrity or 0
    shield_max = caller.db.shield_max or 100
    psi = caller.db.psi or 0
    psi_max = caller.db.psi_max or 60

    # Guild skill passives can extend effective stamina/PSI caps.
    _regen_guild = _get_guild_skill_bonuses(caller)
    stamina_max += _regen_guild.get("stamina_max", 0)
    psi_max += _regen_guild.get("psi_max", 0)

    attrs = caller.db.attrs or {}
    con = attrs.get("con", 10)
    mind = attrs.get("mind", 10)
    dex = attrs.get("dex", 10)

    if in_combat:
        hp_gain, stamina_gain, focus_gain, shield_gain, psi_gain = 0, 1, 1, 0, 0
    else:
        hp_gain = 1 + max(0, (con - 10) // 5)       # base 1; +1 per 5 CON above 10
        stamina_gain = 3 + max(0, (dex - 10) // 4)  # base 3; +1 per 4 DEX above 10
        focus_gain = 2
        shield_gain = 1 + max(0, (mind - 10) // 5)  # base 1; +1 per 5 MIND above 10
        psi_gain = 2 + max(0, (mind - 10) // 5)     # base 2; +1 per 5 MIND above 10

    caller.db.hp = min(hp_max, hp + hp_gain)
    caller.db.stamina = min(stamina_max, stamina + stamina_gain)
    caller.db.focus = min(focus_max, focus + focus_gain)
    caller.db.shield_integrity = min(shield_max, shield + shield_gain)
    caller.db.psi = min(psi_max, psi + psi_gain)

    # Show compact prompt when recovering out-of-combat so the player sees
    # their resources ticking up without having to type 'score'.
    if not in_combat and not _is_at_full_resources(caller):
        _send_prompt(caller)


def _begin_sleep(caller_id: int) -> None:
    """Called 2s after CmdSleep — begins the actual rest timer.

    Cancelled if combat starts or the player types 'wake' during setup.
    """
    _SETUP_DEFERREDS.pop(caller_id, None)
    caller = _find_object_by_id(caller_id)
    if not caller:
        return
    # Abort if something cancelled sleep during the setup delay.
    if not caller.db.sleeping_pending:
        return
    caller.db.sleeping_pending = False
    # Double-check: not in combat.
    session = caller.db.combat_session or {}
    if session.get("target_id"):
        caller.db.sleeping = False
        caller.msg("|rCombat prevents you from resting.|n")
        return
    caller.db.sleeping = True
    skills = caller.db.skills or {}
    attrs = caller.db.attrs or {}
    camping = skills.get("camping", 0)
    con = attrs.get("con", 10)
    mind = attrs.get("mind", 10)
    hp_restore = 20 + camping // 2 + max(0, (con - 10) // 2)
    stamina_restore = 30 + camping // 2
    shield_restore = 15 + camping // 2
    from mudgame.systems.psi import resolve_sleep_psi_restore
    _, psi_restore = resolve_sleep_psi_restore(
        psi=0, psi_max=9999, mind=mind, partial=False
    )
    sleep_dur = _get_background_perks(caller)["sleep_duration"]
    caller.msg(
        f"|gYou find a quiet spot and settle in...|n\n"
        f"Resting for {sleep_dur} seconds. Type |wwake|n to rise early.\n"
        f"Expected recovery: |g+~{hp_restore} HP  +~{stamina_restore} Stamina"
        f"  +~{shield_restore} Shield  |c+~{psi_restore} PSI|n"
    )
    deferred = utils.delay(sleep_dur, _wake_up, caller.id)
    _SLEEP_DEFERREDS[caller.id] = deferred


def _wake_up(caller_id: int, partial: bool = False) -> None:
    """Apply lump-sum recovery when sleep ends (natural or early wake).

    Args:
        caller_id: DB id of the sleeping character.
        partial:   True when the player woke early (half recovery).
    """
    _SLEEP_DEFERREDS.pop(caller_id, None)
    caller = _find_object_by_id(caller_id)
    if not caller or not caller.db.sleeping:
        return

    caller.db.sleeping = False

    skills = caller.db.skills or {}
    attrs = caller.db.attrs or {}
    camping = skills.get("camping", 0)
    con = attrs.get("con", 10)
    mind = attrs.get("mind", 10)

    hp_restore = 20 + camping // 2 + max(0, (con - 10) // 2)
    stamina_restore = 30 + camping // 2
    shield_restore = 15 + camping // 2

    if partial:
        hp_restore //= 2
        stamina_restore //= 2
        shield_restore //= 2

    hp = caller.db.hp or 0
    hp_max = caller.db.hp_max or 100
    stamina = caller.db.stamina or 0
    stamina_max = caller.db.stamina_max or 100
    shield = caller.db.shield_integrity or 0
    shield_max = caller.db.shield_max or 100
    psi = caller.db.psi or 0
    psi_max = caller.db.psi_max or 60

    # Guild skill passives extend effective stamina/PSI caps during rest.
    _sleep_guild = _get_guild_skill_bonuses(caller)
    stamina_max += _sleep_guild.get("stamina_max", 0)
    psi_max += _sleep_guild.get("psi_max", 0)
    new_psi, psi_gain = resolve_sleep_psi_restore(
        psi=psi, psi_max=psi_max, mind=mind, partial=partial
    )

    new_hp = min(hp_max, hp + hp_restore)
    new_stamina = min(stamina_max, stamina + stamina_restore)
    new_shield = min(shield_max, shield + shield_restore)

    caller.db.hp = new_hp
    caller.db.stamina = new_stamina
    caller.db.shield_integrity = new_shield
    caller.db.psi = new_psi

    hp_gain = new_hp - hp
    stamina_gain = new_stamina - stamina
    shield_gain = new_shield - shield

    if partial:
        caller.msg("|yYou wake up early — rest was incomplete.|n")
    else:
        caller.msg("|gYou wake feeling refreshed.|n")

    gain_parts = []
    if hp_gain > 0:
        gain_parts.append(f"|g+{hp_gain} HP|n")
    if stamina_gain > 0:
        gain_parts.append(f"|g+{stamina_gain} Stamina|n")
    if shield_gain > 0:
        gain_parts.append(f"|g+{shield_gain} Shield|n")
    if psi_gain > 0:
        gain_parts.append(f"|c+{psi_gain} PSI|n")
    caller.msg("  " + ("  ".join(gain_parts) if gain_parts else "Resources were already full."))

    # Camping skill grows by use on a full sleep cycle (not partial).
    if not partial:
        _maybe_grow_skill(caller, "camping")
        # Stamp camping cooldown: base 60s, reduced by CON (min 30s).
        _con = (caller.db.attrs or {}).get("con", 10)
        cooldown = max(30, 60 - max(0, (_con - 10) * 3))
        caller.db.camping_cooldown_until = time.time() + cooldown


def _end_combat_session(caller, reason: str | None = None, notify: bool = True) -> None:
    idstring = _combat_idstring(caller)
    try:
        TICKER_HANDLER.remove(COMBAT_TICK_INTERVAL, _combat_tick, idstring=idstring)
    except Exception:
        pass
    caller.db.combat_session = None
    # Discard any active PSI ward — it must not carry over to a new fight.
    caller.db.psi_ward = 0
    # Guarantee the regen ticker is running now that combat is over.
    # This is a no-op if it was already started, but acts as a safety net
    # in case the ticker was somehow lost (e.g. after a reload mid-combat).
    _ensure_regen_ticker(caller)
    if reason and notify:
        caller.msg(reason)


def _format_exchange_line(attacker_name: str, defender_name: str, action: str, result, is_player_attack: bool = True) -> str:
    note = result.note

    if note == "insufficient_stamina":
        color = "|y" if is_player_attack else "|Y"
        return f"{color}{attacker_name} tries to {action} but is exhausted.|n"

    if note == "miss" or note.startswith("technique_miss:"):
        color = "|w" if is_player_attack else "|g"
        return f"{color}{attacker_name} swings at {defender_name} but misses.|n"

    if note == "avoided" or note.startswith("technique_avoided:"):
        color = "|g" if is_player_attack else "|w"
        return f"{color}{defender_name} sidesteps {attacker_name}'s {action}. [AVOID]|n"

    if note == "dodged" or note.startswith("technique_dodged:"):
        color = "|g" if is_player_attack else "|c"
        return f"{color}{defender_name} dodges {attacker_name}'s {action}. [|cDODGE|n{color}]|n"

    total_dmg = result.shield_damage + result.hp_damage
    verb = _hit_verb(total_dmg)
    bar = _damage_bar(total_dmg)

    tags = []
    if note.startswith("parried") or note.startswith("technique_parried:"):
        tags.append("|cPARRY|n")
    if note.startswith("technique_"):
        _tn = note.split(":")[1].upper() if ":" in note else ""
        if _tn:
            tags.append(f"|m{_tn}|n")
    if note.startswith("technique_pierce:"):
        tags.append("|yPIERCE|n")
    if "vs_dodge" in note:
        tags.append("|yDODGE|n")
    if "vs_parry" in note:
        tags.append("|yPARRY|n")
    if "vs_guard" in note:
        tags.append("|YGUARD|n")
    if "shield_broken" in note or note == "shield_broken":
        tags.append("|rSHIELD BREAK|n")
    if "feint_bypass" in note:
        tags.append("|mFEINT|n")

    tag_text = f" [{', '.join(tags)}]" if tags else ""

    # Color: green when player hits mob, red/yellow when mob hits player
    if is_player_attack:
        line_color = "|g" if total_dmg > 0 else "|w"
    else:
        line_color = "|r" if total_dmg > 8 else "|Y" if total_dmg > 0 else "|w"

    return f"{line_color}{bar} {attacker_name} {verb} {defender_name}.{tag_text}|n"


def _run_combat_round(caller, mob):
    _ensure_project_root_on_path()
    from mudgame.contracts import CharacterStats
    from mudgame.systems.combat import (
        OFFHAND_HIT_PENALTY, UNARMED_BONUS,
        CombatEntity, apply_hit, resolve_attack_passive,
    )
    from mudgame.systems.status_effects import (
        tick_effects, is_stunned, defense_penalty as _def_penalty, apply_effect,
    )

    equipped = caller.db.equipped or {} if hasattr(caller, "db") else {}
    weapon_key  = equipped.get("main_hand") or "training_vibroblade"
    offhand_key = equipped.get("off_hand")

    weapon_item  = _get_item_data(weapon_key)
    offhand_item = _get_item_data(offhand_key) if offhand_key else None

    # Derive combat style from equipped items.
    two_handed      = bool(weapon_item and weapon_item.get("two_handed"))
    offhand_weapon  = bool(offhand_item and offhand_item.get("weapon_type"))
    offhand_shield  = bool(offhand_item and offhand_item.get("shield_bonus"))

    if two_handed:
        style = "two_hand"
    elif offhand_shield:
        style = "shield"
    else:
        # Off_hand is either a weapon or bare fist — always attacks.
        style = "dual"

    # --- Status effects: tick, drain HP, compute defense penalties -----------
    # Process mob effects first so HP drain is reflected in mob_stats below.
    mob_effects_pre = dict(mob.db.status_effects or {})
    mob_is_stunned = is_stunned(mob_effects_pre)
    mob_def_pen = _def_penalty(mob_effects_pre)
    mob_effects_post, mob_hp_drain, mob_effect_msgs = tick_effects(mob_effects_pre, mob.db.hp or 0)
    if mob_hp_drain > 0:
        mob.db.hp = max(0, (mob.db.hp or 0) - mob_hp_drain)
    mob.db.status_effects = mob_effects_post

    player_effects_pre = dict(caller.db.status_effects or {})
    player_def_pen = _def_penalty(player_effects_pre)
    player_effects_post, player_hp_drain, player_effect_msgs = tick_effects(player_effects_pre, caller.db.hp or 0)
    if player_hp_drain > 0:
        caller.db.hp = max(0, (caller.db.hp or 0) - player_hp_drain)
    caller.db.status_effects = player_effects_post

    if hasattr(caller, "get_stats"):
        player_stats = caller.get_stats()
        player_stats.off_balance = player_effects_pre.get("off_balance", 0) > 0
        skills = caller.db.skills or {}
        # Main-hand damage bonus.
        player_stats.weapon_damage_bonus = weapon_item.get("damage_bonus", 0) if weapon_item else 0
        # Two-handed weapon gets a flat +6 bonus on top of its own damage_bonus.
        if style == "two_hand":
            player_stats.weapon_damage_bonus += 6
        # Shield in off_hand boosts parry window.
        if style == "shield":
            player_stats.shield_parry_bonus = 15
        # Weapon-type specialisation — look up the active type's skill.
        active_weapon_type = weapon_item.get("weapon_type", "") if weapon_item else ""
        active_damage_type = "ranged" if active_weapon_type == "ranged" else "melee"
        player_stats.weapon_type_skill = skills.get(active_weapon_type, 0)
        # Weakened status effect reduces effective dodge/parry this round.
        player_stats.skill_dodge = max(0, player_stats.skill_dodge - player_def_pen)
        player_stats.skill_parry = max(0, player_stats.skill_parry - player_def_pen)
        # Physical damage reduction: sum phys_reduction from all equipped armor slots.
        _armor_slots = ("head", "torso", "legs", "feet")
        player_stats.phys_reduction = sum(
            _get_item_data(equipped.get(slot, "") or "").get("phys_reduction", 0)
            for slot in _armor_slots
            if equipped.get(slot)
        )
        # --- Attribute wiring -----------------------------------------------
        # STR → melee weapon damage bonus (+1 per 3 STR above 10).
        # DEX → accuracy (+1 effective melee per 5 DEX above 10) and evasion
        #        (+1 effective dodge per 4 DEX above 10).
        # MIND → effective focus (+2 per MIND above 10); feeds into passive defense.
        # PER → ranged hit chance only (+1 skill_melee per 3 PER above 10 when ranged).
        # STR → parry (+1 per 5 STR above 10).
        _attrs = caller.db.attrs or {}
        _str = _attrs.get("str", 10)
        _dex = _attrs.get("dex", 10)
        _luck = _attrs.get("luck", 10)
        _mind = _attrs.get("mind", 10)
        _per = _attrs.get("per", 10)
        player_stats.weapon_damage_bonus += max(0, (_str - 10) // 3)
        player_stats.skill_melee = min(100, player_stats.skill_melee + max(0, (_dex - 10) // 5))
        player_stats.skill_dodge = min(100, player_stats.skill_dodge + max(0, (_dex - 10) // 4))
        player_stats.skill_parry = min(100, player_stats.skill_parry + max(0, (_str - 10) // 5))
        player_stats.focus = min(100, player_stats.focus + max(0, (_mind - 10) * 2))
        if active_damage_type == "ranged":
            player_stats.skill_melee = min(100, player_stats.skill_melee + max(0, (_per - 10) // 3))
        # --- Guild passive bonuses ------------------------------------------
        _guild_bonuses = _get_guild_skill_bonuses(caller)
        player_stats.weapon_damage_bonus += _guild_bonuses["weapon_damage"]
        player_stats.phys_reduction += _guild_bonuses["phys_reduction"]
    else:
        player_stats = CharacterStats()
        active_weapon_type = ""
        active_damage_type = "melee"
        _luck = 10   # default when caller has no db attrs
        _guild_bonuses = {"phys_reduction": 0, "weapon_damage": 0, "crit_chance": 0.0, "crit_damage": 0, "psi_heal_bonus": 0, "stamina_max": 0, "psi_max": 0}

    player_entity = CombatEntity(name=caller.name, stats=player_stats)

    # Load mob skills from world_data if available, fall back to tier defaults.
    mob_data = next(
        (m for m in _load_world_data().get("mobs", []) if m["key"] == mob.key),
        {},
    )
    if "skills" in mob_data:
        mob_skills = mob_data["skills"]
    else:
        from mudgame.systems.mobs import stats_from_level as _stats_from_level
        _mob_level = mob_data.get("level", 1)
        _mob_derived = _stats_from_level(_mob_level)
        mob_skills = {
            "melee": _mob_derived["melee"],
            "dodge": _mob_derived["dodge"],
            "parry": _mob_derived["parry"],
        }
    mob_stats = CharacterStats(
        hp=mob.db.hp or 40,
        stamina=mob.db.mob_stamina or 80,
        focus=30,
        shield_integrity=mob.db.shield_integrity or 0,
        equipped_weapon=mob.db.equipped_weapon or "claws",
        skill_melee=mob_skills.get("melee", 15),
        skill_dodge=max(0, mob_skills.get("dodge", 8) - mob_def_pen),
        skill_parry=max(0, mob_skills.get("parry", 5) - mob_def_pen),
        off_balance=mob_effects_pre.get("off_balance", 0) > 0,
    )
    mob_entity = CombatEntity(name=_pretty_name(mob.key), stats=mob_stats)

    session = caller.db.combat_session or {"round": 0}
    round_no = int(session.get("round", 0)) + 1
    session["round"] = round_no
    # Consume the ambush_round flag (set by CmdAmbush) — mob skips round 1.
    _ambush_opening = bool(session.pop("ambush_round", False))
    caller.db.combat_session = session

    player_actions = ["attack", "attack", "heavy", "feint"]
    mob_actions = ["attack", "attack", "heavy", "feint"]

    sep = "|w" + "*" * 20 + f" Round {round_no} " + "*" * 20 + "|n"
    lines = [sep]

    # --- Status effect messages (bleed / stun notifications) ----------------
    for _fx_msg in mob_effect_msgs:
        if _fx_msg.startswith("bleed:"):
            _fx_amt = _fx_msg.split(":")[1]
            lines.append(f"|r{_pretty_name(mob.key)} bleeds — {_fx_amt} damage seeps through.|n")
        elif _fx_msg == "stun:active":
            lines.append(f"|y{_pretty_name(mob.key)} staggers, still reeling.|n")

    for _fx_msg in player_effect_msgs:
        if _fx_msg.startswith("bleed:"):
            _fx_amt = _fx_msg.split(":")[1]
            lines.append(f"|rYou bleed — {_fx_amt} damage seeps through your armor.|n")
        elif _fx_msg == "stun:active":
            lines.append(f"|yYou stagger, still reeling. [STUNNED]|n")

    # --- Technique queue: decrement wind-up and fire if ready ---------------
    _queued = caller.db.queued_technique  # {"name": ..., "ticks_remaining": N}
    _technique_fires = False
    _technique_name = None
    if _queued and isinstance(_queued, dict):
        _tr = _queued.get("ticks_remaining", 0) - 1
        _technique_name = _queued.get("name")
        if _tr <= 0:
            _technique_fires = True
            caller.db.queued_technique = None
        else:
            _queued["ticks_remaining"] = _tr
            caller.db.queued_technique = _queued

    if _technique_fires and _technique_name:
        if _technique_name == "sunder_strike":
            # --- Guild technique: Sunder Strike ---
            from mudgame.systems.combat import CombatResult, _clamp_non_negative
            p_action = "Sunder Strike"
            _anni_cost = 40
            if player_entity.stats.stamina < _anni_cost:
                result = CombatResult(
                    attacker=player_entity.name, defender=mob_entity.name,
                    action="attack", shield_damage=0, hp_damage=0,
                    stamina_spent=0, note="insufficient_stamina",
                )
            else:
                player_entity.stats.stamina = _clamp_non_negative(player_entity.stats.stamina - _anni_cost)
                # 1.5× weapon damage + 10 flat, ignores parry (direct hit).
                _anni_raw = max(1, int(player_entity.stats.weapon_damage_bonus * 1.5) + 10)
                _sh, _hp, _ = apply_hit(mob_entity, raw_damage=_anni_raw, damage_type="melee")
                result = CombatResult(
                    attacker=player_entity.name, defender=mob_entity.name,
                    action="attack", shield_damage=_sh, hp_damage=_hp,
                    stamina_spent=_anni_cost, note="technique_hit:sunder_strike",
                )
            _tech_effects = []
            hit_landed = result.note not in ("insufficient_stamina",)
        elif _technique_name == "warlord_strike":
            # --- Guild technique: Warlord Strike (Iron Covenant rank 15) ---
            from mudgame.systems.combat import CombatResult, _clamp_non_negative
            p_action = "Warlord Strike"
            _war_cost = 55
            if player_entity.stats.stamina < _war_cost:
                result = CombatResult(
                    attacker=player_entity.name, defender=mob_entity.name,
                    action="attack", shield_damage=0, hp_damage=0,
                    stamina_spent=0, note="insufficient_stamina",
                )
            else:
                player_entity.stats.stamina = _clamp_non_negative(player_entity.stats.stamina - _war_cost)
                # 2.0× weapon damage + 20 flat.
                # Bypasses parry (not subject to parry resolution) and
                # phys_reduction (armor ignored); shield still absorbs normally.
                _war_raw = max(1, int(player_entity.stats.weapon_damage_bonus * 2.0) + 20)
                _mob_sh = mob_entity.stats.shield_integrity
                if _mob_sh <= 0:
                    _sh, _hp = 0, _war_raw
                    mob_entity.stats.hp = _clamp_non_negative(mob_entity.stats.hp - _war_raw)
                else:
                    _sh = max(1, int(_war_raw * 0.75))
                    _hp = max(0, _war_raw - _mob_sh)
                    mob_entity.stats.shield_integrity = _clamp_non_negative(_mob_sh - _sh)
                    mob_entity.stats.hp = _clamp_non_negative(mob_entity.stats.hp - _hp)
                result = CombatResult(
                    attacker=player_entity.name, defender=mob_entity.name,
                    action="attack", shield_damage=_sh, hp_damage=_hp,
                    stamina_spent=_war_cost, note="technique_hit:warlord_strike",
                )
            _tech_effects = []
            hit_landed = result.note not in ("insufficient_stamina",)
        else:
            from mudgame.systems.techniques import TECHNIQUE_DEFS, resolve_technique
            _tech_defn = TECHNIQUE_DEFS.get(_technique_name, {})
            p_action = _tech_defn.get("name", _technique_name)
            result, _tech_effects = resolve_technique(player_entity, mob_entity, _technique_name)
            # Apply returned status effects to the mob.
            _mob_fx = dict(mob.db.status_effects or {})
            for _eff_name, _eff_ticks in _tech_effects:
                _mob_fx = apply_effect(_mob_fx, _eff_name, _eff_ticks)
            mob.db.status_effects = _mob_fx
            _TECH_MISS_PREFIXES = ("technique_miss:", "technique_avoided:", "technique_dodged:")
            _TECH_MISS_EXACT = {"insufficient_stamina", "unknown_technique"}
            hit_landed = (
                result.note not in _TECH_MISS_EXACT
                and not any(result.note.startswith(_p) for _p in _TECH_MISS_PREFIXES)
            )
    else:
        p_action = random.choice(player_actions)
        result = resolve_attack_passive(player_entity, mob_entity, p_action, damage_type=active_damage_type)
        hit_landed = result.note not in ("miss", "avoided", "dodged", "insufficient_stamina")

    # --- Weapon-type post-processing (main hand) ----------------------------
    # Bludgeons: landed hits deal bonus shield damage based on skill level.
    if hit_landed and active_weapon_type == "bludgeons":
        bludgeon_bonus = max(1, player_stats.weapon_type_skill // 15)
        extra_sh, _, _ = apply_hit(mob_entity, raw_damage=bludgeon_bonus, damage_type="melee")
        result.shield_damage += extra_sh

    # Polearms: bonus damage on round 1 (first-strike advantage before enemy closes in).
    if hit_landed and active_weapon_type == "polearms" and round_no == 1:
        polearm_bonus = max(2, player_stats.weapon_type_skill // 10)
        extra_sh, extra_hp, _ = apply_hit(mob_entity, raw_damage=polearm_bonus, damage_type="melee")
        result.shield_damage += extra_sh
        result.hp_damage += extra_hp

    # Weakness bonus: +25% extra damage when attacking a mob's weak weapon type.
    _weakness_triggered = False
    _mob_weak_to = mob_data.get("weak_to", "")
    if hit_landed and _mob_weak_to and active_weapon_type == _mob_weak_to:
        weakness_bonus = max(1, (result.shield_damage + result.hp_damage) // 4)
        extra_sh, extra_hp, _ = apply_hit(mob_entity, raw_damage=weakness_bonus, damage_type="melee")
        result.shield_damage += extra_sh
        result.hp_damage += extra_hp
        _weakness_triggered = True

    # Clan Initiate background: +25% damage vs Glass Stalkers.
    _stalker_bonus_triggered = False
    _bg_perks = _get_background_perks(caller)
    if hit_landed and mob.key == "glass_stalker" and _bg_perks["stalker_damage_bonus"] > 0:
        stalker_bonus = max(1, int((result.shield_damage + result.hp_damage) * _bg_perks["stalker_damage_bonus"]))
        extra_sh, extra_hp, _ = apply_hit(mob_entity, raw_damage=stalker_bonus, damage_type="melee")
        result.shield_damage += extra_sh
        result.hp_damage += extra_hp
        _stalker_bonus_triggered = True

    critical = False
    if hit_landed:
        # LUCK → crit chance: base 18% + 1% per LUCK above 10 (max ~28% at LUCK 20).
        # find_weakness guild skill adds additional crit chance.
        _crit_chance = 0.18 + max(0, _luck - 10) * 0.01 + _guild_bonuses["crit_chance"]
        if random.random() < _crit_chance:
            _crit_raw = 8 + _guild_bonuses["crit_damage"]
            extra_sh, extra_hp, _ = apply_hit(mob_entity, raw_damage=_crit_raw, damage_type=active_damage_type)
            result.shield_damage += extra_sh
            result.hp_damage += extra_hp
            critical = True

    p_line = _format_exchange_line("You", _pretty_name(mob.key), p_action, result, is_player_attack=True)
    if critical:
        p_line += " |r[CRITICAL HIT!]|n"
    if _weakness_triggered:
        p_line += f" |m[WEAKNESS: {_mob_weak_to}]|n"
    if _stalker_bonus_triggered:
        p_line += " |y[STALKER BANE]|n"
    lines.append(p_line)

    # Skill growth: melee and weapon-type skill improve on a successful hit.
    if hit_landed:
        _maybe_grow_skill(caller, "melee")
        if active_weapon_type:
            _maybe_grow_skill(caller, active_weapon_type)

    # --- Off-hand attack (dual style only) -----------------------------------
    # Off_hand fires whenever it's not a shield and not a two-hander.
    # If nothing is equipped it uses unarmed stats (UNARMED_BONUS already
    # baked into weapon_damage_bonus via _get_slot_damage_bonus below).
    if style == "dual" and mob_entity.stats.hp > 0:
        # Build a temporary attacker entity with the off-hand damage bonus.
        oh_bonus = offhand_item.get("damage_bonus", 0) if offhand_item else UNARMED_BONUS
        oh_stats_copy = CharacterStats(
            hp=player_entity.stats.hp,
            stamina=player_entity.stats.stamina,
            focus=player_entity.stats.focus,
            shield_integrity=player_entity.stats.shield_integrity,
            equipped_weapon=offhand_key or "unarmed",
            weapon_damage_bonus=oh_bonus,
            skill_melee=player_entity.stats.skill_melee,
            skill_dodge=player_entity.stats.skill_dodge,
            skill_parry=player_entity.stats.skill_parry,
        )
        oh_entity = CombatEntity(name=caller.name, stats=oh_stats_copy)
        oh_weapon_type = offhand_item.get("weapon_type", "") if offhand_item else ""
        oh_damage_type = "ranged" if oh_weapon_type == "ranged" else "melee"
        oh_action = random.choice(["attack", "attack", "feint"])
        oh_result = resolve_attack_passive(
            oh_entity, mob_entity, oh_action, damage_type=oh_damage_type, hit_penalty=OFFHAND_HIT_PENALTY
        )
        # Carry stamina consumed by off-hand back to the main player entity.
        player_entity.stats.stamina = oh_entity.stats.stamina

        oh_label = offhand_item["name"] if offhand_item else "unarmed fist"
        oh_line = _format_exchange_line(
            f"Your {oh_label}", _pretty_name(mob.key), oh_action, oh_result, is_player_attack=True
        )
        lines.append(oh_line)

        if oh_result.note not in ("miss", "avoided", "dodged", "insufficient_stamina"):
            _maybe_grow_skill(caller, "melee")

    # --- Mob counter-attack --------------------------------------------------
    if mob_entity.stats.hp > 0 and mob_is_stunned:
        lines.append(f"|y{_pretty_name(mob.key)} is stunned and cannot act this round!|n")
    elif mob_entity.stats.hp > 0 and _ambush_opening:
        lines.append(f"|c{_pretty_name(mob.key)} is caught off-guard and cannot counter-attack!|n")
    elif mob_entity.stats.hp > 0:
        m_action = random.choice(mob_actions)
        counter = resolve_attack_passive(mob_entity, player_entity, m_action)

        mob_critical = False
        if counter.note not in ("miss", "avoided", "dodged", "insufficient_stamina") and random.random() < 0.12:
            extra_sh, extra_hp, _ = apply_hit(player_entity, raw_damage=6, damage_type="melee")
            counter.shield_damage += extra_sh
            counter.hp_damage += extra_hp
            mob_critical = True

        # PSI Ward: absorb incoming HP damage if the player has an active ward.
        _psi_ward = caller.db.psi_ward or 0
        _mob_hit_landed = counter.note not in ("miss", "avoided", "dodged", "insufficient_stamina")
        if _psi_ward > 0 and _mob_hit_landed and counter.hp_damage > 0:
            absorbed = min(_psi_ward, counter.hp_damage)
            counter.hp_damage -= absorbed
            # Also update the player_entity so apply_stats writes the correct hp.
            player_entity.stats.hp = min(player_entity.stats.hp + absorbed, caller.db.hp_max or 100)
            caller.db.psi_ward = 0
            lines.append(f"|cYour PSI barrier absorbs {absorbed} damage!|n")
        elif _psi_ward > 0:
            # Ward dissipates even if not triggered this round.
            caller.db.psi_ward = 0

        m_line = _format_exchange_line(_pretty_name(mob.key), "you", m_action, counter, is_player_attack=False)
        if mob_critical:
            m_line += " |r[CRITICAL!]|n"
        lines.append(m_line)

        # Skill growth: player's dodge or parry improves when they successfully defend.
        if counter.note == "dodged":
            _maybe_grow_skill(caller, "dodge")
        elif counter.note.startswith("parried"):
            _maybe_grow_skill(caller, "parry")

        # Mob on-hit effect: apply to player on any landed hit (including parried).
        _on_hit_effect = mob_data.get("on_hit_effect")
        if _mob_hit_landed and _on_hit_effect:
            _player_fx = dict(caller.db.status_effects or {})
            _player_fx = apply_effect(_player_fx, _on_hit_effect["name"], _on_hit_effect["ticks"])
            caller.db.status_effects = _player_fx
            lines.append(
                f"|r{_pretty_name(mob.key)} inflicts "
                f"|y{_on_hit_effect['name']}|r on you!|n"
            )

    mob.db.hp = mob_entity.stats.hp
    mob.db.shield_integrity = mob_entity.stats.shield_integrity
    mob.db.mob_stamina = mob_entity.stats.stamina
    if hasattr(caller, "apply_stats"):
        caller.apply_stats(player_entity.stats)

    # Mob health status line (BatMUD style)
    mob_hp_max = mob.db.hp_max or 40
    health_label = _mob_health_label(mob_entity.stats.hp, mob_hp_max)
    lines.append(f"|w{_pretty_name(mob.key)}|n is {health_label}.")

    # Compact prompt (BatMUD style) — reads from db (apply_stats was called above).
    lines.append(_format_prompt(caller))

    combat_done = False

    if mob_entity.stats.hp <= 0:
        xp_gain = mob.db.xp or 25
        caller.db.xp = (caller.db.xp or 0) + xp_gain
        mob_display = _pretty_name(mob.key)
        credit_drop = _award_mob_credits(caller, mob.key)
        credit_str = f" |y+{credit_drop}c.|n" if credit_drop else ""
        loot_dropped = _drop_mob_loot(caller, mob.key)
        if loot_dropped:
            item_names = []
            for ik in loot_dropped:
                idata = _get_item_data(ik)
                item_names.append(idata["name"] if idata else _pretty_name(ik))
            loot_str = f"\n|yDropped:|n " + ", ".join(f"|w{n}|n" for n in item_names) + "  (|yget all|n to pick up)"
        else:
            loot_str = ""
        lines.append(f"|r{mob_display} collapses, systems failing.|n |g+{xp_gain} XP.|n{credit_str}{loot_str}")
        level_up_msgs = _check_level_up(caller)
        lines.extend(level_up_msgs)
        _update_kill_objectives(caller, mob.key)
        mob.location = None
        utils.delay(RESPAWN_DELAY, _respawn_mob, mob.id)
        combat_done = True

    if player_entity.stats.hp <= 0:
        lines.append("|rYou have been defeated. You lose consciousness...|n")
        respawn = search_object("helion_gate", exact=True)
        if respawn:
            caller.move_to(respawn[0], quiet=True)
            caller.db.hp = 30
            caller.db.stamina = 50
            caller.db.shield_integrity = 50
            lines.append("You wake up at the Gate Concourse, battered but alive.")
        combat_done = True

    return lines, combat_done


def _combat_tick(caller_id: int):
    caller = _find_object_by_id(caller_id)
    if not caller:
        return

    # Safety: if somehow a sleeping player has a combat session, jolt them awake.
    if caller.db.sleeping or caller.db.sleeping_pending:
        setup_deferred = _SETUP_DEFERREDS.pop(caller.id, None)
        if setup_deferred:
            try:
                setup_deferred.cancel()
            except Exception:
                pass
        deferred = _SLEEP_DEFERREDS.pop(caller.id, None)
        if deferred:
            try:
                deferred.cancel()
            except Exception:
                pass
        caller.db.sleeping = False
        caller.db.sleeping_pending = False
        caller.msg("|rYou are jolted awake by combat!|n")

    session = caller.db.combat_session or {}
    target_id = session.get("target_id")
    if not target_id:
        _end_combat_session(caller, notify=False)
        return

    mob = _find_object_by_id(int(target_id))
    if not mob or not mob.location or caller.location != mob.location:
        _end_combat_session(caller, "|yCombat ended: target lost or left room.|n")
        return

    _update_location_objectives(caller)
    lines, combat_done = _run_combat_round(caller, mob)
    caller.msg("\n".join(lines))

    if combat_done:
        _end_combat_session(caller, notify=False)


def _check_room_ambush(caller) -> None:
    """Check for ambush-capable mobs when a character enters a room.

    Called from Character.at_after_move.  Rolls the player's alertness
    skill against a random threshold:
      - Detection (pass): player is warned and alertness grows.
      - Ambush (fail): mob gets a free opening strike before combat.
    """
    if not caller.location:
        return

    world_data = _load_world_data()
    mob_data_by_key = {m["key"]: m for m in world_data.get("mobs", [])}
    ambush_mobs = [
        obj for obj in caller.location.contents
        if getattr(obj.db, "actor_type", None) == "mob"
        and mob_data_by_key.get(obj.key, {}).get("can_ambush")
        and (obj.db.hp or 0) > 0
    ]
    if not ambush_mobs:
        return

    skills = caller.db.skills or {}
    alertness = skills.get("alertness", 0)

    # Base 20% detection chance + 1% per alertness point (capped at 100%).
    import random as _rng
    detection_chance = min(100, 20 + alertness)
    roll = _rng.randint(1, 100)
    mob = ambush_mobs[0]
    mob_display = _pretty_name(mob.key)

    if roll <= detection_chance:
        # Player detects the lurking threat.
        caller.msg(
            f"|yYou sense movement — a |w{mob_display}|y lurks here. "
            "Use '|wambush <target>|y' for a first-strike advantage.|n"
        )
        _maybe_grow_skill(caller, "alertness")
    else:
        # Mob gets a free opening strike before the player can react.
        _ensure_project_root_on_path()
        from mudgame.contracts import CharacterStats
        from mudgame.systems.combat import CombatEntity, apply_hit, resolve_attack_passive

        caller.msg(
            f"|r{mob_display} strikes from the shadows before you can react! [AMBUSHED]|n"
        )
        mob_data = mob_data_by_key.get(mob.key, {})
        from mudgame.systems.mobs import stats_from_level as _stats_from_level
        _mob_level = mob_data.get("level", 1)
        _mob_derived = _stats_from_level(_mob_level)
        mob_skills_data = mob_data.get("skills", {})
        mob_stats = CharacterStats(
            hp=mob.db.hp or 40,
            stamina=getattr(mob.db, "mob_stamina", None) or 80,
            focus=30,
            shield_integrity=mob.db.shield_integrity or 0,
            equipped_weapon=getattr(mob.db, "equipped_weapon", None) or "claws",
            skill_melee=mob_skills_data.get("melee", _mob_derived.get("melee", 15)),
            skill_dodge=mob_skills_data.get("dodge", _mob_derived.get("dodge", 8)),
            skill_parry=mob_skills_data.get("parry", _mob_derived.get("parry", 5)),
        )
        mob_entity = CombatEntity(name=mob_display, stats=mob_stats)

        if hasattr(caller, "get_stats"):
            player_stats = caller.get_stats()
        else:
            player_stats = CharacterStats()
        player_entity = CombatEntity(name=caller.name, stats=player_stats)

        counter = resolve_attack_passive(mob_entity, player_entity, "attack")
        total_dmg = counter.shield_damage + counter.hp_damage
        if counter.note not in ("miss", "avoided", "dodged") and total_dmg > 0:
            caller.msg(f"|r  {mob_display} hits you for {total_dmg}! [AMBUSH STRIKE]|n")
            if hasattr(caller, "apply_stats"):
                caller.apply_stats(player_entity.stats)
        else:
            caller.msg(f"|y  The ambush strike glances off — you react just in time.|n")
        _send_prompt(caller)


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

class CmdAttack(Command):
    """Attack a hostile mob in your current room.

    Usage:
      attack <target>
      attack stop
      kill <target>
      fight <target>
      k <target>

    Actions resolve in real-time rounds (server tick).
    Shields absorb most of the initial hits. Fight when shields are low.
    """

    key = "attack"
    aliases = ["kill", "fight", "k"]
    help_category = "Combat"

    def func(self):
        _update_location_objectives(self.caller)
        if not self.args:
            self.caller.msg("Usage: attack <target> or attack stop")
            return

        raw = self.args.strip().lower()
        if raw in {"stop", "off", "flee", "disengage"}:
            _end_combat_session(self.caller, "|yYou disengage from combat.|n")
            return

        session = self.caller.db.combat_session or {}
        if session.get("target_id"):
            target_obj = _find_object_by_id(int(session.get("target_id")))
            if target_obj and target_obj.location == self.caller.location:
                self.caller.msg("|yAlready in combat. Use 'attack stop' to disengage.|n")
                return
            _end_combat_session(self.caller, notify=False)

        target_name = raw.replace(" ", "_")
        if not target_name:
            self.caller.msg("Attack what? Usage: attack <target>")
            return

        # Find mob in current room — match against key or pretty display name.
        mob = None
        for obj in self.caller.location.contents:
            if obj.db.actor_type != "mob":
                continue
            obj_key = obj.key.lower()
            obj_pretty = _pretty_name(obj.key).lower()
            if (target_name in obj_key or obj_key in target_name
                    or raw in obj_pretty or obj_pretty in raw):
                mob = obj
                break

        if not mob:
            self.caller.msg(f"No hostile '{raw}' here.")
            return

        if (mob.db.hp or 0) <= 0:
            self.caller.msg(f"The {_pretty_name(mob.key)} is already down.")
            return

        if self.caller.db.sleeping or self.caller.db.sleeping_pending:
            setup_deferred = _SETUP_DEFERREDS.pop(self.caller.id, None)
            if setup_deferred:
                try:
                    setup_deferred.cancel()
                except Exception:
                    pass
            deferred = _SLEEP_DEFERREDS.pop(self.caller.id, None)
            if deferred:
                try:
                    deferred.cancel()
                except Exception:
                    pass
            self.caller.db.sleeping = False
            self.caller.db.sleeping_pending = False
            self.caller.msg("You jolt awake and enter combat stance!")

        self.caller.db.combat_session = {
            "target_id": mob.id,
            "target_key": mob.key,
            "round": 0,
        }

        idstring = _combat_idstring(self.caller)
        TICKER_HANDLER.add(
            COMBAT_TICK_INTERVAL,
            _combat_tick,
            idstring=idstring,
            persistent=True,
            caller_id=self.caller.id,
        )

        self.caller.msg(
            f"|cEngaging {_pretty_name(mob.key)}. Auto-combat tick every {COMBAT_TICK_INTERVAL}s. "
            "Use 'attack stop' to disengage.|n"
        )

        # Run first round immediately for responsiveness.
        _combat_tick(self.caller.id)


class CmdKick(Command):
    """Deliver a powerful kick to your combat target.

    Usage:
      kick

    Costs 8 Stamina. Deals physical damage that bypasses the bioelectric
    shield entirely — pure kinetic force that hits HP directly. Scales
    with STR (+1 damage per 3 STR above 10).

    Leaves the target |coff-balance|n for one combat round: their dodge and
    parry windows are halved, making the next auto-attack hit more reliably.

    Requires an active combat target (use 'attack <mob>' first).
    """

    key = "kick"
    help_category = "Combat"

    _STAMINA_COST = 8

    def func(self):
        _ensure_project_root_on_path()
        caller = self.caller

        session = caller.db.combat_session or {}
        target_id = session.get("target_id")
        if not target_id:
            caller.msg("|yKick requires an active combat target. Use 'attack <mob>' first.|n")
            return

        mob = _find_object_by_id(int(target_id))
        if not mob or not mob.location or caller.location != mob.location:
            _end_combat_session(caller, "|yCombat ended: target lost or left room.|n")
            return

        if (mob.db.hp or 0) <= 0:
            caller.msg(f"The {_pretty_name(mob.key)} is already down.")
            return

        stamina = caller.db.stamina or 0
        if stamina < self._STAMINA_COST:
            caller.msg(
                f"|yNot enough Stamina to kick. "
                f"Kick costs {self._STAMINA_COST} Stamina (you have {stamina}).|n"
            )
            return

        # Deduct stamina.
        caller.db.stamina = max(0, stamina - self._STAMINA_COST)

        # Compute kick damage: 5 base + 1 per 3 STR above 10.
        attrs = caller.db.attrs or {}
        _str = attrs.get("str", 10)
        damage = 5 + max(0, (_str - 10) // 3)

        # Apply damage directly to mob HP (bypasses shield).
        mob_hp_before = mob.db.hp or 0
        mob.db.hp = max(0, mob_hp_before - damage)
        actual_damage = mob_hp_before - mob.db.hp

        # Apply off_balance status for 1 round.
        from mudgame.systems.status_effects import apply_effect
        mob_fx = dict(mob.db.status_effects or {})
        mob_fx = apply_effect(mob_fx, "off_balance", 1)
        mob.db.status_effects = mob_fx

        mob_display = _pretty_name(mob.key)
        mob_hp_max = mob.db.hp_max or 40
        health_label = _mob_health_label(mob.db.hp, mob_hp_max)

        caller.msg(
            f"|wYou drive your boot into {mob_display}.|n  "
            f"|r-{actual_damage} HP|n (shield bypassed)  "
            f"|c[Off-balance x1]|n  "
            f"Stamina: {caller.db.stamina}"
        )
        caller.msg(f"|w{mob_display}|n is {health_label}.")

        if mob.db.hp <= 0:
            xp_gain = mob.db.xp or 25
            caller.db.xp = (caller.db.xp or 0) + xp_gain
            credit_drop = _award_mob_credits(caller, mob.key)
            credit_str = f" |y+{credit_drop}c.|n" if credit_drop else ""
            caller.msg(f"|r{mob_display} collapses.|n |g+{xp_gain} XP.|n{credit_str}")
            level_up_msgs = _check_level_up(caller)
            for msg in level_up_msgs:
                caller.msg(msg)
            _update_kill_objectives(caller, mob.key)
            mob.location = None
            utils.delay(RESPAWN_DELAY, _respawn_mob, mob.id)
            _end_combat_session(caller, notify=False)
        else:
            _send_prompt(caller)


class CmdSleep(Command):
    """Sleep, rest, or camp to recover HP, Stamina, and Shield.

    Usage:
      sleep
      rest
      camp
      meditate

    You settle in for a short rest. After a few seconds you wake refreshed
    with an instant burst of HP, Stamina, and Shield.

    While resting you cannot take any actions. Type 'wake' to rise
    early — you will receive only partial recovery.

    Characters with higher Camping skill recover more per rest.
    """

    key = "sleep"
    aliases = ["rest", "camp", "meditate", "recover", "descansar", "descanzar"]
    help_category = "General"

    def func(self):
        caller = self.caller
        session = caller.db.combat_session or {}
        if session.get("target_id"):
            caller.msg("|rYou cannot rest while in combat.|n")
            return

        if caller.db.sleeping:
            caller.msg("You are already resting.")
            return

        if caller.db.sleeping_pending:
            caller.msg("You are already scanning for a place to rest.")
            return

        # Cooldown check: must wait between rest cycles.
        cooldown_until = caller.db.camping_cooldown_until or 0
        if time.time() < cooldown_until:
            remaining = int(cooldown_until - time.time())
            caller.msg(f"|yYou need to recover before resting again. ({remaining}s remaining)|n")
            return

        skills = caller.db.skills or {}
        attrs = caller.db.attrs or {}
        camping = skills.get("camping", 0)
        con = attrs.get("con", 10)
        mind = attrs.get("mind", 10)
        hp_restore = 20 + camping // 2 + max(0, (con - 10) // 2)
        stamina_restore = 30 + camping // 2
        shield_restore = 15 + camping // 2
        from mudgame.systems.psi import resolve_sleep_psi_restore
        _, psi_restore = resolve_sleep_psi_restore(
            psi=0, psi_max=9999, mind=mind, partial=False
        )

        caller.db.sleeping_pending = True
        caller.msg(
            f"|gYou scan the area for a safe place to rest...|n\n"
            f"Expected recovery: |g+~{hp_restore} HP  +~{stamina_restore} Stamina"
            f"  +~{shield_restore} Shield  |c+~{psi_restore} PSI|n"
        )
        deferred = utils.delay(2, _begin_sleep, caller.id)
        _SETUP_DEFERREDS[caller.id] = deferred


class CmdWake(Command):
    """Wake from rest early.

    Usage:
      wake
      stand

    Waking early gives only partial recovery (half the normal amount).
    For full benefits, let the rest complete naturally.
    """

    key = "wake"
    aliases = ["stand", "getup", "rise"]
    help_category = "General"

    def func(self):
        caller = self.caller

        # Handle cancellation during the 2s setup phase.
        if caller.db.sleeping_pending:
            setup_deferred = _SETUP_DEFERREDS.pop(caller.id, None)
            if setup_deferred:
                try:
                    setup_deferred.cancel()
                except Exception:
                    pass
            caller.db.sleeping_pending = False
            caller.msg("|yYou decide against resting.|n")
            return

        if not caller.db.sleeping:
            caller.msg("You are not resting.")
            return

        deferred = _SLEEP_DEFERREDS.pop(caller.id, None)
        if deferred:
            try:
                deferred.cancel()
            except Exception:
                pass
        _wake_up(caller.id, partial=True)


class CmdAmbush(Command):
    """Launch a surprise first strike against a lurking enemy.

    Usage:
      ambush <target>

    Initiates combat with a preemptive strike. The target cannot
    counter-attack during the opening round, giving you a free hit
    to open the fight. Only works against enemies capable of ambushing
    (Glass Stalkers, Crystal Wraiths, Elder Stalkers, and similar).

    Your Alertness skill grows with each ambush attempt and each
    successful threat detection when entering a room.
    """

    key = "ambush"
    help_category = "Combat"

    def func(self):
        caller = self.caller
        if not self.args:
            caller.msg("Ambush what? Usage: ambush <target>")
            return

        # Block if already in combat.
        session = caller.db.combat_session or {}
        if session.get("target_id"):
            caller.msg("|yAlready in combat. Use 'attack stop' to disengage first.|n")
            return

        raw = self.args.strip().lower()
        target_name = raw.replace(" ", "_")

        world_data = _load_world_data()
        mob_data_by_key = {m["key"]: m for m in world_data.get("mobs", [])}

        # Find an ambushable mob in the room matching the target string.
        mob = None
        for obj in caller.location.contents:
            if getattr(obj.db, "actor_type", None) != "mob":
                continue
            if not mob_data_by_key.get(obj.key, {}).get("can_ambush"):
                continue
            if (obj.db.hp or 0) <= 0:
                continue
            obj_key = obj.key.lower()
            obj_pretty = _pretty_name(obj.key).lower()
            if (target_name in obj_key or obj_key in target_name
                    or raw in obj_pretty or obj_pretty in raw):
                mob = obj
                break

        if not mob:
            caller.msg(
                f"No ambushable target matching '{raw}' here.\n"
                "Ambush only works on enemies flagged as lurking threats."
            )
            return

        if caller.db.sleeping or caller.db.sleeping_pending:
            caller.msg("|rYou can't ambush while resting.|n")
            return

        caller.db.combat_session = {
            "target_id": mob.id,
            "target_key": mob.key,
            "round": 0,
            "ambush_round": True,   # mob skips counter in round 1
        }

        idstring = _combat_idstring(caller)
        TICKER_HANDLER.add(
            COMBAT_TICK_INTERVAL,
            _combat_tick,
            idstring=idstring,
            persistent=True,
            caller_id=caller.id,
        )

        _maybe_grow_skill(caller, "alertness")

        caller.msg(
            f"|cYou launch a surprise attack on {_pretty_name(mob.key)}! "
            "The target cannot counter-attack this round.|n"
        )
        # Fire round 1 immediately.
        _combat_tick(caller.id)
