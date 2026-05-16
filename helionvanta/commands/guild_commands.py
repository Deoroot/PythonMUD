"""Guild commands: guilds, join, advance, leaveguild, sunder, warlord."""

from __future__ import annotations

from evennia import Command

from commands.cmd_utils import (
    _ensure_project_root_on_path,
    _load_world_data,
    _GUILD_MAX_RANK,
    _guild_skill_cap,
    _apply_guild_rank_passives,
    _remove_guild_rank_passives,
)

_ensure_project_root_on_path()
from mudgame.systems.guilds import (  # noqa: E402
    resolve_guild_join as _resolve_guild_join,
    resolve_guild_advance as _resolve_guild_advance,
)


class CmdGuilds(Command):
    """Show available guilds and your current membership.

    Usage:
      guilds

    Displays the two guilds, their location, and your rank/skills if you
    have joined. Use |wjoin|n at the guild hall to enlist.
    """

    key = "guilds"
    help_category = "Guild"
    locks = "cmd:all()"

    def func(self):
        caller = self.caller
        guilds = _load_world_data().get("guilds", {})
        guild_levels = caller.db.guild_levels or {}
        guild_skills = caller.db.guild_skills or {}
        free_levels = caller.db.free_levels or 0

        lines = ["|c[ GUILDS ]|n"]
        if free_levels > 0:
            lines.append(f"  |yFree level tokens available: {free_levels}|n  (use |wadvance|n at your guild hall)")
        lines.append("")

        for gkey, gdata in guilds.items():
            rank = guild_levels.get(gkey, 0)
            max_rank = gdata.get("max_rank", _GUILD_MAX_RANK)
            hall = gdata.get("hall_room", "?").replace("_", " ").title()
            gname = gdata.get("name", gkey)

            if rank > 0:
                lines.append(f"  |w{gname}|n  - |gRank {rank}/{max_rank}|n")
            else:
                lines.append(f"  |w{gname}|n  - Not joined  (hall: {hall})")

            # Show passive per-rank bonuses.
            passives = gdata.get("passive_per_rank", {})
            if passives:
                p_str = ", ".join(f"+{v} {k}" for k, v in passives.items())
                lines.append(f"    Per rank: {p_str}")

            # Show skills.
            p_skills = guild_skills.get(gkey, {})
            for sk_key, sk_data in gdata.get("skills", {}).items():
                pct = p_skills.get(sk_key, 0)
                cap = _guild_skill_cap(gkey, sk_key, rank)
                if rank > 0:
                    # Show current pct and what's trainable.
                    gate_str = f" [cap at rank {rank}: {cap}%]" if cap < 100 else ""
                    base_cost = sk_data["xp_cost_per_pct"]
                    tier = 1 + pct // 25
                    current_cost = base_cost * tier
                    tier_str = f" (x{tier})" if tier > 1 else ""
                    lines.append(
                        f"    |w{sk_data['name']}|n  {pct}%{gate_str}  "
                        f"|y{current_cost} XP/pct{tier_str}|n  - {sk_data['desc']}"
                    )
                else:
                    lines.append(f"    {sk_data['name']}  - {sk_data['desc']}")
            lines.append("")

        lines.append("  |wjoin|n at the guild hall to enlist.  |wadvance|n to spend a level token.")
        lines.append("  |wtrain <skill>|n to spend XP on guild skills (must be a member).")
        caller.msg("\n".join(lines))


# ---------------------------------------------------------------------------
# CmdJoin - join a guild at the guild hall
# ---------------------------------------------------------------------------

class CmdJoin(Command):
    """Join a guild. You must be standing at the guild hall.

    Usage:
      join

    Costs 1 free level token (earned by leveling past 10).
    You may only join one guild (Iron Covenant or PSI Weavers).
    Grants rank 1 and the first tier of passive stat bonuses.
    """

    key = "join"
    help_category = "Guild"
    locks = "cmd:all()"

    def func(self):
        caller = self.caller
        guilds = _load_world_data().get("guilds", {})

        room = caller.location
        if not room:
            caller.msg("You are nowhere.")
            return
        room_key = room.db.room_key or ""

        # Determine which guild hall the caller is in.
        target_guild_key = next(
            (gk for gk, gd in guilds.items() if gd.get("hall_room") == room_key),
            None,
        )
        if not target_guild_key:
            halls = ", ".join(
                gd.get("hall_room", "").replace("_", " ").title()
                for gd in guilds.values()
            )
            caller.msg(f"|yYou must be at a guild hall to join. Guild halls: {halls}.|n")
            return

        ok, msg, new_guild_levels, new_free_levels, new_guild_skills = _resolve_guild_join(
            guild_key=target_guild_key,
            room_key=room_key,
            guild_levels=dict(caller.db.guild_levels or {}),
            free_levels=caller.db.free_levels or 0,
            guild_skills=dict(caller.db.guild_skills or {}),
            guilds_data=guilds,
        )
        caller.msg(msg)
        if ok:
            caller.db.guild_levels = new_guild_levels
            caller.db.free_levels = new_free_levels
            caller.db.guild_skills = new_guild_skills
            _apply_guild_rank_passives(caller, target_guild_key)


# ---------------------------------------------------------------------------
# CmdAdvance - advance guild rank at the guild hall
# ---------------------------------------------------------------------------

class CmdAdvance(Command):
    """Advance your guild rank. You must be at the guild hall.

    Usage:
      advance

    Costs 1 free level token (earned by leveling past 10).
    Each rank increases passive bonuses and unlocks higher training caps.
    Maximum rank is 20.
    """

    key = "advance"
    help_category = "Guild"
    locks = "cmd:all()"

    def func(self):
        caller = self.caller
        guilds = _load_world_data().get("guilds", {})

        room = caller.location
        if not room:
            caller.msg("You are nowhere.")
            return
        room_key = room.db.room_key or ""

        target_guild_key = next(
            (gk for gk, gd in guilds.items() if gd.get("hall_room") == room_key),
            None,
        )
        if not target_guild_key:
            caller.msg("|yYou must be at your guild hall to advance.|n")
            return

        ok, msg, new_guild_levels, new_free_levels = _resolve_guild_advance(
            guild_key=target_guild_key,
            room_key=room_key,
            guild_levels=dict(caller.db.guild_levels or {}),
            free_levels=caller.db.free_levels or 0,
            guilds_data=guilds,
        )
        caller.msg(msg)
        if ok:
            caller.db.guild_levels = new_guild_levels
            caller.db.free_levels = new_free_levels
            _apply_guild_rank_passives(caller, target_guild_key)


# ---------------------------------------------------------------------------
# CmdLeaveGuild - resign from your current guild (refunds tokens)
# ---------------------------------------------------------------------------

class CmdLeaveGuild(Command):
    """Resign from your current guild, recovering your spent level tokens.

    Usage:
      leaveguild
      leaveguild confirm

    All tokens spent on this guild (1 to join + 1 per advance) are refunded.
    All guild stat passives are reversed and guild skill training is wiped.
    You will need to re-join from scratch if you change your mind.

    This can be used from anywhere - no need to visit the guild hall.
    """

    key = "leaveguild"
    aliases = ["leave guild"]
    help_category = "Guild"
    locks = "cmd:all()"

    def func(self):
        caller = self.caller
        guild_levels = caller.db.guild_levels or {}

        # Find the guild the caller belongs to.
        current_guild_key = next(
            (gk for gk, rank in guild_levels.items() if rank > 0), None
        )
        if not current_guild_key:
            caller.msg("|yYou are not a member of any guild.|n")
            return

        guilds = _load_world_data().get("guilds", {})
        gdata = guilds.get(current_guild_key, {})
        gname = gdata.get("name", current_guild_key)
        rank = guild_levels[current_guild_key]
        tokens_refunded = rank  # 1 join token + (rank-1) advance tokens

        if self.args.strip().lower() != "confirm":
            passives = gdata.get("passive_per_rank", {})
            p_str = ", ".join(f"-{v * rank} {k}" for k, v in passives.items())
            caller.msg(
                f"|c{gname} - Resign|n\n"
                f"  Current rank: {rank}  |  Tokens refunded: {tokens_refunded}\n"
                f"  Stat passives removed: {p_str or 'none'}\n"
                f"  All guild skill training for this guild is lost.\n\n"
                f"|yType |wleaveguild confirm|y to proceed, or do nothing to cancel.|n"
            )
            return

        # Reverse all stat passives accumulated through join + advances.
        _remove_guild_rank_passives(caller, current_guild_key, rank)

        # Refund tokens.
        caller.db.free_levels = (caller.db.free_levels or 0) + tokens_refunded

        # Clear guild membership.
        new_guild_levels = dict(guild_levels)
        new_guild_levels.pop(current_guild_key, None)
        caller.db.guild_levels = new_guild_levels

        new_guild_skills = dict(caller.db.guild_skills or {})
        new_guild_skills.pop(current_guild_key, None)
        caller.db.guild_skills = new_guild_skills

        caller.msg(
            f"|g*** You have resigned from the {gname}. ***|n\n"
            f"  {tokens_refunded} level token(s) returned (total: {caller.db.free_levels}).\n"
            f"  Guild stat bonuses have been reversed.\n"
            f"  Visit a guild hall to join a new guild."
        )


# ---------------------------------------------------------------------------
# CmdSunder - queue the Iron Covenant guild technique
# ---------------------------------------------------------------------------

class CmdSunder(Command):
    """Queue the Sunder Strike guild technique (Iron Covenant, rank 5+).

    Usage:
      sunder

    A massive 2-round wind-up strike that deals 1.5x weapon damage + 10 flat,
    bypassing the target's parry defense. Costs 40 Stamina on fire.

    Requires: Iron Covenant membership (rank 5+), sunder_strike trained > 0%.
    Must be in active combat.
    """

    key = "sunder"
    help_category = "Guild"
    locks = "cmd:all()"

    def func(self):
        caller = self.caller
        session = caller.db.combat_session or {}
        if not session.get("target_id"):
            caller.msg("|yYou must be in active combat to use Sunder Strike.|n")
            return

        # Guild gate checks.
        guild_levels = caller.db.guild_levels or {}
        rank = guild_levels.get("iron_covenant", 0)
        if rank < 5:
            caller.msg(
                f"|ySunder Strike requires Iron Covenant rank 5 "
                f"(you are rank {rank}).|n"
            )
            return

        guild_skills = caller.db.guild_skills or {}
        anni_pct = guild_skills.get("iron_covenant", {}).get("sunder_strike", 0)
        if anni_pct <= 0:
            caller.msg(
                "|yYou have not trained Sunder Strike. "
                "Use |wtrain sunder_strike|n to invest XP in it.|n"
            )
            return

        existing = caller.db.queued_technique
        if existing and isinstance(existing, dict):
            ex_name = existing.get("name", "?")
            ex_tr = existing.get("ticks_remaining", 0)
            caller.msg(
                f"|yYou already have {ex_name.replace('_', ' ').title()} queued "
                f"({ex_tr} round(s) until it fires). Wait for it to resolve.|n"
            )
            return

        caller.db.queued_technique = {
            "name": "sunder_strike",
            "ticks_remaining": 2,
        }
        caller.msg(
            "|cYou wind up for Sunder Strike.|n  "
            "Fires in 2 rounds - 1.5x weapon damage + 10 flat, ignores parry."
        )


# ---------------------------------------------------------------------------
# CmdWarlordStrike - queue the Iron Covenant rank 15 guild technique
# ---------------------------------------------------------------------------

class CmdWarlordStrike(Command):
    """Queue the Warlord Strike guild technique (Iron Covenant, rank 15+).

    Usage:
      warlord

    A single crushing blow that deals 2.0x weapon damage + 20 flat, bypassing
    the target's parry defense and phys_reduction armor. Costs 55 Stamina on fire.
    Fires after a 1-round wind-up.

    Requires: Iron Covenant membership (rank 15+), warlord_strike trained > 0%.
    Must be in active combat.
    """

    key = "warlord"
    aliases = ["warlordstrike"]
    help_category = "Guild"
    locks = "cmd:all()"

    def func(self):
        caller = self.caller
        session = caller.db.combat_session or {}
        if not session.get("target_id"):
            caller.msg("|yYou must be in active combat to use Warlord Strike.|n")
            return

        guild_levels = caller.db.guild_levels or {}
        rank = guild_levels.get("iron_covenant", 0)
        if rank < 15:
            caller.msg(
                f"|yWarlord Strike requires Iron Covenant rank 15 "
                f"(you are rank {rank}).|n"
            )
            return

        guild_skills = caller.db.guild_skills or {}
        war_pct = guild_skills.get("iron_covenant", {}).get("warlord_strike", 0)
        if war_pct <= 0:
            caller.msg(
                "|yYou have not trained Warlord Strike. "
                "Use |wtrain warlord_strike|n to invest XP in it.|n"
            )
            return

        existing = caller.db.queued_technique
        if existing and isinstance(existing, dict):
            ex_name = existing.get("name", "?")
            ex_tr = existing.get("ticks_remaining", 0)
            caller.msg(
                f"|yYou already have {ex_name.replace('_', ' ').title()} queued "
                f"({ex_tr} round(s) until it fires). Wait for it to resolve.|n"
            )
            return

        caller.db.queued_technique = {
            "name": "warlord_strike",
            "ticks_remaining": 1,
        }
        caller.msg(
            "|cYou focus for Warlord Strike.|n  "
            "Fires next round - 2.0x weapon damage + 20 flat, ignores parry and armor."
        )
