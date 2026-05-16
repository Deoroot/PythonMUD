"""
PlayerShip — a player-pilotable ship on The Drift corridor grid.

The ship object moves through SectorRoom and DockingBayRoom objects.
Players ride inside the ShipCabinRoom, which is a separate persistent
room whose description is updated whenever the ship moves.

Boarding:
    In a DockingBayRoom the ship key appears as an exit; walking it
    moves the player into the ShipCabinRoom.  On entry ShipNavCmdSet
    is added automatically (see typeclasses/rooms.py ShipCabinRoom).

Navigation:
    Players type n/s/e/w (or numpad equivalents) → CmdShipMove in
    ShipNavCmdSet delegates to ship.move_in_direction(dir), which
    traverses sector exits while the player stays in the cabin.
"""

from __future__ import annotations

from evennia.objects.objects import DefaultObject


# ---------------------------------------------------------------------------
# OOB helper (module-level to avoid circular imports)
# ---------------------------------------------------------------------------

def _send_sector_oob(player, cabin) -> None:
    """Send a sector_update OOB packet to *player* based on the ship's location."""
    from evennia import search_object

    ship_id = cabin.db.ship_id
    if not ship_id:
        return
    results = search_object(f"#{ship_id}")
    if not results:
        return
    sector = results[0].location
    if not sector:
        return
    player.msg(oob=(
        "sector_update",
        [],
        {
            "room_key":     sector.db.room_key    or sector.key,
            "display_name": sector.db.display_name or sector.key,
            "area":         sector.db.area        or "",
            "planet":       sector.db.planet      or "",
            "room_type":    sector.db.room_type   or "",
        },
    ))


# ---------------------------------------------------------------------------
# Typeclass
# ---------------------------------------------------------------------------

class PlayerShip(DefaultObject):
    """
    A player-owned and player-piloted ship on the Helion-Vanta lane.

    Persistent db attributes
    ------------------------
    ship_name       str   display name shown to players
    ship_class      str   e.g. "Light Courier"
    owner_id        int   id of the owning Character
    state           str   "docked" | "underway"
    gangway_exits   list  [out_dbref, in_dbref] of open gangway Exits
    cabin_key       str   key of the persistent ShipCabinRoom object
    """

    # ------------------------------------------------------------------
    # Creation
    # ------------------------------------------------------------------

    def at_object_creation(self):
        self.db.ship_name = "Unnamed Vessel"
        self.db.ship_class = "Light Courier"
        self.db.owner_id = None
        self.db.state = "docked"
        self.db.gangway_exits = []
        self.db.cabin_key = None

        self.tags.add("player_ship", category="ship")

        # Create the persistent ShipCabinRoom (no location — floats in limbo).
        from evennia import create_object

        cabin = create_object(
            "typeclasses.rooms.ShipCabinRoom",
            key=f"{self.key}_cabin",
        )
        cabin.db.display_name = "Ship Helm"
        cabin.db.room_key = f"{self.key}_cabin"
        cabin.db.desc = (
            "The helm of your ship. Viewports show open space beyond the hull. "
            "Navigation controls line the forward console. "
            "Use n/s/e/w to navigate, |wlaunch|n to undock, |wdock|n to dock manually."
        )
        cabin.db.ship_id = self.id
        self.db.cabin_key = cabin.key

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def get_cabin(self):
        """Return the ShipCabinRoom, or None if missing."""
        from evennia import search_object

        if not self.db.cabin_key:
            return None
        results = search_object(self.db.cabin_key, exact=True)
        return results[0] if results else None

    # ------------------------------------------------------------------
    # Docking / undocking
    # ------------------------------------------------------------------

    def dock(self, bay):
        """Place ship in bay, set state=docked, open boarding exits."""
        self.location = bay
        self.db.state = "docked"
        self._open_gangway(bay)
        self._update_cabin_status(bay)

    def undock(self):
        """Close gangways and set state=underway."""
        self._close_gangway()
        self.db.state = "underway"
        cabin = self.get_cabin()
        if cabin:
            cabin.msg_contents(
                "|cHelm:|n Gangway sealed. Engines online. "
                "Use n/s/e/w to navigate."
            )

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    def move_in_direction(self, direction: str):
        """Move ship one step in *direction* through sector exits."""
        current = self.location
        if not current:
            return

        # Find matching exit.
        target = None
        for ex in current.exits:
            if ex.key.lower() == direction.lower():
                target = ex.destination
                break

        cabin = self.get_cabin()

        if target is None:
            if cabin:
                cabin.msg_contents(
                    f"|yHelm:|n No navigable exit to the {direction}."
                )
            return

        # Move ship object.
        self.location = target

        # Auto-dock when entering a DockingBayRoom.
        if target.is_typeclass("typeclasses.rooms.DockingBayRoom", exact=False):
            self.dock(target)
            bay_name = (
                target.db.display_name
                or target.key.replace("_", " ").title()
            )
            if cabin:
                cabin.msg_contents(
                    f"|cHelm:|n Docking at |w{bay_name}|n. "
                    "Gangway open. Use |wlaunch|n to undock."
                )
            return

        # Update cabin status and notify all occupants.
        self._update_cabin_status(target)
        if cabin:
            sector_name = (
                target.db.display_name
                or target.key.replace("_", " ").title()
            )
            cabin.msg_contents(f"|cHelm:|n Sector — |w{sector_name}|n.")
            for obj in cabin.contents:
                if obj.has_account:
                    _send_sector_oob(obj, cabin)

    # ------------------------------------------------------------------
    # Gangway management
    # ------------------------------------------------------------------

    def _open_gangway(self, bay):
        """Create boarding exits between bay and cabin (idempotent)."""
        # Always close stale exits first.
        self._close_gangway()

        cabin = self.get_cabin()
        if not cabin:
            return

        from evennia import create_object

        # cabin → bay  (free disembark exit)
        gangway_out = create_object(
            "typeclasses.exits.Exit",
            key="disembark",
            location=cabin,
            destination=bay,
        )
        gangway_out.db.desc = "The gangway leads out to the docking bay."

        # bay → cabin  (free boarding exit; key = ship key so it is unique)
        gangway_in = create_object(
            "typeclasses.exits.Exit",
            key=self.key,
            location=bay,
            destination=cabin,
        )
        ship_name = self.db.ship_name or self.key
        gangway_in.db.desc = f"Board the {ship_name}."

        self.db.gangway_exits = [gangway_out.dbref, gangway_in.dbref]

        bay_name = bay.db.display_name or bay.key.replace("_", " ").title()
        bay.msg_contents(
            f"|c{ship_name}|n is docked. Board with: |w{self.key}|n"
        )

    def _close_gangway(self):
        """Delete both gangway exits. Safe to call when none are open."""
        from evennia import search_object

        for dbref in self.db.gangway_exits or []:
            results = search_object(dbref, exact=True)
            if results:
                results[0].delete()
        self.db.gangway_exits = []

    # ------------------------------------------------------------------
    # Cabin status
    # ------------------------------------------------------------------

    def _update_cabin_status(self, current_location):
        """Refresh cabin desc with current location info."""
        cabin = self.get_cabin()
        if not cabin:
            return
        ship_name = self.db.ship_name or "Your Ship"
        loc_name = (
            current_location.db.display_name
            or current_location.key.replace("_", " ").title()
        )
        state = self.db.state or "underway"
        if state == "docked":
            status_str = f"docked at |w{loc_name}|n"
        else:
            status_str = f"sector |w{loc_name}|n"
        cabin.db.desc = (
            f"The helm of the |w{ship_name}|n. "
            f"Viewports show open space beyond the hull. "
            f"Navigation console: {status_str}. "
            f"Use n/s/e/w to navigate, |wlaunch|n to undock, |wdock|n to dock."
        )

    # ------------------------------------------------------------------
    # Status string
    # ------------------------------------------------------------------

    def get_status_string(self) -> str:
        ship_name = self.db.ship_name or self.key
        ship_class = self.db.ship_class or "Unknown Class"
        state = self.db.state or "unknown"
        loc = self.location
        loc_name = ""
        if loc:
            loc_name = (
                loc.db.display_name
                or loc.key.replace("_", " ").title()
            )
        owner_id = self.db.owner_id
        owner_str = ""
        if owner_id:
            from evennia import search_object
            results = search_object(f"#{owner_id}")
            if results:
                owner_str = f"  Owner: {results[0].key}"

        if state == "docked":
            state_str = f"|gdocked|n at {loc_name}"
        else:
            state_str = f"|yunderway|n — {loc_name}"

        return (
            f"|c{ship_name}|n  ({ship_class}){owner_str}\n"
            f"  Status: {state_str}"
        )
