"""Convenience wrapper for invoking Evennia reliably from local virtualenv."""

from __future__ import annotations

import sys

from evennia.server.evennia_launcher import main


if __name__ == "__main__":
    # Preserve CLI semantics, e.g. `python tools/evennia_cli.py migrate`
    main()
