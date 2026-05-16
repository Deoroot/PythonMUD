"""PSI ability commands.

Contains CmdPsi with all PSI sub-abilities: heal, shock, ward, bolt, shatter, lance.
"""

from __future__ import annotations

from evennia import Command, utils

from commands.cmd_utils import (
    _ensure_project_root_on_path,
    _pretty_name,
    _find_object_by_id,
    _get_background_perks,
    _get_guild_skill_bonuses,
    _mob_health_label,
    _send_prompt,
    _check_level_up,
    _update_kill_objectives,
    _award_mob_credits,
    RESPAWN_DELAY,
    _respawn_mob,
)
from commands.combat_commands import _end_combat_session

_ensure_project_root_on_path()


class CmdPsi(Command):
    """Use a PSI ability.

    Usage:
      psi              — show PSI pool, MIND stat, and ability descriptions
      psi heal         — channel PSI energy inward to restore HP (any time)
      psi shock        — discharge PSI at your combat target, bypassing armor

    PSI Weavers guild abilities (membership required):
      psi ward         — erect a 1-round PSI barrier absorbing melee damage  [rank 1+]
      psi bolt         — concentrated PSI blast, stronger than shock          [rank 3+]
      psi shatter      — massive PSI burst + stuns target 1 round             [rank 6+]
      psi lance        — void energy strike that bypasses shields entirely     [rank 13+]

    Both base abilities draw from your PSI pool. PSI regenerates passively
    and scales with MIND. Higher MIND means stronger heals and more damage.

    PSI Heal:  costs 20 PSI. Restores 10 HP + 2 per MIND above 10.
    PSI Shock: costs 25 PSI. Deals 8 dmg + 3 per MIND above 10 to a combat
               target. Bypasses physical armor; shield absorbs first.
    """

    key = "psi"
    help_category = "Combat"

    def func(self):
        args = self.args.strip().lower() if self.args else ""

        if not args:
            self._show_psi_info()
            return

        if args == "heal":
            self._psi_heal()
            return

        if args in ("shock", "blast"):
            self._psi_shock()
            return

        if args == "ward":
            self._psi_ward()
            return

        if args == "bolt":
            self._psi_bolt()
            return

        if args == "shatter":
            self._psi_shatter()
            return

        if args in ("lance", "void lance", "void_lance"):
            self._psi_lance()
            return

        self.caller.msg(
            f"Unknown PSI ability '{args}'. "
            "Usage: psi  |  psi heal  |  psi shock  |  psi ward  |  psi bolt  |  psi shatter  |  psi lance"
        )

    def _show_psi_info(self):
        caller = self.caller
        psi = caller.db.psi or 0
        psi_max = caller.db.psi_max or 60
        attrs = caller.db.attrs or {}
        mind = attrs.get("mind", 10)

        guild_levels = caller.db.guild_levels or {}
        psi_rank = guild_levels.get("psi_weavers", 0)
        focused_bonus = _get_guild_skill_bonuses(caller).get("psi_heal_bonus", 0)

        heal_power = 10 + max(0, (mind - 10) * 2) + focused_bonus
        shock_power = 8 + max(0, (mind - 10) * 3)
        heal_cost = max(1, 20 - _get_background_perks(caller)["psi_heal_cost_reduction"])

        lines = [
            f"|cPSI|n: {psi}/{psi_max}   MIND: {mind}",
            "",
            f"  |wpsi heal|n   — Restore ~{heal_power} HP    [cost: {heal_cost} PSI]  (any time)",
            f"  |wpsi shock|n  — Deal ~{shock_power} PSI dmg [cost: 25 PSI]  (combat only)",
        ]

        if psi_rank >= 1:
            ward_abs = 20 + psi_rank * 2
            lines.append(f"  |wpsi ward|n   — Absorb {ward_abs} damage next round [cost: 30 PSI]  (PSI Weavers rank {psi_rank})")
        if psi_rank >= 3:
            bolt_power = 15 + max(0, (mind - 10) * 4)
            lines.append(f"  |wpsi bolt|n   — Deal ~{bolt_power} PSI dmg [cost: 35 PSI]  (PSI Weavers rank {psi_rank})")
        if psi_rank >= 6:
            shatter_power = 20 + max(0, (mind - 10) * 6)
            lines.append(f"  |wpsi shatter|n — Deal ~{shatter_power} PSI dmg + stun [cost: 50 PSI]  (PSI Weavers rank {psi_rank})")
        if psi_rank >= 13:
            lance_power = 30 + max(0, (mind - 10) * 8)
            lines.append(f"  |wpsi lance|n  — Deal ~{lance_power} direct HP dmg (bypasses shields) [cost: 70 PSI]  (PSI Weavers rank {psi_rank})")

        lines.append("")
        lines.append("PSI regenerates passively. MIND increases both heal and damage.")
        caller.msg("\n".join(lines))

    def _psi_heal(self):
        _ensure_project_root_on_path()
        from mudgame.systems.psi import resolve_psi_heal

        caller = self.caller
        psi = caller.db.psi or 0
        psi_max = caller.db.psi_max or 60
        hp = caller.db.hp or 0
        hp_max = caller.db.hp_max or 100
        attrs = caller.db.attrs or {}
        mind = attrs.get("mind", 10)

        # Focused Channel guild bonus.
        heal_bonus = _get_guild_skill_bonuses(caller).get("psi_heal_bonus", 0)

        # Compact Remnant background: PSI Heal costs 15 instead of 20.
        cost_reduction = _get_background_perks(caller)["psi_heal_cost_reduction"]
        heal_cost = max(1, 20 - cost_reduction)

        new_psi, hp_gained, note = resolve_psi_heal(psi, psi_max, mind, hp, hp_max, heal_bonus, cost_reduction)

        if note == "insufficient_psi":
            caller.msg(
                f"|yNot enough PSI. PSI Heal costs {heal_cost} PSI "
                f"(you have {psi}/{psi_max}).|n"
            )
            return

        if note == "already_full":
            caller.msg("|yYour wounds are already fully healed.|n")
            return

        caller.db.psi = new_psi
        caller.db.hp = min(hp_max, hp + hp_gained)
        bonus_str = f" (+{heal_bonus} Focused Channel)" if heal_bonus else ""
        caller.msg(
            f"|gYou channel PSI energy inward.|n  "
            f"|w+{hp_gained} HP|n restored{bonus_str}.  "
            f"PSI: {new_psi}/{psi_max}"
        )
        _send_prompt(caller)

    def _psi_shock(self):
        _ensure_project_root_on_path()
        from mudgame.systems.psi import resolve_psi_shock

        caller = self.caller
        session = caller.db.combat_session or {}
        target_id = session.get("target_id")
        if not target_id:
            caller.msg(
                "|yPSI Shock requires an active combat target. "
                "Use 'attack <mob>' first.|n"
            )
            return

        mob = _find_object_by_id(int(target_id))
        if not mob or not mob.location or caller.location != mob.location:
            _end_combat_session(caller, "|yCombat ended: target lost or left room.|n")
            return

        psi = caller.db.psi or 0
        psi_max = caller.db.psi_max or 60
        attrs = caller.db.attrs or {}
        mind = attrs.get("mind", 10)

        mob_shield = mob.db.shield_integrity or 0
        mob_hp = mob.db.hp or 0

        new_psi, sh_dmg, hp_dmg, note = resolve_psi_shock(psi, mind, mob_shield, mob_hp)

        if note == "insufficient_psi":
            caller.msg(
                f"|yNot enough PSI. PSI Shock costs 25 PSI "
                f"(you have {psi}/{psi_max}).|n"
            )
            return

        # Apply damage.
        mob.db.shield_integrity = max(0, mob_shield - sh_dmg)
        mob.db.hp = max(0, mob_hp - hp_dmg)
        caller.db.psi = new_psi

        total_dmg = sh_dmg + hp_dmg
        mob_display = _pretty_name(mob.key)

        parts = []
        if sh_dmg:
            parts.append(f"shield: -{sh_dmg}")
        if hp_dmg:
            parts.append(f"HP: -{hp_dmg}")
        detail = f"  ({', '.join(parts)})" if parts else ""

        caller.msg(
            f"|cYou release a PSI pulse at {mob_display}.|n  "
            f"|w{total_dmg} PSI damage|n{detail}  "
            f"PSI: {new_psi}/{psi_max}"
        )

        mob_hp_max = mob.db.hp_max or 40
        health_label = _mob_health_label(mob.db.hp, mob_hp_max)
        caller.msg(f"|w{mob_display}|n is {health_label}.")

        # Handle mob death from PSI shock.
        if mob.db.hp <= 0:
            xp_gain = mob.db.xp or 25
            caller.db.xp = (caller.db.xp or 0) + xp_gain
            credit_drop = _award_mob_credits(caller, mob.key)
            credit_str = f" |y+{credit_drop}c.|n" if credit_drop else ""
            caller.msg(f"|r{mob_display} collapses, systems failing.|n |g+{xp_gain} XP.|n{credit_str}")
            level_up_msgs = _check_level_up(caller)
            for msg in level_up_msgs:
                caller.msg(msg)
            _update_kill_objectives(caller, mob.key)
            mob.location = None
            utils.delay(RESPAWN_DELAY, _respawn_mob, mob.id)
            _end_combat_session(caller, notify=False)
        else:
            _send_prompt(caller)

    # ------------------------------------------------------------------
    # PSI Weavers guild abilities
    # ------------------------------------------------------------------

    def _check_psi_weaver_rank(self, min_rank: int, ability_name: str) -> bool:
        """Return True if caller meets the PSI Weavers rank requirement, else msg them."""
        caller = self.caller
        guild_levels = caller.db.guild_levels or {}
        rank = guild_levels.get("psi_weavers", 0)
        if rank < min_rank:
            caller.msg(
                f"|y{ability_name} requires PSI Weavers rank {min_rank} "
                f"(you are rank {rank}). Join or advance at the Sanctum on Vanta IX.|n"
            )
            return False
        return True

    def _psi_ward(self):
        _ensure_project_root_on_path()
        from mudgame.systems.psi import resolve_psi_ward

        if not self._check_psi_weaver_rank(1, "Resonance Shield"):
            return

        caller = self.caller
        psi = caller.db.psi or 0
        psi_max = caller.db.psi_max or 60
        guild_levels = caller.db.guild_levels or {}
        rank = guild_levels.get("psi_weavers", 0)

        new_psi, absorption, note = resolve_psi_ward(psi, rank)

        if note == "insufficient_psi":
            caller.msg(
                f"|yNot enough PSI. Resonance Shield costs 30 PSI "
                f"(you have {psi}/{psi_max}).|n"
            )
            return

        caller.db.psi = new_psi
        caller.db.psi_ward = absorption
        caller.msg(
            f"|cYou raise a Resonance Shield.|n  "
            f"Absorbs up to |w{absorption}|n incoming melee damage this round.  "
            f"PSI: {new_psi}/{psi_max}"
        )
        _send_prompt(caller)

    def _psi_bolt(self):
        _ensure_project_root_on_path()
        from mudgame.systems.psi import resolve_psi_bolt

        if not self._check_psi_weaver_rank(3, "PSI Bolt"):
            return

        caller = self.caller
        session = caller.db.combat_session or {}
        target_id = session.get("target_id")
        if not target_id:
            caller.msg("|yPSI Bolt requires an active combat target. Use 'attack <mob>' first.|n")
            return

        mob = _find_object_by_id(int(target_id))
        if not mob or not mob.location or caller.location != mob.location:
            _end_combat_session(caller, "|yCombat ended: target lost or left room.|n")
            return

        psi = caller.db.psi or 0
        psi_max = caller.db.psi_max or 60
        attrs = caller.db.attrs or {}
        mind = attrs.get("mind", 10)
        mob_shield = mob.db.shield_integrity or 0
        mob_hp = mob.db.hp or 0

        new_psi, sh_dmg, hp_dmg, note = resolve_psi_bolt(psi, mind, mob_shield, mob_hp)

        if note == "insufficient_psi":
            caller.msg(
                f"|yNot enough PSI. PSI Bolt costs 35 PSI "
                f"(you have {psi}/{psi_max}).|n"
            )
            return

        mob.db.shield_integrity = max(0, mob_shield - sh_dmg)
        mob.db.hp = max(0, mob_hp - hp_dmg)
        caller.db.psi = new_psi

        total_dmg = sh_dmg + hp_dmg
        mob_display = _pretty_name(mob.key)
        parts = []
        if sh_dmg:
            parts.append(f"shield: -{sh_dmg}")
        if hp_dmg:
            parts.append(f"HP: -{hp_dmg}")
        detail = f"  ({', '.join(parts)})" if parts else ""

        caller.msg(
            f"|cYou hurl a PSI Bolt at {mob_display}.|n  "
            f"|w{total_dmg} PSI damage|n{detail}  "
            f"PSI: {new_psi}/{psi_max}"
        )

        mob_hp_max = mob.db.hp_max or 40
        health_label = _mob_health_label(mob.db.hp, mob_hp_max)
        caller.msg(f"|w{mob_display}|n is {health_label}.")

        if mob.db.hp <= 0:
            xp_gain = mob.db.xp or 25
            caller.db.xp = (caller.db.xp or 0) + xp_gain
            credit_drop = _award_mob_credits(caller, mob.key)
            credit_str = f" |y+{credit_drop}c.|n" if credit_drop else ""
            caller.msg(f"|r{mob_display} collapses, systems failing.|n |g+{xp_gain} XP.|n{credit_str}")
            level_up_msgs = _check_level_up(caller)
            for msg in level_up_msgs:
                caller.msg(msg)
            _update_kill_objectives(caller, mob.key)
            mob.location = None
            utils.delay(RESPAWN_DELAY, _respawn_mob, mob.id)
            _end_combat_session(caller, notify=False)
        else:
            _send_prompt(caller)

    def _psi_shatter(self):
        _ensure_project_root_on_path()
        from mudgame.systems.psi import resolve_psi_shatter

        if not self._check_psi_weaver_rank(6, "Mind Shatter"):
            return

        caller = self.caller
        session = caller.db.combat_session or {}
        target_id = session.get("target_id")
        if not target_id:
            caller.msg("|yMind Shatter requires an active combat target. Use 'attack <mob>' first.|n")
            return

        mob = _find_object_by_id(int(target_id))
        if not mob or not mob.location or caller.location != mob.location:
            _end_combat_session(caller, "|yCombat ended: target lost or left room.|n")
            return

        psi = caller.db.psi or 0
        psi_max = caller.db.psi_max or 60
        attrs = caller.db.attrs or {}
        mind = attrs.get("mind", 10)
        mob_shield = mob.db.shield_integrity or 0
        mob_hp = mob.db.hp or 0

        new_psi, sh_dmg, hp_dmg, stuns, note = resolve_psi_shatter(psi, mind, mob_shield, mob_hp)

        if note == "insufficient_psi":
            caller.msg(
                f"|yNot enough PSI. Mind Shatter costs 50 PSI "
                f"(you have {psi}/{psi_max}).|n"
            )
            return

        mob.db.shield_integrity = max(0, mob_shield - sh_dmg)
        mob.db.hp = max(0, mob_hp - hp_dmg)
        caller.db.psi = new_psi

        if stuns and mob.db.hp > 0:
            mob.db.is_stunned = True

        total_dmg = sh_dmg + hp_dmg
        mob_display = _pretty_name(mob.key)
        parts = []
        if sh_dmg:
            parts.append(f"shield: -{sh_dmg}")
        if hp_dmg:
            parts.append(f"HP: -{hp_dmg}")
        detail = f"  ({', '.join(parts)})" if parts else ""
        stun_str = "  |rSTUNNED 1 round!|n" if stuns and mob.db.hp > 0 else ""

        caller.msg(
            f"|cYou unleash Mind Shatter at {mob_display}!|n  "
            f"|w{total_dmg} PSI damage|n{detail}{stun_str}  "
            f"PSI: {new_psi}/{psi_max}"
        )

        mob_hp_max = mob.db.hp_max or 40
        health_label = _mob_health_label(mob.db.hp, mob_hp_max)
        caller.msg(f"|w{mob_display}|n is {health_label}.")

        if mob.db.hp <= 0:
            xp_gain = mob.db.xp or 25
            caller.db.xp = (caller.db.xp or 0) + xp_gain
            credit_drop = _award_mob_credits(caller, mob.key)
            credit_str = f" |y+{credit_drop}c.|n" if credit_drop else ""
            caller.msg(f"|r{mob_display} collapses, systems failing.|n |g+{xp_gain} XP.|n{credit_str}")
            level_up_msgs = _check_level_up(caller)
            for msg in level_up_msgs:
                caller.msg(msg)
            _update_kill_objectives(caller, mob.key)
            mob.location = None
            utils.delay(RESPAWN_DELAY, _respawn_mob, mob.id)
            _end_combat_session(caller, notify=False)
        else:
            _send_prompt(caller)

    def _psi_lance(self):
        _ensure_project_root_on_path()
        from mudgame.systems.psi import resolve_psi_lance

        if not self._check_psi_weaver_rank(13, "Void Lance"):
            return

        caller = self.caller
        session = caller.db.combat_session or {}
        target_id = session.get("target_id")
        if not target_id:
            caller.msg("|yVoid Lance requires an active combat target. Use 'attack <mob>' first.|n")
            return

        mob = _find_object_by_id(int(target_id))
        if not mob or not mob.location or caller.location != mob.location:
            _end_combat_session(caller, "|yCombat ended: target lost or left room.|n")
            return

        # Check void_lance skill trained.
        guild_skills = caller.db.guild_skills or {}
        lance_pct = guild_skills.get("psi_weavers", {}).get("void_lance", 0)
        if lance_pct <= 0:
            caller.msg(
                "|yYou have not trained Void Lance. "
                "Use |wtrain void_lance|n to invest XP in it.|n"
            )
            return

        psi = caller.db.psi or 0
        psi_max = caller.db.psi_max or 60
        attrs = caller.db.attrs or {}
        mind = attrs.get("mind", 10)
        mob_hp = mob.db.hp or 0

        new_psi, hp_dmg, note = resolve_psi_lance(psi, mind, mob_hp)

        if note == "insufficient_psi":
            caller.msg(
                f"|yNot enough PSI. Void Lance costs 70 PSI "
                f"(you have {psi}/{psi_max}).|n"
            )
            return

        # Void Lance bypasses shields entirely — direct HP damage.
        mob.db.hp = max(0, mob_hp - hp_dmg)
        caller.db.psi = new_psi

        mob_display = _pretty_name(mob.key)
        caller.msg(
            f"|cYou hurl a Void Lance at {mob_display}!|n  "
            f"|w{hp_dmg} direct HP damage|n (shields bypassed)  "
            f"PSI: {new_psi}/{psi_max}"
        )

        mob_hp_max = mob.db.hp_max or 40
        health_label = _mob_health_label(mob.db.hp, mob_hp_max)
        caller.msg(f"|w{mob_display}|n is {health_label}.")

        if mob.db.hp <= 0:
            xp_gain = mob.db.xp or 25
            caller.db.xp = (caller.db.xp or 0) + xp_gain
            credit_drop = _award_mob_credits(caller, mob.key)
            credit_str = f" |y+{credit_drop}c.|n" if credit_drop else ""
            caller.msg(f"|r{mob_display} collapses, systems failing.|n |g+{xp_gain} XP.|n{credit_str}")
            level_up_msgs = _check_level_up(caller)
            for msg in level_up_msgs:
                caller.msg(msg)
            _update_kill_objectives(caller, mob.key)
            mob.location = None
            utils.delay(RESPAWN_DELAY, _respawn_mob, mob.id)
            _end_combat_session(caller, notify=False)
        else:
            _send_prompt(caller)

        mob_hp_max = mob.db.hp_max or 40
        health_label = _mob_health_label(mob.db.hp, mob_hp_max)
        caller.msg(f"|w{mob_display}|n is {health_label}.")

        if mob.db.hp <= 0:
            xp_gain = mob.db.xp or 25
            caller.db.xp = (caller.db.xp or 0) + xp_gain
            credit_drop = _award_mob_credits(caller, mob.key)
            credit_str = f" |y+{credit_drop}c.|n" if credit_drop else ""
            caller.msg(f"|r{mob_display} collapses, systems failing.|n |g+{xp_gain} XP.|n{credit_str}")
            level_up_msgs = _check_level_up(caller)
            for msg in level_up_msgs:
                caller.msg(msg)
            _update_kill_objectives(caller, mob.key)
            mob.location = None
            utils.delay(RESPAWN_DELAY, _respawn_mob, mob.id)
            _end_combat_session(caller, notify=False)
        else:
            _send_prompt(caller)
