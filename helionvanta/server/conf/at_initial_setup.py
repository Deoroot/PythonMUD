"""
At_initial_setup module template

Custom at_initial_setup method. This allows you to hook special
modifications to the initial server startup process. Note that this
will only be run once - when the server starts up for the very first
time! It is called last in the startup process and can thus be used to
overload things that happened before it.

The module must contain a global function at_initial_setup().  This
will be called without arguments. Note that tracebacks in this module
will be QUIETLY ignored, so make sure to check it well to make sure it
does what you expect it to.

"""


def at_initial_setup():
    from evennia.utils import logger

    try:
        from world.mud_bootstrap import build_vertical_slice
        from evennia import search_object
        from django.conf import settings as django_settings

        summary = build_vertical_slice()
        logger.log_info(
            "Initial Helion-Vanta world build complete: "
            f"rooms+{summary['rooms_created']}, exits+{summary['exits_created']}, "
            f"npcs+{summary['npcs_created']}, mobs+{summary['mobs_created']}."
        )
        # Set default start location to helion_gate.
        start = search_object("helion_gate", exact=True)
        if start:
            dbref = start[0].dbref
            django_settings.DEFAULT_HOME = dbref
            django_settings.START_LOCATION = dbref
            logger.log_info(f"START_LOCATION set to helion_gate ({dbref}).")
    except Exception:
        logger.log_trace("Initial Helion-Vanta world build failed.")
