"""Social, look, movement-alias, status, and scan commands."""

from __future__ import annotations

from evennia import Command

from commands.cmd_utils import (
    _ensure_project_root_on_path,
    _pretty_name,
    _load_world_data,
    _get_item_data,
    _get_or_init_ledger,
    _get_or_init_reputation,
    _rep_tier,
    _get_quest_state,
    _update_location_objectives,
    _is_quest_complete,
    _format_quest_progress,
    _accept_contract,
    _turnin_contract,
    _mob_health_label,
    _send_room_oob,
    _quests,
    SLEEP_DURATION,
    _SETUP_DEFERREDS,
    _SLEEP_DEFERREDS,
)


class CmdScan(Command):
    """Inspect local tactical metadata.

    Usage:
      scan
    """

    key = "scan"
    help_category = "General"

    def func(self):
        _update_location_objectives(self.caller)
        room = self.caller.location
        if not room:
            self.caller.msg("You are nowhere. Sensors fail to calibrate.")
            return

        planet = room.db.planet or "unknown"
        area = room.db.area or "unknown"
        room_type = room.db.room_type or "unknown"
        mobs = [_pretty_name(obj.key) for obj in room.contents if obj.db.actor_type == "mob"]

        per = (self.caller.db.attrs or {}).get("per", 10)

        msg = [
            f"Area scan: {room.db.display_name or room.key}",
            f"- Planet: {planet}",
            f"- Area: {area}",
            f"- Room type: {room_type}",
        ]
        if mobs:
            if per >= 15:
                # Higher PER reveals rough mob health states.
                mob_detail = []
                for obj in room.contents:
                    if obj.db.actor_type != "mob":
                        continue
                    hp = obj.db.hp or 0
                    hp_max = obj.db.hp_max or 40
                    pct = (hp / hp_max * 100) if hp_max else 0
                    health_word = "healthy" if pct >= 70 else "wounded" if pct >= 30 else "critical"
                    mob_detail.append(f"{_pretty_name(obj.key)} [{health_word}]")
                msg.append(f"- Hostiles detected: {', '.join(mob_detail)}")
            else:
                msg.append(f"- Hostiles detected: {', '.join(mobs)}")
        else:
            msg.append("- Hostiles detected: none")
        if per >= 12:
            msg.append(f"- Perception: {per} (enhanced scan active)")
        self.caller.msg("\n".join(msg))


class CmdConsider(Command):
    """Size up a hostile target to gauge your chances in a fight.

    Usage:
      consider <target>
      con <target>

    Gives a qualitative threat assessment comparing your combat experience
    to the target's apparent power. No exact numbers are revealed.
    """

    key = "consider"
    aliases = ["con"]
    help_category = "Combat"

    def func(self):
        caller = self.caller
        if not self.args.strip():
            caller.msg("Consider whom? Usage: consider <target>")
            return

        room = caller.location
        if not room:
            return

        target_name = self.args.strip().lower()
        mob = None
        for obj in room.contents:
            if obj.db.actor_type == "mob" and target_name in obj.key.lower():
                mob = obj
                break

        if not mob:
            caller.msg(f"You don't see '{self.args.strip()}' here to size up.")
            return

        player_level = caller.db.level or 1
        mob_level = mob.db.level or 1
        gap = mob_level - player_level

        if gap >= 5:
            threat = "suicidal \u2014 they would destroy you without breaking a sweat"
        elif gap >= 3:
            threat = "dangerous \u2014 you'd be lucky to survive this fight"
        elif gap >= 1:
            threat = "tough \u2014 they have the advantage over you"
        elif gap == 0:
            threat = "an even match \u2014 this could go either way"
        elif gap >= -2:
            threat = "manageable \u2014 you have the edge"
        else:
            threat = "easy prey \u2014 little real challenge here"

        _ensure_project_root_on_path()
        mob_data = next(
            (m for m in _load_world_data().get("mobs", []) if m["key"] == mob.key),
            {},
        )
        mob_skills = mob_data.get("skills", {})
        mob_melee = mob_skills.get("melee", 15)
        mob_dodge = mob_skills.get("dodge", 8)

        def _mob_adj(v: int) -> str:
            if v < 12:
                return "weak"
            if v < 22:
                return "moderate"
            if v < 35:
                return "strong"
            return "formidable"

        mob_display = _pretty_name(mob.key)
        caller.msg(
            f"You study |w{mob_display}|n carefully...\n"
            f"  Threat assessment: |y{threat}|n.\n"
            f"  Their strikes look |c{_mob_adj(mob_melee)}|n. "
            f"Their footwork reads as |c{_mob_adj(mob_dodge)}|n."
        )


class CmdAppraise(Command):
    """Have a tech-assessor examine an item's hidden qualities.

    Usage:
      appraise <item>

    A tech-assessor NPC must be present in the room. They reveal an item's
    protective or offensive properties using descriptive language \u2014 no raw
    numbers are given. Items must be in your inventory or currently equipped.
    """

    key = "appraise"
    help_category = "General"

    def func(self):
        caller = self.caller
        if not self.args.strip():
            caller.msg("Appraise what? Usage: appraise <item>")
            return

        room = caller.location
        if not room:
            return

        # Check for an appraiser NPC in the room.
        appraiser = None
        for obj in room.contents:
            if obj.db.actor_type == "npc" and obj.db.role == "appraiser":
                appraiser = obj
                break

        if not appraiser:
            caller.msg(
                "There's no tech-assessor here. "
                "Find one in a market district."
            )
            return

        _ensure_project_root_on_path()
        item_arg = self.args.strip().lower()
        ledger = caller.db.ledger or {}
        inventory = ledger.get("inventory", [])
        equipped = caller.db.equipped or {}

        # Search inventory and all equipped slots.
        all_items = list(inventory) + [v for v in equipped.values() if v]
        matched_key = None
        for item_key in all_items:
            item_data = _get_item_data(item_key)
            if not item_data:
                continue
            item_name = item_data.get("name", item_key)
            if item_arg in item_name.lower() or item_arg in item_key.lower():
                matched_key = item_key
                break

        if not matched_key:
            caller.msg(
                f"You don't have '{self.args.strip()}' in your inventory or gear."
            )
            return

        item_data = _get_item_data(matched_key)
        item_name = item_data.get("name", matched_key)
        appraiser_name = _pretty_name(appraiser.key)

        weapon_type    = item_data.get("weapon_type")
        damage_bonus   = item_data.get("damage_bonus", 0)
        phys_reduction = item_data.get("phys_reduction", 0)
        armor_bonus    = item_data.get("armor_bonus", 0)
        shield_bonus   = item_data.get("shield_bonus", 0)
        two_handed     = item_data.get("two_handed", False)

        def _dmg_adj(v: int) -> str:
            if v <= 0: return "standard"
            if v <= 3: return "enhanced"
            if v <= 6: return "strong"
            if v <= 9: return "exceptional"
            return "devastating"

        def _dr_adj(v: int) -> str:
            if v == 0: return "negligible"
            if v == 1: return "light"
            if v <= 3: return "moderate"
            if v <= 5: return "solid"
            return "heavy"

        def _hp_adj(v: int) -> str:
            if v <= 5:  return "minimal"
            if v <= 15: return "modest"
            if v <= 25: return "solid"
            if v <= 40: return "substantial"
            return "impressive"

        def _sh_adj(v: int) -> str:
            if v <= 10: return "modest"
            if v <= 25: return "solid"
            if v <= 40: return "strong"
            return "heavy"

        lines = [f"|w{appraiser_name}|n examines your |w{item_name}|n carefully."]

        if weapon_type:
            th = " Two-handed." if two_handed else ""
            lines.append(
                f"  \"{item_name} \u2014 {weapon_type} weapon. "
                f"Striking power: |c{_dmg_adj(damage_bonus)}|n.{th}\""
            )
        elif phys_reduction > 0 or armor_bonus > 0:
            lines.append(
                f"  \"{item_name} \u2014 armor. "
                f"Impact resistance: |c{_dr_adj(phys_reduction)}|n. "
                f"Protective capacity: |c{_hp_adj(armor_bonus)}|n.\""
            )
        elif shield_bonus > 0:
            lines.append(
                f"  \"{item_name} \u2014 field brace. "
                f"Capacity: |c{_sh_adj(shield_bonus)}|n.\""
            )
        else:
            lines.append(f"  \"{item_name} \u2014 nothing unusual detected.\"")

        caller.msg("\n".join(lines))


class CmdStatus(Command):
    """Display your current combat stats.

    Usage:
      status
      score
      stats
    """

    key = "status"
    aliases = ["score", "stats"]
    help_category = "General"

    def func(self):
        _update_location_objectives(self.caller)
        ledger = _get_or_init_ledger(self.caller)
        inventory = ledger.get("inventory", [])
        inv_text = ", ".join(inventory) if inventory else "none"
        if hasattr(self.caller, "status_string"):
            rep = _get_or_init_reputation(self.caller)
            helion = rep.get("helion_colony", 0)
            vanta = rep.get("vanta_clans", 0)
            soul_xp = self.caller.db.soul_xp or 0
            reincarnations = self.caller.db.reincarnations or 0
            soul_line = ""
            if soul_xp > 0:
                soul_line = (
                    f"\nSoul Pool: |c{soul_xp} XP|n banked "
                    f"(life #{reincarnations} \u2014 use 'claimlevels' to spend)"
                )
            elif reincarnations > 0:
                soul_line = f"\nReincarnations: {reincarnations}"
            self.caller.msg(
                f"{self.caller.status_string()}\n"
                f"Inventory: {inv_text}\n"
                f"Reputation: Helion {helion} ({_rep_tier(helion)}), "
                f"Vanta {vanta} ({_rep_tier(vanta)})"
                f"{soul_line}"
            )
        else:
            self.caller.msg("No status information available.")


class CmdReputation(Command):
    """Show current faction standings.

    Usage:
      rep
      reputation
      factions
    """

    key = "reputation"
    aliases = ["rep", "factions"]
    help_category = "General"

    def func(self):
        rep = _get_or_init_reputation(self.caller)
        helion = int(rep.get("helion_colony", 0))
        vanta = int(rep.get("vanta_clans", 0))
        self.caller.msg(
            "|wFaction Standings|n\n"
            f"  Helion Colony: {helion:>4}  ({_rep_tier(helion)})\n"
            f"  Vanta Clans:   {vanta:>4}  ({_rep_tier(vanta)})"
        )


class CmdLook(Command):
    """Look at the room or a specific target.

    Usage:
      look
      look <target>
      look at <target>
      la <target>
    """

    key = "look"
    aliases = ["la", "l"]
    help_category = "General"

    def func(self):
        caller = self.caller
        args = self.args.strip()
        # Strip leading 'at ' prefix
        if args.lower().startswith("at "):
            args = args[3:].strip()

        if not args:
            # Render room description directly \u2014 avoids recursive execute_cmd loop
            room = caller.location
            if not room:
                caller.msg("You are nowhere.")
                return
            caller.msg(room.return_appearance(caller))
            _send_room_oob(caller)
            return

        # Try to find a matching object in the room
        raw = args.lower()
        target_key = raw.replace(" ", "_")
        room = caller.location
        if not room:
            caller.msg("You are nowhere.")
            return

        found = None
        for obj in room.contents:
            if obj == caller:
                continue
            obj_key = obj.key.lower()
            obj_pretty = _pretty_name(obj.key).lower()
            if (target_key in obj_key or obj_key in target_key
                    or raw in obj_pretty or obj_pretty in raw):
                found = obj
                break

        if not found:
            caller.msg(f"You don't see '{args}' here.")
            return

        display = _pretty_name(found.key)
        actor_type = found.db.actor_type or "object"

        if actor_type == "mob":
            hp = found.db.hp or 0
            hp_max = found.db.hp_max or 40
            sh = found.db.shield_integrity or 0
            sh_max = found.db.shield_max or 20
            health = _mob_health_label(hp, hp_max)
            desc = found.db.desc or f"A hostile combat unit designated {display}."
            caller.msg(
                f"|w{display}|n\n"
                f"{desc}\n"
                f"Status: {health}\n"
                f"|wSH:|n {sh}/{sh_max}  |wHP:|n {hp}/{hp_max}"
            )
        elif actor_type == "npc":
            desc = found.db.desc or f"{display} stands here."
            caller.msg(f"|w{display}|n\n{desc}")
        else:
            desc = found.db.desc or f"You see {display}."
            caller.msg(f"|w{display}|n\n{desc}")


class CmdMoveAlias(Command):
    """Directional aliases and numpad navigation shortcuts.

    Examples:
      n s e w u d
      ne nw se sw
      8 2 4 6 7 9 1 3
      5 (look)
    """

    key = "n"
    aliases = ["s", "e", "w", "u", "d", "ne", "nw", "se", "sw", "1", "2", "3", "4", "5", "6", "7", "8", "9"]
    help_category = "General"

    _MAP = {
        "n": "north",
        "s": "south",
        "e": "east",
        "w": "west",
        "u": "up",
        "d": "down",
        "ne": "northeast",
        "nw": "northwest",
        "se": "southeast",
        "sw": "southwest",
        "8": "north",
        "2": "south",
        "4": "west",
        "6": "east",
        "7": "northwest",
        "9": "northeast",
        "1": "southwest",
        "3": "southeast",
        "5": "look",
    }

    def func(self):
        cmd = self._MAP.get(self.cmdstring.lower())
        if not cmd:
            self.caller.msg("Unknown movement alias.")
            return
        if cmd != "look" and (self.caller.db.sleeping or self.caller.db.sleeping_pending):
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
            self.caller.msg("|yYou can't move while resting. Type |wwake|y to get up first.|n")
            return
        self.caller.execute_cmd(cmd)
        if cmd != "look":
            _send_room_oob(self.caller)


class CmdTalk(Command):
    """Talk to NPCs in your room.

    Usage:
      talk <npc>

    Marshal Kaine can now hand out and complete contracts directly.
    """

    key = "talk"
    aliases = ["speak", "hail"]
    help_category = "General"

    def func(self):
        _update_location_objectives(self.caller)
        if not self.args:
            npcs = [obj.key for obj in self.caller.location.contents if obj.db.actor_type == "npc"]
            if not npcs:
                self.caller.msg("No one here seems interested in conversation.")
                return
            self.caller.msg(f"People nearby: {', '.join(npcs)}")
            return

        target_name = self.args.strip()
        # Strip natural-language prepositions so "talk to kaine" works like "talk kaine".
        for _prefix in ("to ", "with ", "at "):
            if target_name.lower().startswith(_prefix):
                target_name = target_name[len(_prefix):]
                break
        target_name = target_name.lower().replace(" ", "_")
        npc = None
        for obj in self.caller.location.contents:
            if obj.db.actor_type != "npc":
                continue
            key_match = target_name in obj.key.lower() or obj.key.lower() in target_name
            db_name = (obj.db.name or "").lower().replace(" ", "_")
            name_match = db_name and (target_name in db_name or db_name in target_name)
            if key_match or name_match:
                npc = obj
                break

        if not npc:
            self.caller.msg(f"No NPC matching '{self.args.strip()}' is here.")
            return

        display_name = npc.db.name or npc.key
        dialogue = npc.db.dialogue or "..."
        lines = [f"{display_name} says: \"{dialogue}\""]

        if npc.key == "helion_marshal":
            intro = "helion_intro_colony_defense"
            vanta = "vanta_expedition_artifact_recovery"
            qstate = _get_quest_state(self.caller)
            active = qstate.get("active", {})
            completed = set(qstate.get("completed", []))

            if intro not in completed and intro not in active:
                _, msg = _accept_contract(self.caller, intro, require_start_room=False)
                lines.append(msg)
            elif intro in active:
                # Talking to Kaine fulfils the "talk to Kaine" step \u2014 heals any stale state.
                _quests.set_event_progress(active, intro, "talk_kaine")
                self.caller.db.quest_state = qstate
                if _is_quest_complete(self.caller, intro):
                    _, msg = _turnin_contract(self.caller, intro, require_giver_room=False)
                    lines.append(msg)
                else:
                    prog = active[intro]
                    lines.append(
                        "Marshal Kaine says: \"Clear two raiders in the Warrens and report back.\""
                    )
                    lines.extend(_format_quest_progress(intro, prog))
            elif vanta not in completed and vanta not in active:
                _, msg = _accept_contract(self.caller, vanta, require_start_room=False)
                lines.append(msg)
                lines.append(
                    "Marshal Kaine says: \"Board at Shuttle Dock A3, hit Vanta hard, and bring me proof.\""
                )
            elif vanta in active:
                if _is_quest_complete(self.caller, vanta):
                    _, msg = _turnin_contract(self.caller, vanta, require_giver_room=False)
                    lines.append(msg)
                    # Guild breadcrumb: nudge the player toward the two guild halls.
                    guild_levels = self.caller.db.guild_levels or {}
                    in_a_guild = any(r > 0 for r in guild_levels.values())
                    if not in_a_guild:
                        lines.append(
                            "Marshal Kaine says: \"Outstanding work, soldier. "
                            "With field experience like yours, the faction halls will want you. "
                            "The Iron Covenant keeps order on Helion — their hall is in the industrial district. "
                            "The PSI Weavers operate from the Sanctum on Vanta IX. "
                            "Either outfit can take your career further than I can. Type |wguilds|n for details.\""
                        )
                else:
                    prog = active[vanta]
                    lines.append(
                        "Marshal Kaine says: \"Vanta objective still open. Keep pressure and return with the relic.\""
                    )
                    lines.extend(_format_quest_progress(vanta, prog))
            else:
                lines.append("Marshal Kaine says: \"You've done enough for now. Stand by for new orders.\"")

        elif npc.key == "vanta_blademaster":
            skills = self.caller.db.skills or {}
            sp = self.caller.db.skill_points or 0
            sk_b = skills.get("blades", 5)
            sk_bl = skills.get("bludgeons", 5)
            sk_p = skills.get("polearms", 5)
            sk_r = skills.get("ranged", 5)
            sk_m = skills.get("melee", 10)
            sk_d = skills.get("dodge", 10)
            sk_pa = skills.get("parry", 10)
            lines.append(
                f"Thorne assesses your form. Current skills: "
                f"Melee {sk_m}  Dodge {sk_d}  Parry {sk_pa}  "
                f"Blades {sk_b}  Bludgeons {sk_bl}  Polearms {sk_p}  Ranged {sk_r}"
            )
            if sp > 0:
                lines.append(
                    f"You have |y{sp} skill point(s)|n to spend. "
                    "Use 'train <melee|dodge|parry|blades|bludgeons|polearms|ranged>' to improve."
                )
            else:
                lines.append(
                    "Earn skill points by defeating enemies. "
                    "Use 'train <skill>' when you have points to spend."
                )
            lines.append(
                "Thorne says: \"When your weapon skill reaches 20, techniques open to you. "
                "Slash for blades, Concussion for bludgeons, Lunge for lance or blade. "
                "Type the technique name while in combat to queue it.\""
            )
            # Blade Trial quest.
            thorne_key = "thorne_blade_trial"
            qstate = _get_quest_state(self.caller)
            active = qstate.get("active", {})
            completed = set(qstate.get("completed", []))
            if thorne_key not in completed and thorne_key not in active:
                _, msg = _accept_contract(self.caller, thorne_key, require_start_room=False)
                lines.append(msg)
                lines.append(
                    "Thorne says: \"Two Glass Stalkers. In the dunes below. "
                    "Come back when it's done.\""
                )
            elif thorne_key in active:
                # Talking to Thorne fulfils the "talk to Thorne" step \u2014 heals any stale state.
                _quests.set_event_progress(active, thorne_key, "talk_thorne")
                self.caller.db.quest_state = qstate
                if _is_quest_complete(self.caller, thorne_key):
                    _, msg = _turnin_contract(self.caller, thorne_key, require_giver_room=False)
                    lines.append(msg)
                else:
                    prog = active[thorne_key]
                    lines.append("Thorne says: \"Stay focused.\"")
                    lines.extend(_format_quest_progress(thorne_key, prog))
            else:
                lines.append("Thorne nods. \"You carry yourself differently now. Good.\"")

        elif npc.key == "helion_scout":
            lines.append(
                "Kess says quietly: \"Slag Hounds in the Forge run hot \u2014 energy cells destabilize "
                "fast down there. Bludgeons crack them open. Blades just skate off the chassis.\""
            )
            kess_key = "kess_clear_scrapforge"
            qstate = _get_quest_state(self.caller)
            active = qstate.get("active", {})
            completed = set(qstate.get("completed", []))
            if kess_key not in completed and kess_key not in active:
                _, msg = _accept_contract(self.caller, kess_key, require_start_room=False)
                lines.append(msg)
                lines.append(
                    "Kess says: \"Two Hounds, Scrapforge Junction. "
                    "Come back when the junction's clear.\""
                )
            elif kess_key in active:
                # Talking to Kess fulfils the "talk to Kess" step \u2014 heals any stale state.
                _quests.set_event_progress(active, kess_key, "talk_kess")
                self.caller.db.quest_state = qstate
                if _is_quest_complete(self.caller, kess_key):
                    _, msg = _turnin_contract(self.caller, kess_key, require_giver_room=False)
                    lines.append(msg)
                else:
                    prog = active[kess_key]
                    lines.append("Kess says: \"Keep moving.\"")
                    lines.extend(_format_quest_progress(kess_key, prog))
            else:
                lines.append("Kess says: \"Junction's cleaner. Appreciate it.\"")

        elif npc.key == "vanta_elder":
            lines.append(
                "Lyros says: \"The vault's resonance still reads active. The Guardian has been "
                "there since before the Clans arrived. Old iron responds to impact \u2014 bludgeons, "
                "not blades, if you intend to face it.\""
            )
            lyros_key = "lyros_vault_recon"
            lyros2_key = "lyros_ancient_record"
            qstate = _get_quest_state(self.caller)
            active = qstate.get("active", {})
            completed = set(qstate.get("completed", []))

            if lyros_key not in completed and lyros_key not in active:
                _, msg = _accept_contract(self.caller, lyros_key, require_start_room=False)
                lines.append(msg)
                lines.append(
                    "Lyros says: \"Walk to the vault. Report what you find. That is all I ask.\""
                )
            elif lyros_key in active:
                # Talking to Lyros fulfils the "talk to Lyros" step — heals any stale state.
                _quests.set_event_progress(active, lyros_key, "talk_lyros")
                self.caller.db.quest_state = qstate
                if _is_quest_complete(self.caller, lyros_key):
                    _, msg = _turnin_contract(self.caller, lyros_key, require_giver_room=False)
                    lines.append(msg)
                else:
                    prog = active[lyros_key]
                    lines.append("Lyros says: \"The ruins wait.\"")
                    lines.extend(_format_quest_progress(lyros_key, prog))
            elif lyros2_key not in completed and lyros2_key not in active:
                # lyros_vault_recon done — offer the follow-up.
                _, msg = _accept_contract(self.caller, lyros2_key, require_start_room=False)
                lines.append(msg)
                lines.append(
                    "Lyros says: \"Deeper still lies the Subsurface Complex. Something there "
                    "predates the Clans by millennia. The Ancient Construct is its warden. "
                    "Destroy it and bring back what you find — the record must be preserved.\""
                )
            elif lyros2_key in active:
                _quests.set_event_progress(active, lyros2_key, "talk_lyros")
                self.caller.db.quest_state = qstate
                if _is_quest_complete(self.caller, lyros2_key):
                    _, msg = _turnin_contract(self.caller, lyros2_key, require_giver_room=False)
                    lines.append(msg)
                else:
                    prog = active[lyros2_key]
                    lines.append("Lyros says: \"The Construct still stands. Return when it is done.\"")
                    lines.extend(_format_quest_progress(lyros2_key, prog))
            else:
                lines.append("Lyros inclines his head. \"The ruins hold their secrets. You've seen that now.\"")

        elif npc.key == "iron_guildmaster":
            guild_levels = self.caller.db.guild_levels or {}
            rank = guild_levels.get("iron_covenant", 0)
            lines.append(
                f"Varro says: \"Iron Covenant rank {rank}. Every rank earned in iron and pain — "
                "the Covenant does not hand out honours.\""
            )
            lines.append(
                "\"Rank advances through combat. Push your level, push your guild rank. "
                "Rank 11 opens the deeper disciplines — Iron Will, Bulwark, Warlord Strike, "
                "Battle Mastery. Rank 20 is the ceiling. Few reach it.\""
            )
            varro1_key = "varro_depths_cleansing"
            varro2_key = "varro_captain_bounty"
            qstate = _get_quest_state(self.caller)
            active = qstate.get("active", {})
            completed = set(qstate.get("completed", []))

            if varro1_key not in completed and varro1_key not in active:
                _, msg = _accept_contract(self.caller, varro1_key, require_start_room=False)
                lines.append(msg)
                lines.append(
                    "Varro says: \"Scrap Crawlers are infesting the Conduit Run. "
                    "Three of them. Clear it out and I'll see you equipped.\""
                )
            elif varro1_key in active:
                _quests.set_event_progress(active, varro1_key, "talk_varro")
                self.caller.db.quest_state = qstate
                if _is_quest_complete(self.caller, varro1_key):
                    _, msg = _turnin_contract(self.caller, varro1_key, require_giver_room=False)
                    lines.append(msg)
                else:
                    prog = active[varro1_key]
                    lines.append("Varro says: \"Three Crawlers. Conduit Run. Move.\"")
                    lines.extend(_format_quest_progress(varro1_key, prog))
            elif varro2_key not in completed and varro2_key not in active:
                _, msg = _accept_contract(self.caller, varro2_key, require_start_room=False)
                lines.append(msg)
                lines.append(
                    "Varro says: \"There's a Raider Captain in the Stronghold. "
                    "Elite target, heavily armed. Taking him down sends a message. "
                    "Bring me proof and I'll make it worth your while.\""
                )
            elif varro2_key in active:
                _quests.set_event_progress(active, varro2_key, "talk_varro")
                self.caller.db.quest_state = qstate
                if _is_quest_complete(self.caller, varro2_key):
                    _, msg = _turnin_contract(self.caller, varro2_key, require_giver_room=False)
                    lines.append(msg)
                else:
                    prog = active[varro2_key]
                    lines.append("Varro says: \"Captain's still breathing. Fix that.\"")
                    lines.extend(_format_quest_progress(varro2_key, prog))
            else:
                lines.append("Varro says: \"You've done your share. The Covenant remembers.\"")

        elif npc.key == "psi_guildmaster":
            guild_levels = self.caller.db.guild_levels or {}
            rank = guild_levels.get("psi_weavers", 0)
            lines.append(
                f"Solen says: \"PSI Weavers rank {rank}. Resonance does not lie — "
                "every rank is a deepening of the signal you carry.\""
            )
            lines.append(
                "\"The high disciplines open at rank 11: Deep Resonance, Void Lance, "
                "PSI Surge, Mind Fortress. Rank 20 is where the frequency becomes architecture. "
                "Most Weavers plateau at 8 or 9. You may be different.\""
            )
            solen_key = "solen_spire_purge"
            qstate = _get_quest_state(self.caller)
            active = qstate.get("active", {})
            completed = set(qstate.get("completed", []))

            if solen_key not in completed and solen_key not in active:
                _, msg = _accept_contract(self.caller, solen_key, require_start_room=False)
                lines.append(msg)
                lines.append(
                    "Solen says: \"Crystal Wraiths are resonance-entities — they amplify "
                    "and corrupt the field harmonics of the spire interior. Three of them "
                    "must be purged before the signal stabilises. I need this done.\""
                )
            elif solen_key in active:
                _quests.set_event_progress(active, solen_key, "talk_solen")
                self.caller.db.quest_state = qstate
                if _is_quest_complete(self.caller, solen_key):
                    _, msg = _turnin_contract(self.caller, solen_key, require_giver_room=False)
                    lines.append(msg)
                else:
                    prog = active[solen_key]
                    lines.append("Solen says: \"The wraiths persist. Maintain focus.\"")
                    lines.extend(_format_quest_progress(solen_key, prog))
            else:
                lines.append(
                    "Solen says: \"The spire resonates cleanly now. Your signal has grown.\""
                )

        elif npc.key == "vanta_broker":
            lines.append(
                "Sorn says: \"Customs ring. Everything that moves through Vanta IX "
                "moves through here eventually. I see what people bring back from the ruins — "
                "and how much of it they understand.\""
            )
            sorn_key = "sorn_deep_salvage"
            qstate = _get_quest_state(self.caller)
            active = qstate.get("active", {})
            completed = set(qstate.get("completed", []))
            vanta_prereq = "vanta_expedition_artifact_recovery"

            if vanta_prereq not in completed:
                lines.append(
                    "Sorn says: \"You haven't been deep yet. Come back once you've run "
                    "a real ruin contract — the surface work doesn't interest me.\""
                )
            elif sorn_key not in completed and sorn_key not in active:
                _, msg = _accept_contract(self.caller, sorn_key, require_start_room=False)
                lines.append(msg)
                lines.append(
                    "Sorn says: \"Subsurface Complex, east of the spire. Get in, "
                    "reach the lower level, document what you find. "
                    "I'll have something waiting for you when you come back.\""
                )
            elif sorn_key in active:
                _quests.set_event_progress(active, sorn_key, "talk_sorn")
                self.caller.db.quest_state = qstate
                if _is_quest_complete(self.caller, sorn_key):
                    _, msg = _turnin_contract(self.caller, sorn_key, require_giver_room=False)
                    lines.append(msg)
                else:
                    prog = active[sorn_key]
                    lines.append("Sorn says: \"Subsurface Complex. You haven't been down yet.\"")
                    lines.extend(_format_quest_progress(sorn_key, prog))
            else:
                lines.append(
                    "Sorn says: \"You've seen the complex. Not many can say that.\""
                )

        elif npc.db.role == "information":
            # Generic info-NPC branch: show any tactical dialogue and quest hints.
            lines.append(
                f"{display_name} adds: "
                "\"Check 'scan' when you enter a new area \u2014 it shows room type and hostiles present.\""
            )

        self.caller.msg("\n".join(lines))
