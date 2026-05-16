"""
NpcTransportShip — autonomous colonial transport traversing The Shardfield.

Each ship owns a persistent Cabin Room that players occupy while in transit.
When underway the ship object lives in the overworld_kael_cluster room and
db.grid_pos tracks its cell in the unified 80×32 grid (y=20 tradelane row).
When docked the ship object moves to the docking bay room and db.grid_pos=None.

Ticker pattern  (persistent, SHIP_TICK_INTERVAL seconds):
    Docked:   count down dock_ticks_remaining; when 0 close gangway & depart.
    Underway: advance one grid cell per tick along SHIP_GRID_ROUTE; if endpoint
              → move to docking bay, open gangway.

Grid route (y=20 tradelane):
    index  0 — [32, 20]  Helion side  → docks at helion_docking_bay
    index  7 — [39, 20]  Waystation Kael PA announcement
    index 15 — [47, 20]  Vanta side   → docks at vanta_docking_bay
    Ships ping-pong: direction = +1 (→ Vanta) or -1 (→ Helion).
"""

from __future__ import annotations

from evennia.objects.objects import DefaultObject

# ---------------------------------------------------------------------------
# Route constants (shared with corridor_bootstrap so imported from here)
# ---------------------------------------------------------------------------

SHIP_TICK_INTERVAL: int = 40   # seconds per sector / tick
DOCK_TICKS: int = 3            # ticks spent docked  (3 × 40 s = 120 s ≈ 2 min)

SHIP_ROUTE: list[str] = [
    "helion_docking_bay",      # index  0 — Helion port
    "drift_helion_outer",      # index  1
    "drift_corridor_alpha",    # index  2
    "drift_corridor_beta",     # index  3
    "drift_belt_alpha",        # index  4
    "drift_waystation_kael",   # index  5 — scenic mid-point
    "drift_belt_beta",         # index  6
    "drift_corridor_gamma",    # index  7
    "drift_corridor_delta",    # index  8
    "drift_vanta_outer",       # index  9
    "vanta_docking_bay",       # index 10 — Vanta port
]

# ---------------------------------------------------------------------------
# Grid route — 16 cells along the y=20 tradelane of the unified 80×32 grid.
# Replaces SHIP_ROUTE for actual tick movement; SHIP_ROUTE kept for compat.
# ---------------------------------------------------------------------------

SHIP_GRID_ROUTE: list[list[int]] = [[x, 20] for x in range(32, 48)]

_ENDPOINT_INDICES: frozenset[int] = frozenset({0, len(SHIP_GRID_ROUTE) - 1})


# ---------------------------------------------------------------------------
# Top-level ticker callback
# MUST be a module-level function so Evennia can re-import it by path after
# a server reload.
# ---------------------------------------------------------------------------

def _ship_tick(*args, **kwargs):
    """Called by TICKER_HANDLER every SHIP_TICK_INTERVAL seconds."""
    from evennia import search_object

    ship_id = kwargs.get("ship_id")
    if ship_id is None:
        return
    results = search_object(f"#{ship_id}")
    if not results:
        return
    results[0].tick()


# ---------------------------------------------------------------------------
# Typeclass
# ---------------------------------------------------------------------------

class NpcTransportShip(DefaultObject):
    """
    An autonomous NPC transport ship on the Helion-Vanta lane.

    Persistent db attributes
    ------------------------
    ship_name               str        display name shown to players
    ship_class              str        e.g. "Colonial Transport Mk-III"
    route                   list       copy of SHIP_ROUTE (kept for compat)
    route_index             int        current step index in SHIP_GRID_ROUTE
    grid_pos                list|None  [x, y] cell when underway; None when docked
    direction               int        +1 toward Vanta IX, -1 toward Helion Reach
    state                   str        "docked" | "underway"
    dock_ticks_remaining    int        countdown while docked
    gangway_exits           list       [out_dbref, in_dbref] of open gangway Exits
    fare                    int        credits required to board
    cabin_key               str        key of the persistent Cabin Room object
    """

    # ------------------------------------------------------------------
    # Creation
    # ------------------------------------------------------------------

    def at_object_creation(self):
        self.db.ship_name = "Unknown Vessel"
        self.db.ship_class = "Colonial Transport"
        self.db.route = list(SHIP_ROUTE)
        self.db.route_index = 0
        self.db.grid_pos = None
        self.db.direction = 1
        self.db.state = "docked"
        self.db.dock_ticks_remaining = DOCK_TICKS
        self.db.gangway_exits = []
        self.db.fare = 50
        self.db.cabin_key = None

        # Tag for easy global lookup (search_tag("npc_ship", category="ship")).
        self.tags.add("npc_ship", category="ship")

        # Create the persistent cabin room.
        from evennia import create_object

        cabin = create_object("typeclasses.rooms.Room", key=f"{self.key}_cabin")
        cabin.db.display_name = "Passenger Cabin"
        cabin.db.room_key = f"{self.key}_cabin"
        cabin.db.room_type = "shuttle"
        cabin.db.planet = "the_drift"
        cabin.db.area = "transit"
        cabin.db.desc = (
            "The passenger compartment of a colonial transport. "
            "Bench seating lines the hull walls. "
            "A status display shows the current sector and estimated arrival."
        )
        cabin.db.ship_id = self.id
        self.db.cabin_key = cabin.key

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def get_cabin(self):
        """Return the Cabin Room object, or None if missing."""
        from evennia import search_object

        if not self.db.cabin_key:
            return None
        results = search_object(self.db.cabin_key, exact=True)
        return results[0] if results else None

    # ------------------------------------------------------------------
    # Ticker management
    # ------------------------------------------------------------------

    def start_ticker(self):
        """Register (or re-register) the persistent movement ticker."""
        from evennia import TICKER_HANDLER

        TICKER_HANDLER.add(
            SHIP_TICK_INTERVAL,
            _ship_tick,
            idstring=f"npc_ship_{self.id}",
            persistent=True,
            ship_id=self.id,
        )

    # ------------------------------------------------------------------
    # Tick dispatcher
    # ------------------------------------------------------------------

    def tick(self):
        """Called once per SHIP_TICK_INTERVAL by the ticker."""
        state = self.db.state or "docked"
        if state == "docked":
            self._tick_docked()
        elif state == "underway":
            self._tick_underway()

    def _tick_docked(self):
        self.db.dock_ticks_remaining = (self.db.dock_ticks_remaining or 1) - 1
        if self.db.dock_ticks_remaining <= 0:
            self._depart()

    def _tick_underway(self):
        new_index = (self.db.route_index or 0) + (self.db.direction or 1)
        # Safety clamp.
        new_index = max(0, min(new_index, len(SHIP_GRID_ROUTE) - 1))
        self.db.route_index = new_index
        grid_pos = SHIP_GRID_ROUTE[new_index]
        self.db.grid_pos = grid_pos

        # Move ship object to the unified overworld room while underway.
        from evennia import search_object

        ow_results = search_object("overworld_kael_cluster", exact=True)
        if ow_results:
            self.location = ow_results[0]

        # Update cabin description.
        self._update_cabin_status(grid_pos)

        # Announce to cabin passengers.
        cabin = self.get_cabin()
        if cabin and cabin.contents:
            if new_index == 7:
                cabin.msg_contents(
                    "|cShip PA:|n Waystation Kael visible off the port bow. "
                    "Transit continues on schedule."
                )
            else:
                x, y = grid_pos
                cabin.msg_contents(
                    f"|cShip PA:|n Crossing asteroid field — position [{x}, {y}]."
                )

        # Endpoint check.
        if new_index in _ENDPOINT_INDICES:
            bay_key = "helion_docking_bay" if new_index == 0 else "vanta_docking_bay"
            bay_results = search_object(bay_key, exact=True)
            if bay_results:
                self.location = bay_results[0]
                self.db.grid_pos = None
                self._arrive_at_port(bay_results[0])

    # ------------------------------------------------------------------
    # Port arrival / departure
    # ------------------------------------------------------------------

    def _arrive_at_port(self, port_room):
        self.db.state = "docked"
        self.db.dock_ticks_remaining = DOCK_TICKS

        # Reverse direction for the return leg.
        self.db.direction = 1 if self.db.route_index == 0 else -1

        port_name = (
            port_room.db.display_name
            or port_room.key.replace("_", " ").title()
        )
        depart_min = DOCK_TICKS * SHIP_TICK_INTERVAL // 60

        cabin = self.get_cabin()
        if cabin:
            cabin.msg_contents(
                f"|cShip PA:|n Now docking at |w{port_name}|n. "
                f"Gangway will open momentarily. "
                f"Departure in approximately {depart_min} minutes."
            )

        self._open_gangway(port_room)

    def _depart(self):
        self._close_gangway()

        cabin = self.get_cabin()
        if cabin:
            cabin.msg_contents(
                "|cShip PA:|n Gangway sealed. Preparing for departure. "
                "Secure all belongings."
            )

        self.db.state = "underway"
        # Immediately advance one sector (first move of the leg).
        self._tick_underway()

    # ------------------------------------------------------------------
    # Gangway management
    # ------------------------------------------------------------------

    def _open_gangway(self, port_room):
        """Create boarding Exits between port_room and cabin.

        Calls _close_gangway first so this method is idempotent.
        """
        # Always clean up stale exits before creating new ones.
        self._close_gangway()

        cabin = self.get_cabin()
        if not cabin:
            return

        from evennia import create_object

        # cabin → port_room  (free, always open while docked)
        gangway_out = create_object(
            "typeclasses.exits.Exit",
            key="gangway",
            location=cabin,
            destination=port_room,
        )
        gangway_out.db.desc = "The boarding gangway leads out to the docking bay."

        # port_room → cabin  (fare-gated)
        ship_name = self.db.ship_name or self.key
        gangway_in = create_object(
            "typeclasses.exits.FareGangwayExit",
            key="board",
            location=port_room,
            destination=cabin,
        )
        gangway_in.db.fare = self.db.fare or 0
        gangway_in.db.desc = f"Board the {ship_name}."

        self.db.gangway_exits = [gangway_out.dbref, gangway_in.dbref]

        # Announce to docking bay.
        depart_min = DOCK_TICKS * SHIP_TICK_INTERVAL // 60
        port_room.msg_contents(
            f"|y{ship_name}|n has docked. Gangway open. "
            f"Fare: |w{self.db.fare}|n credits. "
            f"Departure in ~{depart_min} min."
        )

    def _close_gangway(self):
        """Delete both gangway Exits.  Safe to call when none are open."""
        from evennia import search_object

        for dbref in self.db.gangway_exits or []:
            results = search_object(dbref, exact=True)
            if results:
                results[0].delete()
        self.db.gangway_exits = []

        # Announce departure from the port room.
        if self.location:
            self.location.msg_contents(
                f"|y{self.db.ship_name or self.key}|n has departed."
            )

    # ------------------------------------------------------------------
    # Cabin status update
    # ------------------------------------------------------------------

    def _update_cabin_status(self, grid_pos: list[int]):
        """Refresh cabin desc with current grid position info."""
        cabin = self.get_cabin()
        if not cabin:
            return
        ship_name = self.db.ship_name or "Transport"
        x, y = grid_pos
        direction_str = (
            "bound for Vanta IX"
            if (self.db.direction or 1) == 1
            else "bound for Helion Reach"
        )
        cabin.db.desc = (
            f"The passenger compartment of the |w{ship_name}|n. "
            f"Bench seating lines the hull. "
            f"The status display reads: |wThe Shardfield [{x}, {y}]|n — {direction_str}. "
            f"A viewport shows tumbling asteroid debris beyond the hull."
        )

    # ------------------------------------------------------------------
    # Status string (used by CmdShips)
    # ------------------------------------------------------------------

    def get_status_string(self) -> str:
        idx = self.db.route_index or 0
        state = self.db.state or "unknown"
        ship_name = self.db.ship_name or self.key

        if state == "docked":
            ticks = self.db.dock_ticks_remaining or 0
            secs = ticks * SHIP_TICK_INTERVAL
            depart = f"{secs // 60}m {secs % 60}s"
            loc_name = ""
            if self.location:
                loc_name = (
                    self.location.db.display_name
                    or self.location.key.replace("_", " ").title()
                )
            return (
                f"|w{ship_name}|n — |gdocked|n at {loc_name}  "
                f"(departs ~{depart})"
            )
        else:
            direction_str = (
                "→ Vanta IX"
                if (self.db.direction or 1) == 1
                else "→ Helion Reach"
            )
            grid_pos = self.db.grid_pos or SHIP_GRID_ROUTE[idx]
            progress = (
                f"step {idx + 1}/{len(SHIP_GRID_ROUTE)} "
                f"[{grid_pos[0]}, {grid_pos[1]}]"
            )
            return (
                f"|w{ship_name}|n — |yunderway|n {direction_str}  ({progress})"
            )
