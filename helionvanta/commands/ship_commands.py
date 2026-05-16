"""Commands related to the NPC transport ship system."""

from evennia import Command


class CmdShips(Command):
    """
    Show the status of all NPC transport ships on the Helion-Vanta lane.

    Usage:
        ships

    Displays each ship's name, current state (docked or underway), direction,
    and estimated departure time or route progress.

    When a ship is docked at your current port its docking bay will have a
    |wboard|n exit. Type |wboard|n to pay the fare and enter the passenger cabin.
    Type |wgangway|n from inside the cabin to disembark at the current port.
    """

    key = "ships"
    aliases = ["ship"]
    locks = "cmd:all()"
    help_category = "Travel"

    def func(self):
        from evennia import search_tag

        ships = search_tag("npc_ship", category="ship")
        if not ships:
            self.caller.msg("No transit ships are currently active.")
            return

        lines = ["|wHelion — Vanta Transit Lane  |n|x(ship status)|n", ""]
        for ship in sorted(ships, key=lambda s: s.db.ship_name or s.key):
            lines.append("  " + ship.get_status_string())
        lines += [
            "",
            "|xFor passage: go to a docking bay and type |wboard|n|x.|n",
        ]
        self.caller.msg("\n".join(lines))
