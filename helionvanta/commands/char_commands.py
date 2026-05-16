"""Character reset and reincarnation commands."""

from __future__ import annotations

from evennia import Command

from commands.cmd_utils import LEVEL_XP_TABLE


# ---------------------------------------------------------------------------
# Reincarnation constants
# ---------------------------------------------------------------------------

# Rooms that host a Soul Archive NPC.  Builders can also set db.has_soul_archive
# = True on any room to add an archive location without touching this list.
_SOUL_ARCHIVE_ROOMS: frozenset[str] = frozenset({"helion_gate", "vanta_customs"})

# Credit fee formula: base + (level-1)*per_level + reincarnations*per_life
_REINCARNATION_BASE_FEE: int = 500
_REINCARNATION_PER_LEVEL: int = 100
_REINCARNATION_PER_LIFE: int = 500

# Skill-point bonus per reincarnation, capped.
_REINCARNATION_SKILL_BONUS: int = 2
_REINCARNATION_SKILL_BONUS_CAP: int = 10


def _reincarnation_fee(level: int, reincarnations: int) -> int:
    """Return the credit cost to reincarnate at the given level and past-life count."""
    return (
        _REINCARNATION_BASE_FEE
        + (level - 1) * _REINCARNATION_PER_LEVEL
        + reincarnations * _REINCARNATION_PER_LIFE
    )


def _do_character_reset(caller, *, preserve_soul: bool = False) -> None:
    """Reset a character to level-1 defaults.

    Always preserved: ``db.ledger`` (credits + inventory items).
    If *preserve_soul* is True: ``db.soul_xp`` and ``db.reincarnations`` are
    also preserved (set by caller before or after this function as needed).

    Guild state (guild_levels, free_levels, guild_skills) is always wiped so
    the player can choose a new guild path through chargen.
    """
    # _init_stats() resets hp/stamina/focus/shield/xp/level/skills/attrs/
    # chargen but intentionally does NOT touch ledger, soul_xp, reincarnations,
    # or guild fields \u2014 so we reset guild fields explicitly here.
    caller._init_stats()
    caller.db.guild_levels = {}
    caller.db.free_levels = 0
    caller.db.guild_skills = {}
    caller.db.guild_passives_applied = {}
    caller.db.psi_ward = 0
    if not preserve_soul:
        caller.db.soul_xp = 0
        caller.db.reincarnations = 0


class CmdRecreate(Command):
    """Wipe your character and start fresh from character creation.

    Usage:
      recreate
      recreate confirm

    Available only if you have less than 15,000 XP (below the level-10
    threshold).  If you are at or above that point, seek a Soul Archive
    in Helion Gate or Vanta Customs to reincarnate instead.

    What is preserved:  credits, inventory items.
    What is lost:       level, XP, all skills, attributes, guild progress.

    Your character name stays tied to your account.  Type |wrecreate confirm|n
    to proceed \u2014 there is no undo.
    """

    key = "recreate"
    locks = "cmd:all()"
    help_category = "Character"

    def func(self):
        caller = self.caller
        xp = caller.db.xp or 0
        threshold = LEVEL_XP_TABLE.get(10, 15_000)

        if xp >= threshold:
            caller.msg(
                "|yYou have too much experience to recreate freely. "
                "Seek a Soul Archive (Helion Gate or Vanta Customs) to reincarnate instead.|n"
            )
            return

        if self.args.strip().lower() != "confirm":
            level = caller.db.level or 1
            ledger = caller.db.ledger or {}
            credits = ledger.get("credits", 0)
            n_items = len(ledger.get("inventory", []))
            caller.msg(
                f"|yRECREATE WARNING|n\n"
                f"This will reset your character to level 1 and restart chargen.\n"
                f"  Level {level} | {xp} XP \u2014 permanently lost.\n"
                f"  Skills, attributes, and guild progress \u2014 permanently lost.\n"
                f"  Credits ({credits} cr) and {n_items} inventory item(s) \u2014 kept.\n\n"
                f"Type |wrecreate confirm|n to proceed, or do nothing to cancel."
            )
            return

        _do_character_reset(caller, preserve_soul=False)
        caller.msg(
            "|gCharacter reset. Relog to begin character creation from scratch.|n"
        )


class CmdReincarnate(Command):
    """Be reborn through the Soul Archive \u2014 preserve your earned wealth and items.

    Usage:
      reincarnate
      reincarnate confirm

    You must be standing at a Soul Archive (Helion Gate or Vanta Customs).
    A credit fee is charged that scales with your current level and how many
    times you have reincarnated before.

    Your XP is banked into a Soul Pool.  After chargen is complete, use
    |wclaimlevels|n to spend that pool and reclaim your levels one at a time.

    What is preserved:  credits (minus fee), all inventory items, Soul Pool XP.
    What is reset:      level, skills, attributes, guild progress.
    Bonus:              +2 starting skill points per past reincarnation (max 10).
    """

    key = "reincarnate"
    locks = "cmd:all()"
    help_category = "Character"

    def func(self):
        caller = self.caller

        # Location check.
        room = caller.location
        room_key = (room.db.room_key if room else "") or ""
        has_archive = room_key in _SOUL_ARCHIVE_ROOMS or bool(
            room and room.db.has_soul_archive
        )
        if not has_archive:
            caller.msg(
                "|yYou must be at a Soul Archive to reincarnate.\n"
                "Seek one at Helion Gate or Vanta Customs.|n"
            )
            return

        xp = caller.db.xp or 0
        level = caller.db.level or 1
        reincarnations = caller.db.reincarnations or 0
        fee = _reincarnation_fee(level, reincarnations)
        ledger = caller.db.ledger or {}
        credits = ledger.get("credits", 0)
        n_items = len(ledger.get("inventory", []))
        # Bank at least the XP threshold for the current level so that XP
        # spent on guild skill training never silently reduces the soul pool
        # below what the player earned through leveling.
        xp_to_bank = max(xp, LEVEL_XP_TABLE.get(level, 0))
        new_soul_xp = (caller.db.soul_xp or 0) + xp_to_bank
        skill_bonus = min(
            (reincarnations + 1) * _REINCARNATION_SKILL_BONUS,
            _REINCARNATION_SKILL_BONUS_CAP,
        )

        if self.args.strip().lower() != "confirm":
            affordable = "|g(affordable)|n" if credits >= fee else "|r(insufficient funds)|n"
            caller.msg(
                f"|cSOUL ARCHIVE \u2014 REINCARNATION|n\n"
                f"The keeper intones: 'Death is not the end. Only the terms must be settled.'\n\n"
                f"  Current level: {level}  |  XP: {xp}  |  Reincarnations: {reincarnations}\n"
                f"  Fee: |y{fee} credits|n  {affordable}  (balance: {credits} cr)\n\n"
                f"  After reincarnation:\n"
                f"    Soul Pool: {new_soul_xp} XP  (spend with 'claimlevels' after chargen)\n"
                f"    Credits remaining: {credits - fee} cr\n"
                f"    Inventory ({n_items} item(s)): preserved\n"
                f"    Starting skill point bonus: +{skill_bonus}\n\n"
                f"Type |wreincarnate confirm|n to proceed, or do nothing to cancel."
            )
            return

        if credits < fee:
            caller.msg(
                f"|rYou cannot afford the reincarnation fee "
                f"({fee} cr required, {credits} cr available).|n"
            )
            return

        # Deduct fee and save updated ledger.
        new_ledger = dict(ledger)
        new_ledger["credits"] = credits - fee

        # Bank XP into soul pool before resetting.
        banked_soul_xp = (caller.db.soul_xp or 0) + xp_to_bank
        new_reincarnations = reincarnations + 1

        # Full reset (preserving soul fields so we can restore them).
        _do_character_reset(caller, preserve_soul=True)

        # Restore soul fields and ledger.
        caller.db.soul_xp = banked_soul_xp
        caller.db.reincarnations = new_reincarnations
        caller.db.ledger = new_ledger

        # Apply skill-point bonus (overrides _init_stats reset to 0).
        caller.db.skill_points = skill_bonus

        caller.msg(
            f"|g*** Soul Archive \u2014 Reincarnation complete. ***|n\n"
            f"Soul Pool: |w{banked_soul_xp} XP|n banked.\n"
            f"Reincarnation #{new_reincarnations}.  Skill bonus: +{skill_bonus} starting points.\n"
            f"Use |wclaimlevels|n after chargen to reclaim your levels.\n"
            f"Relog to begin character creation."
        )
