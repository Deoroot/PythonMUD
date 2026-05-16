"""Quest board, task journal, travel, and map commands."""

from __future__ import annotations

from evennia import Command, search_object

from world.runtime_state import get_shuttle_machine, normalize_destination

from commands.cmd_utils import (
    _pretty_name,
    _get_quest_state,
    _update_location_objectives,
    _is_quest_complete,
    _format_quest_progress,
    _accept_contract,
    _turnin_contract,
    _quest_by_key,
    _resolve_quest_alias,
    _send_room_oob,
    _quests,
    _SETUP_DEFERREDS,
    _SLEEP_DEFERREDS,
)


class CmdQuest(Command):
    """Quest board and contract management.

    Usage:
      quest
      quest accept <key|intro|vanta>
      quest progress
      quest turnin <key|intro|vanta>
    """

    key = "quest"
    aliases = ["q"]
    help_category = "General"

    def func(self):
        _update_location_objectives(self.caller)
        args = self.args.strip()
        if not args:
            self._show_board()
            return

        parts = args.split(maxsplit=1)
        cmd = parts[0].lower()
        value = parts[1].strip().lower() if len(parts) > 1 else ""

        if cmd in {"accept", "take", "start"}:
            self._accept_quest(value)
            return

        if cmd in {"progress", "log", "journal"}:
            self._show_progress()
            return

        if cmd in {"turnin", "complete", "report"}:
            self._turnin_quest(value)
            return

        self.caller.msg("Usage: quest | quest accept <key> | quest progress | quest turnin <key>")

    def _show_board(self):
        quest_defs = _quests.QUEST_DEFS
        if not quest_defs:
            self.caller.msg("No quest contracts available.")
            return

        state = _get_quest_state(self.caller)
        active = state.get("active", {})
        completed = set(state.get("completed", []))

        active_lines = []
        available_lines = []
        done_lines = []

        for key, qst in quest_defs.items():
            name = qst["name"]
            if key in completed:
                done_lines.append(f"  |x[done]|n  {name}")
            elif key in active:
                prog = active[key]
                active_lines.append(f"\n|w{name}|n  |y[in progress]|n")
                active_lines.extend(_format_quest_progress(key, prog))
            else:
                requires = qst.get("requires", [])
                missing = [r for r in requires if r not in completed]
                if missing:
                    req_names = ", ".join(_pretty_name(r) for r in missing)
                    available_lines.append(f"  |x[locked]|n  {name}  (requires: {req_names})")
                else:
                    available_lines.append(f"  [available]  {name}")

        lines = ["|wContract Board|n"]
        if active_lines:
            lines.append("|yActive:|n")
            lines.extend(active_lines)
        if available_lines:
            lines.append("|wAvailable:|n")
            lines.extend(available_lines)
        if done_lines:
            lines.append("|xCompleted:|n")
            lines.extend(done_lines)

        lines.append("\nUse |wquest progress|n for full details, |wquest turnin <key>|n to hand in.")
        self.caller.msg("\n".join(lines))

    def _accept_quest(self, raw_key: str):
        if not raw_key:
            self.caller.msg("Usage: quest accept <key|intro|vanta>")
            return

        quest_key = _resolve_quest_alias(raw_key)
        if not quest_key:
            self.caller.msg("Unknown quest key.")
            return

        _, message = _accept_contract(self.caller, quest_key, require_start_room=True)
        self.caller.msg(message)

    def _show_progress(self):
        state = _get_quest_state(self.caller)
        active = state.get("active", {})
        if not active:
            self.caller.msg("No active contracts. Use 'quest' to view the board.")
            return

        lines = ["|wActive Contracts|n"]
        for key, prog in active.items():
            quest = _quest_by_key(key)
            name = quest["name"] if quest else _pretty_name(key)
            complete = _is_quest_complete(self.caller, key)
            status = "  |g[ready to turn in]|n" if complete else ""
            lines.append(f"\n|w{name}|n{status}")
            lines.extend(_format_quest_progress(key, prog))

        lines.append("\nUse |wquest turnin <key>|n when objectives are complete.")
        self.caller.msg("\n".join(lines))

    def _turnin_quest(self, raw_key: str):
        if not raw_key:
            self.caller.msg("Usage: quest turnin <key|intro|vanta>")
            return

        quest_key = _resolve_quest_alias(raw_key)
        if not quest_key:
            self.caller.msg("Unknown quest key.")
            return

        _, message = _turnin_contract(self.caller, quest_key, require_giver_room=True)
        self.caller.msg(message)


class CmdTasks(Command):
    """Show your active quest objectives (quest journal).

    Usage:
      tasks
      journal
      log

    Displays all currently active contracts with per-objective progress.
    Use 'quest' to see the full board including available and completed quests.
    """

    key = "tasks"
    aliases = ["journal", "log", "quests", "contracts"]
    help_category = "General"

    def func(self):
        _update_location_objectives(self.caller)
        state = _get_quest_state(self.caller)
        active = state.get("active", {})

        if not active:
            self.caller.msg(
                "You have no active contracts.\n"
                "Use |wquest|n to view the board and pick one up."
            )
            return

        lines = ["|wActive Contracts|n"]
        for key, prog in active.items():
            quest = _quest_by_key(key)
            name = quest["name"] if quest else _pretty_name(key)
            complete = _is_quest_complete(self.caller, key)
            status = "  |g[ready to turn in]|n" if complete else ""
            lines.append(f"\n|w{name}|n{status}")
            lines.extend(_format_quest_progress(key, prog))

        lines.append("\nUse |wquest turnin <key>|n when objectives are complete.")
        self.caller.msg("\n".join(lines))


class CmdTravel(Command):
    """Travel between Helion and Vanta via shuttle.

    Usage:
      travel <helion|vanta>
      board              (auto-selects opposite destination from dock)
      dock               (same as board)
    """

    key = "travel"
    aliases = ["tr", "board", "dock"]
    help_category = "General"

    SHUTTLE_ROOM_KEYS = {
        "shuttle_airlock",
        "shuttle_cargo",
        "shuttle_lounge",
        "shuttle_observation",
    }

    PORT_ROOM_KEYS = {"helion_shuttle_dock", "vanta_shuttle_dock"}

    _PORT_OPPOSITE = {
        "helion_shuttle_dock": "vanta_shuttle_dock",
        "vanta_shuttle_dock": "helion_shuttle_dock",
    }

    def func(self):
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
            self.caller.msg("You wake up and prepare for travel.")

        # Auto-derive destination when invoked as 'board' / 'dock' with no args,
        # or when 'travel' is used without arguments.
        if not self.args:
            room = self.caller.location
            room_key = (room.db.room_key or room.key) if room else ""
            if room_key in self.PORT_ROOM_KEYS:
                opposite = self._PORT_OPPOSITE[room_key]
                # e.g. "helion_shuttle_dock" -> "helion"
                self.args = opposite.replace("_shuttle_dock", "")
            elif room_key in self.SHUTTLE_ROOM_KEYS:
                self.caller.msg(
                    "The shuttle is already in transit or docked. "
                    "Use 'travel <helion|vanta>' to choose your destination."
                )
                return
            else:
                self.caller.msg(
                    "You must be at a shuttle dock to board. "
                    "Head to the Shuttle Dock and use 'board' or 'travel <helion|vanta>'."
                )
                return

        destination = normalize_destination(self.args)
        if not destination:
            self.caller.msg("Unknown destination. Use 'helion' or 'vanta'.")
            return

        room = self.caller.location
        if not room:
            self.caller.msg("You are not in a valid location for travel.")
            return

        room_key = room.db.room_key or room.key
        if room_key not in (self.SHUTTLE_ROOM_KEYS | self.PORT_ROOM_KEYS):
            self.caller.msg("You must be at a shuttle dock or onboard the shuttle.")
            return

        # Update active quest objective when boarding from Helion dock.
        state = _get_quest_state(self.caller)
        vanta_prog = state.get("active", {}).get("vanta_expedition_artifact_recovery")
        if vanta_prog and room_key == "helion_shuttle_dock":
            vanta_prog["boarded_shuttle"] = True
            self.caller.db.quest_state = state

        machine = get_shuttle_machine()
        if destination == machine.current_port:
            self.caller.msg("Shuttle already docked at that destination.")
            return

        # Move caller onboard if they are currently at dock.
        if room_key in self.PORT_ROOM_KEYS:
            airlock = search_object("shuttle_airlock", exact=True)
            if not airlock:
                self.caller.msg("Shuttle airlock unavailable. Run mudbuild first.")
                return
            self.caller.move_to(airlock[0], quiet=True)
            machine.board(self.caller.key)

        machine.destination_port = destination
        if machine.state == "docked":
            machine.begin_boarding()
        machine.depart()

        # Move all characters currently onboard shuttle rooms.
        destination_room = search_object(destination, exact=True)
        if not destination_room:
            self.caller.msg("Destination dock not found. Run mudbuild first.")
            return

        onboard = []
        for shuttle_room_key in self.SHUTTLE_ROOM_KEYS:
            found = search_object(shuttle_room_key, exact=True)
            if not found:
                continue
            for obj in found[0].contents:
                if obj.has_account:
                    onboard.append(obj)

        machine.arrive()
        for obj in onboard:
            obj.move_to(destination_room[0], quiet=True)
            obj.msg(f"The shuttle docks at {destination}. Airlock cycles open.")
            _send_room_oob(obj)

            # Update active travel objectives for all onboard players.
            qstate = _get_quest_state(obj)
            vprog = qstate.get("active", {}).get("vanta_expedition_artifact_recovery")
            if vprog:
                if destination == "vanta_shuttle_dock":
                    vprog["arrived_vanta"] = True
                if destination == "helion_shuttle_dock":
                    vprog["returned_helion"] = True
                obj.db.quest_state = qstate

        machine.reset_docked()

        # Keep shuttle dynamic dock exit synchronized with current port.
        airlock = search_object("shuttle_airlock", exact=True)
        if airlock:
            for ex in airlock[0].exits:
                if ex.key == "dock":
                    ex.destination = destination_room[0]

        self.caller.msg(f"Transit complete. Current route: {machine.route_label()}")


class CmdMap(Command):
    """Show a compass map of adjacent rooms.

    Usage: map

    Displays the current room plus each immediately adjacent room in the
    eight compass directions (N/S/E/W/Up/Down).  Room names are capped at
    18 characters; longer names are truncated with a tilde (~).
    """

    key = "map"
    help_category = "Navigation"
    locks = "cmd:all()"

    _DIRS = {"north", "south", "east", "west", "up", "down"}
    _CELL = 22   # visual width of every cell (including brackets)
    _NW   = 18   # max room-name characters before truncating

    # ------------------------------------------------------------------
    def _label(self, room, highlight: bool = False) -> str:
        """Return a padded, fixed-visual-width label for *room*.

        The returned string is always *self._CELL* visible characters wide
        so that compass alignment stays consistent regardless of colour codes.
        """
        name = (getattr(room.db, "display_name", None) or room.key)
        if len(name) > self._NW:
            name = name[: self._NW - 1] + "~"
        raw_bracket = f"[{name}]"
        pad   = self._CELL - len(raw_bracket)
        lp    = pad // 2
        rp    = pad - lp
        inner = f"|w{raw_bracket}|n" if highlight else raw_bracket
        return " " * lp + inner + " " * rp

    def _blank(self) -> str:
        return " " * self._CELL

    # ------------------------------------------------------------------
    def func(self):
        loc = self.caller.location
        if not loc:
            self.caller.msg("You are nowhere.")
            return

        # Collect exits (cardinal + vertical only).
        ex_map: dict[str, object] = {}
        for ex in loc.exits:
            d = ex.key.lower()
            if d in self._DIRS:
                ex_map[d] = ex.destination

        def cell(d: str) -> str:
            return self._label(ex_map[d]) if d in ex_map else self._blank()

        here = self._label(loc, highlight=True)
        C = self._CELL  # shorthand

        # Horizontal connectors \u2014 visible only when the exit exists.
        lc = "---" if "west"  in ex_map else "   "
        rc = "---" if "east"  in ex_map else "   "
        vn = "|"   if "north" in ex_map else " "
        vs = "|"   if "south" in ex_map else " "

        # Indent so north/south cells sit centred above/below "here".
        # Layout:  [west C] [lc 3] [here C] [rc 3] [east C]
        #           ^ = 0            ^ = C+3
        I   = C + 3          # left edge of "here" in the mid row
        mid = I + C // 2     # centre column (for the vert connectors)

        loc_name = getattr(loc.db, "display_name", None) or loc.key

        rows = [
            f"|c[ MAP ]|n  {loc_name}",
            "",
            " " * I + cell("north"),
            " " * mid + vn,
            cell("west") + lc + here + rc + cell("east"),
            " " * mid + vs,
            " " * I + cell("south"),
        ]

        if "up" in ex_map or "down" in ex_map:
            up_l = self._label(ex_map["up"]).strip()   if "up"   in ex_map else "(none)"
            dn_l = self._label(ex_map["down"]).strip() if "down" in ex_map else "(none)"
            rows += ["", f"  up: {up_l}    down: {dn_l}"]

        self.caller.msg("\n".join(r.rstrip() for r in rows))
