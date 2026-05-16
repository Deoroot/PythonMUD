"""
Build The Drift corridor — 27 sector rooms, 2 docking bays, all exits,
and the two NPC transport ships that run the Helion-Vanta lane.

Safe to call multiple times: all room / exit / ship operations are
find-or-create (idempotent).  Call AFTER build_vertical_slice() so that
helion_gate and vanta_customs already exist.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Room data
# ---------------------------------------------------------------------------

# Ship lane — 9 named rooms forming the NPC transport route
_SHIP_LANE: list[dict] = [
    {
        "key": "drift_helion_outer",
        "name": "Helion Outer Marker",
        "desc": (
            "The last sector before open corridor. Helion Reach's outer asteroid "
            "field thins here — boulders tagged with colonial survey markers drift "
            "slowly, the paint worn by years of micro-impact. The cleared shipping "
            "lane cuts through them in a straight line, border beacons flashing "
            "amber at three-second intervals."
        ),
    },
    {
        "key": "drift_corridor_alpha",
        "name": "Corridor Alpha-1",
        "desc": (
            "Open lane. The debris belt is behind; ahead is the Drift in full — "
            "centuries-old collision fragments hanging in slow, predictable arcs. "
            "The lane was blasted clear at enormous cost; magnetic buoys keep the "
            "path marked and lit. Stars are unusually bright here, unobscured by "
            "any atmosphere."
        ),
    },
    {
        "key": "drift_corridor_beta",
        "name": "Corridor Beta-1",
        "desc": (
            "Mid-corridor sector. A cluster of ice-bearing comets drifts north of "
            "the lane, too diffuse to be hazardous. Sensor returns bounce strangely "
            "off the ice and iron mix — long-range comms are unreliable until the "
            "cluster passes. The lane markers pulse on schedule."
        ),
    },
    {
        "key": "drift_belt_alpha",
        "name": "Alpha Debris Belt",
        "desc": (
            "The route narrows. Dense collision remnants form a wall to port and "
            "starboard; the Drift was not fully cleared here, only threaded through. "
            "The colonial authority maintains the lane with periodic detonation runs, "
            "but fresh debris migrates in constantly. Hull stress readings fluctuate."
        ),
    },
    {
        "key": "drift_waystation_kael",
        "name": "Waystation Kael",
        "desc": (
            "A modular station anchored to a nickel-iron fragment at the corridor "
            "midpoint. Waystation Kael is old — pre-colonial old — visible through "
            "the viewport as a cluster of mismatched docking rings and pressurized "
            "modules welded together across decades. Running lights blink in the "
            "non-standard pattern of an independent operator. Ships pass through; "
            "some stop. The station watches without broadcasting."
        ),
    },
    {
        "key": "drift_belt_beta",
        "name": "Beta Debris Belt",
        "desc": (
            "The second belt is wider but less dense — the debris here is older, "
            "worn smooth by two centuries of mutual attrition. The lane widens on "
            "exit. Vanta Colonial Authority marker buoys begin appearing, yellow "
            "where Helion Colonial Authority's were amber."
        ),
    },
    {
        "key": "drift_corridor_gamma",
        "name": "Corridor Gamma-1",
        "desc": (
            "Cleared lane on the Vanta side of the Drift. Sensor range improves; "
            "the silhouette of Vanta IX is visible as a dark disk against a dim "
            "star field, its captured-moon orbit bringing it within range. "
            "The Glass Dunes are too far to resolve, but the orbital station's "
            "running lights are visible if you know where to look."
        ),
    },
    {
        "key": "drift_corridor_delta",
        "name": "Corridor Delta-1",
        "desc": (
            "Final approach sector. Traffic increases — mining tenders, clan "
            "courier drones, and the occasional unmarked hull running quiet. "
            "The Vanta Orbital Dock resolves on screen as a ring structure, "
            "rotation visible at this range. Docking beacons transmit on "
            "colonial frequencies."
        ),
    },
    {
        "key": "drift_vanta_outer",
        "name": "Vanta Outer Marker",
        "desc": (
            "Edge of Vanta IX space. The orbital dock looms — a ring habitat "
            "with Clan sigils painted large on the docking collar faces. "
            "Patrol corvettes hold station at the approach corridor boundaries. "
            "Colonial markings are tolerated here; clan authority is understood "
            "by everyone passing through."
        ),
    },
]

# Northern debris belt — 9 rooms (row above ship lane)
_NORTH_BELT: list[dict] = [
    {
        "key": f"drift_north_{i}",
        "name": f"Northern Debris Field — Sector N{i}",
        "desc": (
            f"A dense cluster of collision fragments at the northern edge of "
            f"The Drift. Rock and metal tumble slowly in interlocking orbits. "
            f"Survey beacons have been launched here but not recovered. "
            f"No active lane markers. Sector N{i}."
        ),
    }
    for i in range(9)
]

# Southern derelict field — 9 rooms (row below ship lane)
_SOUTH_DEBRIS: list[dict] = [
    {
        "key": f"drift_south_{i}",
        "name": f"Southern Debris Field — Sector S{i}",
        "desc": (
            f"The southern edge of The Drift — the Derelict Field. "
            f"Wrecked hulls from the original collision event and subsequent "
            f"accidents drift here unpowered. Salvage claims have been filed "
            f"and disputed for decades. Dead sensor signatures on every sweep. "
            f"Sector S{i}."
        ),
    }
    for i in range(9)
]

# Docking bays — 1 per port
_DOCKING_BAYS: list[dict] = [
    {
        "key": "helion_docking_bay",
        "name": "Helion Transit Bay",
        "planet": "helion_reach",
        "area": "spaceport",
        "port_room_key": "helion_gate",
        "port_exit": "port",    # helion_gate → helion_docking_bay
        "bay_exit": "terminal", # helion_docking_bay → helion_gate
        "desc": (
            "A pressurized bay adjacent to the main spaceport concourse, "
            "reserved for the Helion-Vanta transit lane. The deck is marked "
            "with mag-lock grid lines and docking collar alignment rails. "
            "Status boards above the airlock display the next scheduled arrival. "
            "A pressure door connects back to the Gate Concourse."
        ),
    },
    {
        "key": "vanta_docking_bay",
        "name": "Vanta Transit Bay",
        "planet": "vanta_ix",
        "area": "orbital_dock",
        "port_room_key": "vanta_customs",
        "port_exit": "port",    # vanta_customs → vanta_docking_bay
        "bay_exit": "terminal", # vanta_docking_bay → vanta_customs
        "desc": (
            "A deep-access docking bay cut into the orbital hull, separate from "
            "the old Shardline berths. The collar rings are Clan-spec — wider "
            "than colonial standard, built for independent haulers. A status "
            "board displays arrivals in both HCA format and Clan-script. "
            "The Customs Ring is through the pressure door aft."
        ),
    },
]

# NPC ships
_NPC_SHIPS: list[dict] = [
    {
        "key": "hca_reliant",
        "ship_name": "HCA Reliant",
        "ship_class": "Colonial Transport Mk-III",
        "fare": 60,
        "start_bay_key": "helion_docking_bay",
        "start_index": 0,
        "start_direction": 1,
        "cabin_desc": (
            "The passenger deck of the |wHCA Reliant|n — a Helion Colonial Authority "
            "contracted transport. Twelve bench-seats in colonial gray with "
            "friction webbing. A route display above the forward bulkhead shows "
            "current sector position and estimated arrival. The walls carry HCA "
            "regulation notices and a faded safety diagram. The cabin smells of "
            "recycled air and people."
        ),
    },
    {
        "key": "the_shardwind",
        "ship_name": "The Shardwind",
        "ship_class": "Clan Independent Transport",
        "fare": 40,
        "start_bay_key": "vanta_docking_bay",
        "start_index": 15,
        "start_direction": -1,
        "cabin_desc": (
            "The passenger hold of |wThe Shardwind|n — an independent Vanta Clan "
            "hauler running the colonial lane under temporary HCA permit. "
            "Bench seating has been re-skinned in Clan textile patterns, warm "
            "against the hull's industrial gray. A hand-painted route board "
            "marks waypoints in both colonial notation and old Clan script."
        ),
    },
]


# ---------------------------------------------------------------------------
# Bootstrap function
# ---------------------------------------------------------------------------

def build_corridor() -> dict[str, int]:
    """
    Create all Drift rooms, exits, and NPC ships.  Safe to run multiple times.

    Returns a stats dict with counts of newly created objects.
    """
    from evennia import create_object, search_object
    from typeclasses.ship import SHIP_ROUTE, SHIP_TICK_INTERVAL, DOCK_TICKS

    rooms_created = 0
    exits_created = 0
    ships_created = 0

    # -- helpers -----------------------------------------------------------

    def _find_or_create_room(key, name, desc, typeclass, planet="the_drift", area="drift_corridor"):
        nonlocal rooms_created
        existing = search_object(key, exact=True)
        if existing:
            room = existing[0]
        else:
            room = create_object(typeclass, key=key)
            rooms_created += 1
        room.db.room_key = key
        room.db.display_name = name
        room.db.desc = desc
        room.db.planet = planet
        room.db.area = area
        return room

    def _ensure_exit(src, direction, dst):
        nonlocal exits_created
        for ex in src.exits:
            if ex.key == direction:
                ex.destination = dst
                return ex
        create_object(
            "typeclasses.exits.Exit",
            key=direction,
            location=src,
            destination=dst,
        )
        exits_created += 1

    # -- build sector rooms ------------------------------------------------

    all_sector_data = _NORTH_BELT + _SHIP_LANE + _SOUTH_DEBRIS
    sector_rooms: dict[str, object] = {}
    for data in all_sector_data:
        room = _find_or_create_room(
            data["key"],
            data["name"],
            data["desc"],
            "typeclasses.rooms.SectorRoom",
        )
        sector_rooms[data["key"]] = room

    # -- build docking bay rooms -------------------------------------------

    bay_rooms: dict[str, object] = {}
    for bay in _DOCKING_BAYS:
        room = _find_or_create_room(
            bay["key"],
            bay["name"],
            bay["desc"],
            "typeclasses.rooms.DockingBayRoom",
            planet=bay["planet"],
            area=bay["area"],
        )
        room.db.room_type = "docking_bay"
        bay_rooms[bay["key"]] = room

    all_rooms = {**sector_rooms, **bay_rooms}

    # -- wire E/W exits within each row ------------------------------------

    rows = [
        [d["key"] for d in _NORTH_BELT],
        [d["key"] for d in _SHIP_LANE],
        [d["key"] for d in _SOUTH_DEBRIS],
    ]
    for row_keys in rows:
        for i in range(len(row_keys) - 1):
            west_r = all_rooms[row_keys[i]]
            east_r = all_rooms[row_keys[i + 1]]
            _ensure_exit(west_r, "east", east_r)
            _ensure_exit(east_r, "west", west_r)

    # -- wire N/S exits between rows (north ↔ lane ↔ south) ---------------

    north_keys = [d["key"] for d in _NORTH_BELT]
    lane_keys  = [d["key"] for d in _SHIP_LANE]
    south_keys = [d["key"] for d in _SOUTH_DEBRIS]

    for i in range(9):
        n = all_rooms[north_keys[i]]
        l = all_rooms[lane_keys[i]]
        s = all_rooms[south_keys[i]]
        _ensure_exit(n, "south", l)
        _ensure_exit(l, "north", n)
        _ensure_exit(l, "south", s)
        _ensure_exit(s, "north", l)

    # -- wire docking bays ↔ planet port concourses -----------------------

    for bay in _DOCKING_BAYS:
        bay_room = bay_rooms[bay["key"]]
        port_results = search_object(bay["port_room_key"], exact=True)
        if port_results:
            port_room = port_results[0]
            _ensure_exit(port_room, bay["port_exit"], bay_room)
            _ensure_exit(bay_room,  bay["bay_exit"],  port_room)

    # -- wire docking bays ↔ drift grid (for player ship navigation) -------
    # NPC ships skip these exits (they use direct location assignment).
    # Player ships traverse them via CmdShipMove.

    _BAY_GRID_LINKS: list[tuple[str, str, str]] = [
        ("helion_docking_bay", "east", "drift_helion_outer"),
        ("drift_helion_outer", "west", "helion_docking_bay"),
        ("vanta_docking_bay",  "west", "drift_vanta_outer"),
        ("drift_vanta_outer",  "east", "vanta_docking_bay"),
    ]
    for src_key, direction, dst_key in _BAY_GRID_LINKS:
        src = all_rooms.get(src_key)
        dst = all_rooms.get(dst_key)
        if src and dst:
            _ensure_exit(src, direction, dst)

    # -- spawn / update NPC ships -----------------------------------------

    for ship_data in _NPC_SHIPS:
        existing = search_object(ship_data["key"], exact=True)
        if existing:
            ship = existing[0]
        else:
            ship = create_object(
                "typeclasses.ship.NpcTransportShip",
                key=ship_data["key"],
            )
            ships_created += 1

        # Always re-apply config so tweaks take effect on re-run.
        ship.db.ship_name = ship_data["ship_name"]
        ship.db.ship_class = ship_data["ship_class"]
        ship.db.fare = ship_data["fare"]
        ship.db.route = list(SHIP_ROUTE)

        # Update cabin desc.
        cabin = ship.get_cabin()
        if cabin:
            cabin.db.desc = ship_data["cabin_desc"]
            cabin.db.display_name = f"{ship_data['ship_name']} — Passenger Cabin"

        # Place ship in starting bay only when not already underway.
        if ship.db.state != "underway":
            start_bay = bay_rooms.get(ship_data["start_bay_key"])
            if start_bay:
                ship.location = start_bay
                ship.db.route_index = ship_data["start_index"]
                ship.db.direction = ship_data["start_direction"]
                ship.db.state = "docked"
                ship.db.dock_ticks_remaining = DOCK_TICKS
                # _open_gangway calls _close_gangway first → idempotent.
                ship._open_gangway(start_bay)

        # (Re-)register the persistent ticker — safe to call on every boot.
        ship.start_ticker()

    return {
        "sector_rooms_created": rooms_created,
        "exits_created": exits_created,
        "ships_created": ships_created,
    }
