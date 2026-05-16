"""
ShipNavCmdSet — navigation commands active while a player is aboard a PlayerShip.

Added/removed automatically by ShipCabinRoom.at_object_receive / at_object_leave.
Priority 10, Union merge: overrides the standard CmdMoveAlias direction keys so
that n/s/e/w (and numpad equivalents) move the ship rather than the player.

Commands
--------
CmdShipMove     n/s/e/w + numpad 1-4/6-9 → ship.move_in_direction()
CmdShipLaunch   launch / undock          → ship.undock()
CmdShipDock     dock                     → ship.dock(current_bay)
CmdShipStatus   helm / shipstatus        → ship.get_status_string()
"""

from __future__ import annotations

from evennia import CmdSet
from evennia.commands.command import Command

# ---------------------------------------------------------------------------
# Direction resolution helpers
# ---------------------------------------------------------------------------

_NUMPAD_TO_DIR: dict[str, str] = {
    "1": "southwest",
    "2": "south",
    "3": "southeast",
    "4": "west",
    "6": "east",
    "7": "northwest",
    "8": "north",
    "9": "northeast",
}

_SHORT_TO_DIR: dict[str, str] = {
    "n":  "north",
    "s":  "south",
    "e":  "east",
    "w":  "west",
    "ne": "northeast",
    "nw": "northwest",
    "se": "southeast",
    "sw": "southwest",
}


def _resolve_direction(cmdstring: str) -> str:
    """Map short / numpad key to full compass direction name."""
    s = cmdstring.lower()
    return _NUMPAD_TO_DIR.get(s) or _SHORT_TO_DIR.get(s) or s


def _get_ship(caller):
    """Return the PlayerShip whose cabin the caller is in, or None."""
    cabin = caller.location
    if not cabin:
        return None
    ship_id = cabin.db.ship_id
    if not ship_id:
        return None
    from evennia import search_object
    results = search_object(f"#{ship_id}")
    return results[0] if results else None


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

class CmdShipMove(Command):
    """
    Navigate the ship one sector in a compass direction.

    Usage:
      n / north / 8     — north
      s / south / 2     — south
      e / east  / 6     — east
      w / west  / 4     — west
      nw/7  ne/9  sw/1  se/3 — diagonals (sector grid may not have these exits)

    The ship is docked — type |wlaunch|n first to undock.
    """

    key = "north"
    aliases = [
        "n", "south", "s", "east", "e", "west", "w",
        "northeast", "ne", "northwest", "nw",
        "southeast", "se", "southwest", "sw",
        "1", "2", "3", "4", "6", "7", "8", "9",
    ]
    locks = "cmd:all()"
    help_category = "Ship Navigation"

    def func(self):
        ship = _get_ship(self.caller)
        if not ship:
            self.caller.msg("You are not aboard a ship.")
            return

        if ship.db.state == "docked":
            self.caller.msg(
                "|yThe ship is docked. Use |wlaunch|n to undock before navigating.|n"
            )
            return

        direction = _resolve_direction(self.cmdstring)
        ship.move_in_direction(direction)


class CmdShipLaunch(Command):
    """
    Undock the ship and prepare for navigation.

    Usage:
      launch
      undock

    The ship must be docked in a docking bay. Once launched, use n/s/e/w
    to move through sectors. Use |wdock|n to manually dock when in a bay.
    """

    key = "launch"
    aliases = ["undock"]
    locks = "cmd:all()"
    help_category = "Ship Navigation"

    def func(self):
        ship = _get_ship(self.caller)
        if not ship:
            self.caller.msg("You are not aboard a ship.")
            return

        if ship.db.state == "underway":
            self.caller.msg("|yThe ship is already underway.|n")
            return

        # Verify there are navigable exits from the bay.
        bay = ship.location
        nav_exits = [ex for ex in (bay.exits if bay else [])]
        if not nav_exits:
            self.caller.msg(
                "|yNo exits available from this bay. Cannot undock.|n"
            )
            return

        ship.undock()
        self.caller.msg(
            "|gEngines online. Navigation ready.|n  "
            "Use n/s/e/w to move. |wdock|n to dock at a bay."
        )


class CmdShipDock(Command):
    """
    Manually dock the ship in the current docking bay.

    Usage:
      dock

    The ship must already be physically located in a DockingBayRoom
    (i.e. you navigated here and it auto-approached). Docking opens
    the gangway so other players can board.  Use |wlaunch|n to undock.
    """

    key = "dock"
    locks = "cmd:all()"
    help_category = "Ship Navigation"

    def func(self):
        ship = _get_ship(self.caller)
        if not ship:
            self.caller.msg("You are not aboard a ship.")
            return

        if ship.db.state == "docked":
            self.caller.msg("|yAlready docked.|n")
            return

        bay = ship.location
        if not bay or not bay.is_typeclass(
            "typeclasses.rooms.DockingBayRoom", exact=False
        ):
            self.caller.msg(
                "|yYou can only dock in a docking bay. "
                "Navigate to one first (the ship will auto-dock on entry).|n"
            )
            return

        ship.dock(bay)
        self.caller.msg("|gDocked. Gangway open. Use |wlaunch|n to undock.|n")


class CmdShipStatus(Command):
    """
    Display status information for your current ship.

    Usage:
      helm
      shipstatus
    """

    key = "helm"
    aliases = ["shipstatus", "shipstat"]
    locks = "cmd:all()"
    help_category = "Ship Navigation"

    def func(self):
        ship = _get_ship(self.caller)
        if not ship:
            self.caller.msg("You are not aboard a ship.")
            return
        self.caller.msg(ship.get_status_string())


# ---------------------------------------------------------------------------
# CmdSet
# ---------------------------------------------------------------------------

class ShipNavCmdSet(CmdSet):
    """
    Navigation commands available while inside a PlayerShip cabin.

    Priority 10, Union merge — overrides the default CmdMoveAlias direction
    keys so that n/s/e/w move the ship instead of the player character.
    """

    key = "ShipNavCmdSet"
    priority = 10
    mergetype = "Union"

    def at_cmdset_creation(self):
        self.add(CmdShipMove())
        self.add(CmdShipLaunch())
        self.add(CmdShipDock())
        self.add(CmdShipStatus())
