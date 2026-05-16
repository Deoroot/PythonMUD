"""
Room

Rooms are simple containers that has no location of their own.

"""

from evennia.objects.objects import DefaultRoom

from .objects import ObjectParent


def _actor_display(obj):
    """Return a coloured display string for an NPC or mob.

    Colour logic:
      * Mob with auto_aggro set (hostile)  → red   |r
      * Mob without auto_aggro (passive)   → amber  |y
      * Non-mob actor (friendly NPC)       → green  |g
    """
    name = obj.db.name or obj.key.replace("_", " ").title()
    if obj.db.actor_type == "mob":
        if obj.db.auto_aggro:
            return f"|r{name}|n"
        return f"|y{name}|n"
    return f"|g{name}|n"


class Room(ObjectParent, DefaultRoom):
    """
    Rooms are like any Object, except their location is None
    (which is default). They also use basetype_setup() to
    add locks so they cannot be puppeted or picked up.
    (to change that, use at_object_creation instead)

    See mygame/typeclasses/objects.py for a list of
    properties and methods available on all Objects.
    """

    def return_appearance(self, looker, **kwargs):
        if not looker:
            return ""

        name = self.db.display_name or self.key
        desc = self.db.desc or ""

        # Exits
        exit_keys = [ex.key for ex in self.exits]
        exit_str = "  Exits: " + ", ".join(exit_keys) if exit_keys else "  No obvious exits."

        # Contents — actors (NPCs/mobs) and other players
        present = []
        for obj in self.contents:
            if obj == looker:
                continue
            if obj.db.actor_type:
                present.append(_actor_display(obj))
            elif obj.has_account:
                present.append(obj.get_display_name(looker))

        lines = [f"|w{name}|n"]
        if desc:
            lines.append(desc)
        lines.append(exit_str)
        if present:
            lines.append("  " + "  ".join(present))

        # Floor items — dropped by mobs
        floor_items = self.db.floor_items or []
        if floor_items:
            from mudgame.data.world_data import WORLD_DATA
            item_catalog = WORLD_DATA.get("items", {})
            item_names = []
            for key in floor_items:
                item_data = item_catalog.get(key)
                item_names.append(item_data["name"] if item_data else key.replace("_", " ").title())
            lines.append("|yOn the ground:|n " + ", ".join(f"|w{n}|n" for n in item_names))

        return "\n".join(lines)


class SectorRoom(Room):
    """
    A room in open space — one tile of The Drift corridor grid.

    Sector rooms are traversed only by ships (NPC or player-piloted). Players
    never enter them directly; they ride inside a ship's Cabin Room which is
    a separate, stable object.

    Defaults:
        room_type = "sector"
        planet    = "the_drift"
        area      = "drift_corridor"
    """

    def at_object_creation(self):
        super().at_object_creation()
        if not self.db.room_type:
            self.db.room_type = "sector"
        if not self.db.planet:
            self.db.planet = "the_drift"
        if not self.db.area:
            self.db.area = "drift_corridor"


class DockingBayRoom(Room):
    """
    A ship docking bay at the edge of a port (Helion or Vanta).

    DockingBayRoom sits one step inside the port concourse. NPC ships dock
    here, open a FareGangwayExit into their Cabin Room, and delete it on
    departure. The standard appearance is augmented with any docked ship info.

    Defaults:
        room_type = "docking_bay"
    """

    def at_object_creation(self):
        super().at_object_creation()
        if not self.db.room_type:
            self.db.room_type = "docking_bay"

    def return_appearance(self, looker, **kwargs):
        base = super().return_appearance(looker, **kwargs)

        docked = []
        for obj in self.contents:
            if obj.is_typeclass("typeclasses.ship.NpcTransportShip", exact=False):
                ship_name = obj.db.ship_name or obj.key
                fare = obj.db.fare or 0
                state = obj.db.state or "unknown"
                ticks = obj.db.dock_ticks_remaining or 0
                from typeclasses.ship import SHIP_TICK_INTERVAL
                depart_secs = ticks * SHIP_TICK_INTERVAL
                depart_str = f"{depart_secs // 60}m {depart_secs % 60}s"
                if state == "docked":
                    docked.append(
                        f"  |y{ship_name}|n — docked  "
                        f"(fare: {fare} cr, departs ~{depart_str})"
                    )
                else:
                    docked.append(f"  |w{ship_name}|n — preparing to depart")
            elif obj.is_typeclass("typeclasses.player_ship.PlayerShip", exact=False):
                ship_name = obj.db.ship_name or obj.key
                owner_id = obj.db.owner_id
                owner_str = ""
                if owner_id:
                    from evennia import search_object
                    owner_results = search_object(f"#{owner_id}")
                    if owner_results:
                        owner_str = f" (owner: {owner_results[0].key})"
                docked.append(f"  |c{ship_name}|n — player ship{owner_str}  (board: type the ship key)")

        if docked:
            return base + "\n" + "\n".join(docked)
        return base


class ShipCabinRoom(Room):
    """
    The helm/passenger cabin inside a player-piloted ship.

    When a player character enters this room, ShipNavCmdSet is added at
    priority 10 so their direction keys move the ship through sector exits
    rather than moving the player. The cmdset is removed on exit.

    db.ship_id must be set to the PlayerShip's id for nav commands to work.

    Defaults:
        room_type = "ship_cabin"
        planet    = "the_drift"
        area      = "player_ship"
    """

    def at_object_creation(self):
        super().at_object_creation()
        if not self.db.room_type:
            self.db.room_type = "ship_cabin"
        if not self.db.planet:
            self.db.planet = "the_drift"
        if not self.db.area:
            self.db.area = "player_ship"

    def at_object_receive(self, moved_obj, source_location, **kwargs):
        super().at_object_receive(moved_obj, source_location, **kwargs)
        if moved_obj.has_account:
            from commands.ship_nav_commands import ShipNavCmdSet
            moved_obj.cmdset.add(ShipNavCmdSet, permanent=True)

    def at_object_leave(self, moved_obj, target_location, **kwargs):
        super().at_object_leave(moved_obj, target_location, **kwargs)
        if moved_obj.has_account:
            try:
                from commands.ship_nav_commands import ShipNavCmdSet
                moved_obj.cmdset.delete(ShipNavCmdSet)
            except Exception:
                pass
