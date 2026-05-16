"""Admin/builder commands: mudbuild, resetchar, claimlevels, grantship."""

from __future__ import annotations

from evennia import Command

from commands.cmd_utils import (
    _check_level_up,
    LEVEL_XP_TABLE,
    RESPAWN_DELAY,
    _respawn_mob,
    repop_dead_mobs,
)
from world.mud_bootstrap import build_vertical_slice
from world.corridor_bootstrap import build_corridor


class CmdMudBuild(Command):
    """Build or refresh the Helion-Vanta vertical-slice world.

    Usage:
      mudbuild
    """

    key = "mudbuild"
    locks = "cmd:perm(Builder)"
    help_category = "Admin"

    def func(self):
        force = "reset" in self.args.lower() if self.args else False
        summary = build_vertical_slice(force_reset=force)
        corridor = build_corridor()
        self.caller.msg(
            "World build completed: "
            f"rooms+{summary['rooms_created']} (total {summary['total_rooms']}), "
            f"exits+{summary['exits_created']}, "
            f"npcs+{summary['npcs_created']}, mobs+{summary['mobs_created']}. "
            f"Corridor: sectors+{corridor['sector_rooms_created']}, "
            f"exits+{corridor['exits_created']}, ships+{corridor['ships_created']}."
        )
        # Move caller to the starting room.
        from evennia import search_object
        start = search_object("helion_gate", exact=True)
        if start:
            self.caller.move_to(start[0], quiet=False)
        else:
            self.caller.msg("Warning: helion_gate room not found.")


class CmdResetChar(Command):
    """Hard-reset a character's stats and progression to level-1 defaults.

    Usage:
      resetchar <character>
      resetchar <character> /statsonly

    Without a switch, resets everything: level, XP, stats, skills, attrs,
    equipment - and forces chargen on next login.

    With /statsonly, only the pool maximums and current values are corrected
    to level-correct values (safe to run on an active character without wiping
    their progression).

    Builder permission required.
    """

    key = "resetchar"
    locks = "cmd:perm(Builder)"
    help_category = "Admin"

    def func(self):
        caller = self.caller
        if not self.args:
            caller.msg("Usage: resetchar <character>  or  resetchar <character> /statsonly")
            return

        stats_only = "/statsonly" in self.switches

        target_name = self.args.strip()
        from evennia import search_object
        candidates = search_object(target_name, exact=False)
        target = None
        for c in candidates:
            if hasattr(c, "db") and c.db.hp is not None:
                target = c
                break

        if not target:
            caller.msg(f"Character '{target_name}' not found.")
            return

        if stats_only:
            # Repair pools to level-correct values without touching progression.
            level = target.db.level or 1
            gains = max(0, level - 1)
            target.db.hp_max = 100 + gains * 10 + gains * 3  # base + lvl gain + CON gain
            target.db.hp = target.db.hp_max
            target.db.stamina_max = 100 + gains * 8
            target.db.stamina = target.db.stamina_max
            target.db.shield_max = 100 + gains * 10
            target.db.shield_integrity = target.db.shield_max
            target.db.focus_max = 50 + gains * 5
            target.db.focus = target.db.focus_max
            caller.msg(
                f"[resetchar] Pool maxima corrected for {target.name} at level {level}:\n"
                f"  HP {target.db.hp_max} | Stamina {target.db.stamina_max} "
                f"| Shield {target.db.shield_max} | Focus {target.db.focus_max}"
            )
            if target.has_account and target.sessions.count():
                target.msg(
                    "|y[Admin] Your stat pools have been corrected by staff. "
                    "You are fully restored.|n"
                )
        else:
            # Full wipe - calls _init_stats() and queues chargen.
            target._init_stats()
            target.db.chargen_complete = False
            target.db.background = None
            caller.msg(
                f"[resetchar] {target.name} fully reset to level 1. "
                f"Chargen will run on their next login."
            )
            if target.has_account and target.sessions.count():
                target.msg(
                    "|r[Admin] Your character has been reset to level 1 by staff. "
                    "Please relog to complete character creation.|n"
                )


class CmdClaimLevels(Command):
    """Spend your banked Soul Pool XP to reclaim levels after reincarnation.

    Usage:
      claimlevels             - show soul pool balance and reachable levels
      claimlevels next        - claim one level
      claimlevels <n>         - claim exactly n levels
      claimlevels all         - claim all levels your pool can afford

    Each claimed level applies the full stat gains as if you levelled normally.
    You can stop at any point and save the remaining pool for guild advancement
    or a future reincarnation.
    """

    key = "claimlevels"
    locks = "cmd:all()"
    help_category = "Character"

    def func(self):
        caller = self.caller
        soul_xp = caller.db.soul_xp or 0

        if soul_xp <= 0:
            caller.msg("|yYou have no banked Soul Pool XP. Reincarnate first to build a pool.|n")
            return

        level = caller.db.level or 1
        xp = caller.db.xp or 0
        arg = self.args.strip().lower()

        if not arg:
            # Show status: find highest reachable level.
            max_reach = level
            tmp_xp = xp
            tmp_soul = soul_xp
            for nxt in range(level + 1, max(LEVEL_XP_TABLE) + 2):
                thr = LEVEL_XP_TABLE.get(nxt)
                if thr is None:
                    break
                needed = thr - tmp_xp
                if tmp_soul >= needed:
                    max_reach = nxt
                    tmp_xp = thr
                    tmp_soul -= needed
                else:
                    break
            next_cost = ""
            if level < max(LEVEL_XP_TABLE):
                nxt_thr = LEVEL_XP_TABLE.get(level + 1)
                if nxt_thr:
                    needed = nxt_thr - xp
                    if soul_xp >= needed:
                        next_cost = f"  Next level costs: {needed} XP - |gaffordable|n"
                    else:
                        next_cost = f"  Next level costs: {needed} XP - |r{needed - soul_xp} XP short|n"
            caller.msg(
                f"|cSoul Pool|n\n"
                f"  Banked: {soul_xp} XP\n"
                f"  Current level: {level}  (regular XP: {xp})\n"
                f"  Reachable: up to level |w{max_reach}|n\n"
                f"{next_cost}\n"
                f"Use |wclaimlevels next|n, |wclaimlevels <n>|n, or |wclaimlevels all|n."
            )
            return

        # Parse how many levels to claim.
        if arg == "all":
            n = 999
        elif arg == "next":
            n = 1
        else:
            try:
                n = int(arg)
                if n <= 0:
                    raise ValueError
            except ValueError:
                caller.msg("Usage: claimlevels [next | all | <number>]")
                return

        claimed = 0
        for _ in range(n):
            cur_level = caller.db.level or 1
            nxt_level = cur_level + 1
            threshold = LEVEL_XP_TABLE.get(nxt_level)
            if threshold is None:
                caller.msg("|yYou have reached the maximum level in the table.|n")
                break
            cur_xp = caller.db.xp or 0
            cur_soul = caller.db.soul_xp or 0
            xp_needed = threshold - cur_xp
            if xp_needed > cur_soul:
                caller.msg(
                    f"|yNot enough Soul Pool XP for level {nxt_level} "
                    f"(need {xp_needed}, have {cur_soul}).|n"
                )
                break
            # Transfer XP from soul pool to regular XP, then check level-up.
            caller.db.xp = cur_xp + xp_needed
            caller.db.soul_xp = cur_soul - xp_needed
            level_msgs = _check_level_up(caller)
            for msg in level_msgs:
                caller.msg(msg)
            claimed += 1

        if claimed > 0:
            remaining = caller.db.soul_xp or 0
            caller.msg(
                f"|gClaimed {claimed} level(s). Now level {caller.db.level or 1}. "
                f"Soul Pool remaining: {remaining} XP.|n"
            )


# ---------------------------------------------------------------------------
# CmdGrantShip - builder command to assign a player ship
# ---------------------------------------------------------------------------

class CmdGrantShip(Command):
    """Grant a PlayerShip to a character and dock it in the current bay.

    Usage:
      grantship <character>
      grantship <character> = <ship name>

    You must be standing in a DockingBayRoom (or the ship will default to
    helion_docking_bay).  One ship per character; delete the existing ship
    object before re-granting.

    Builder permission required.
    """

    key = "grantship"
    locks = "cmd:perm(Builder)"
    help_category = "Building"

    def func(self):
        caller = self.caller
        if not self.args:
            caller.msg("Usage: grantship <character> [= <ship name>]")
            return

        raw = self.args.strip()
        if "=" in raw:
            target_name, ship_name = [x.strip() for x in raw.split("=", 1)]
        else:
            target_name = raw
            ship_name = None

        # Locate target character.
        from evennia import search_object

        candidates = search_object(target_name, exact=False)
        target = None
        for c in candidates:
            if c.has_account:
                target = c
                break

        if not target:
            caller.msg(f"Character '{target_name}' not found.")
            return

        # Determine docking bay.
        bay = caller.location
        if not bay or not bay.is_typeclass(
            "typeclasses.rooms.DockingBayRoom", exact=False
        ):
            bay_results = search_object("helion_docking_bay", exact=True)
            if not bay_results:
                caller.msg(
                    "Could not find a docking bay. "
                    "Stand in a DockingBayRoom when running this command."
                )
                return
            bay = bay_results[0]

        # Reject duplicate ships.
        ship_key = f"player_ship_{target.id}"
        existing = search_object(ship_key, exact=True)
        if existing:
            caller.msg(
                f"{target.key} already has a ship "
                f"('{existing[0].db.ship_name}'). Delete it first."
            )
            return

        # Create ship - at_object_creation builds the ShipCabinRoom.
        from evennia import create_object

        ship = create_object(
            "typeclasses.player_ship.PlayerShip",
            key=ship_key,
        )
        ship.db.ship_name = ship_name or f"{target.key}'s Ship"
        ship.db.ship_class = "Light Courier"
        ship.db.owner_id = target.id

        # Dock in bay (opens gangway).
        ship.dock(bay)

        bay_name = bay.db.display_name or bay.key.replace("_", " ").title()
        caller.msg(
            f"|gGranted ship '{ship.db.ship_name}' to {target.key}.|n  "
            f"Docked at {bay_name}. Board key: |w{ship_key}|n"
        )
        target.msg(
            f"|c*** A ship has been assigned to you: |w{ship.db.ship_name}|n.|c ***|n\n"
            f"  Docked at {bay_name}. Board it by typing: |w{ship_key}|n\n"
            f"  Once aboard, use |wlaunch|n to undock and n/s/e/w to navigate."
        )
