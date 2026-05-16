"""Runtime state utilities for shuttle travel in the Evennia gamedir."""

from __future__ import annotations

import sys
from pathlib import Path


def _ensure_project_root_on_path() -> None:
    root = str(Path(__file__).resolve().parents[2])
    if root not in sys.path:
        sys.path.insert(0, root)


def get_shuttle_machine():
    """Get a singleton-like shuttle state machine for current server process."""
    _ensure_project_root_on_path()
    from mudgame.systems.travel import ShuttleRouteMachine

    if not hasattr(get_shuttle_machine, "_instance"):
        get_shuttle_machine._instance = ShuttleRouteMachine(  # type: ignore[attr-defined]
            shuttle_key="shardline"
        )
    return get_shuttle_machine._instance  # type: ignore[attr-defined]


def normalize_destination(arg: str) -> str | None:
    cleaned = (arg or "").strip().lower()
    if cleaned in {"helion", "helion_reach", "helion_spaceport"}:
        return "helion_shuttle_dock"
    if cleaned in {"vanta", "vanta_ix", "vanta_orbital_dock"}:
        return "vanta_shuttle_dock"
    return None
