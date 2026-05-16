"""Seed/build script to validate and summarize initial world content."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from mudgame.world.builder import seed_summary


def main() -> None:
    summary = seed_summary()
    print("World Seed Summary")
    print(f"- Rooms: {summary['room_count']}")
    print(f"- NPCs: {summary['npc_count']}")
    print(f"- Mobs: {summary['mob_count']}")
    print(f"- Quests: {summary['quest_count']}")
    print(f"- Missing exits: {summary['missing_exit_count']}")
    print(f"- Invalid metadata: {summary['invalid_metadata_count']}")


if __name__ == "__main__":
    main()
