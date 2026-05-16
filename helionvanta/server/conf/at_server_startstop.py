"""
Server startstop hooks

This module contains functions called by Evennia at various
points during its startup, reload and shutdown sequence. It
allows for customizing the server operation as desired.

This module must contain at least these global functions:

at_server_init()
at_server_start()
at_server_stop()
at_server_reload_start()
at_server_reload_stop()
at_server_cold_start()
at_server_cold_stop()

"""


def at_server_init():
    """
    This is called first as the server is starting up, regardless of how.
    """
    pass


def at_server_start():
    """
    This is called every time the server starts up, regardless of
    how it was shut down.

    1. Clear the `sleeping` flag so that sleep delays (which are not
       persistent across restarts) don't leave characters permanently locked.

    2. Re-register NPC ship tickers.  Persistent tickers survive a reload
       but are wiped on a cold restart.  Calling start_ticker() on every
       boot is safe (idempotent) and ensures ships keep moving after both
       reloads and cold starts.
    """
    try:
        from evennia.typeclasses.attributes import Attribute
        Attribute.objects.filter(db_key="sleeping").delete()
    except Exception:
        pass

    # Re-register NPC ship tickers so they survive both reloads and cold restarts.
    try:
        from evennia import search_tag
        ships = search_tag("npc_ship", category="ship")
        for ship in ships:
            ship.start_ticker()
    except Exception:
        pass


def at_server_stop():
    """
    This is called just before the server is shut down, regardless
    of it is for a reload, reset or shutdown.
    """
    pass


def at_server_reload_start():
    """
    This is called only when server starts back up after a reload.
    """
    pass


def at_server_reload_stop():
    """
    This is called only time the server stops before a reload.
    """
    pass


def at_server_cold_start():
    """
    This is called only when the server starts "cold", i.e. after a
    shutdown or a reset.

    1. Clear stale combat sessions — after a cold restart all mobs are
       gone, so any persisted combat_session would suppress regen.
       _ensure_regen_ticker() no longer uses a flag; it always re-registers
       via TICKER_HANDLER.add() which is idempotent, so no flag cleanup needed.

    2. Auto-build the world — ensures rooms, NPCs and mobs exist after a
       fresh database or crash restart, without requiring a manual mudbuild.
    """
    # Clear stale combat sessions on cold restart.
    # After a cold restart all mobs are gone, so any persisted combat_session
    # would permanently suppress HP/shield/PSI regen for logged-in characters.
    try:
        from evennia.typeclasses.attributes import Attribute
        Attribute.objects.filter(db_key="sleeping").delete()
        Attribute.objects.filter(db_key="combat_session").delete()
    except Exception:
        pass

    # Auto-build world from world_data.
    try:
        import sys
        from pathlib import Path
        root = str(Path(__file__).resolve().parents[3])
        if root not in sys.path:
            sys.path.insert(0, root)
        from helionvanta.world.mud_bootstrap import build_vertical_slice
        build_vertical_slice()
    except Exception:
        pass

    # Build The Drift corridor (depends on planet rooms from build_vertical_slice).
    try:
        from helionvanta.world.corridor_bootstrap import build_corridor
        build_corridor()
    except Exception:
        pass

    # Repop any mobs that are currently offline (location is None).
    # This handles the case where the server crashed mid-respawn-delay.
    try:
        from helionvanta.commands.mud_commands import repop_dead_mobs
        repop_dead_mobs()
    except Exception:
        pass


def at_server_cold_stop():
    """
    This is called only when the server goes down due to a shutdown or
    reset.
    """
    pass
