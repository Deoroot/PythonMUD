"""Command contracts and minimal handlers for vertical slice bootstrap."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

COMMAND_ALIASES = {
    "l": "look",
    "examine": "look",
    "view": "look",
    "g": "go",
    "move": "go",
    "mv": "go",
    "s": "scan",
    "t": "talk",
    "chat": "talk",
    "i": "inventory",
    "inv": "inventory",
    "e": "equip",
    "wield": "equip",
    "atk": "attack",
    "a": "attack",
    "hit": "attack",
    "strike": "attack",
    "p": "parry",
    "block": "parry",
    "d": "dodge",
    "evade": "dodge",
    "tr": "travel",
    "shuttle": "travel",
    "q": "quest",
    "contract": "quest",
}

BASE_COMMANDS = {
    "look",
    "go",
    "scan",
    "talk",
    "inventory",
    "equip",
    "attack",
    "parry",
    "dodge",
    "travel",
    "quest",
}

COMMAND_ARG_REQUIREMENTS = {
    "go": 1,
    "talk": 1,
    "equip": 1,
    "attack": 1,
    "travel": 1,
}


@dataclass(slots=True)
class ParsedCommand:
    command: str
    args: list[str]


def parse_player_input(raw: str) -> ParsedCommand:
    cleaned = (raw or "").strip().lower()
    if not cleaned:
        return ParsedCommand(command="", args=[])

    parts = cleaned.split()
    cmd = COMMAND_ALIASES.get(parts[0], parts[0])
    return ParsedCommand(command=cmd, args=parts[1:])


def validate_command(parsed: ParsedCommand) -> tuple[bool, str]:
    if not parsed.command:
        return False, "No command provided."
    if parsed.command not in BASE_COMMANDS:
        return False, f"Unknown command '{parsed.command}'."
    required_args = COMMAND_ARG_REQUIREMENTS.get(parsed.command, 0)
    if len(parsed.args) < required_args:
        return False, f"Command '{parsed.command}' requires at least {required_args} argument(s)."
    return True, "ok"


def execute_stub(parsed: ParsedCommand) -> str:
    """Return deterministic placeholder output for each base command."""
    handlers = {
        "look": "You take in your surroundings.",
        "go": f"You move {parsed.args[0]}.",
        "scan": "You scan for threats and points of interest.",
        "talk": f"You start a conversation with {' '.join(parsed.args)}.",
        "inventory": "You check your gear and cargo.",
        "equip": f"You ready {' '.join(parsed.args)}.",
        "attack": f"You launch a melee strike at {' '.join(parsed.args)}.",
        "parry": "You angle your weapon for a parry.",
        "dodge": "You shift to evade incoming force.",
        "travel": f"You review shuttle routes to {parsed.args[0]}.",
        "quest": "You check your active contracts.",
    }
    return handlers.get(parsed.command, "Unknown action.")


def dispatch_command(
    parsed: ParsedCommand,
    handler_map: dict[str, Callable[[list[str]], str]] | None = None,
) -> str:
    """Dispatch a parsed command to custom handlers or fallback stubs."""
    valid, message = validate_command(parsed)
    if not valid:
        return message

    if not handler_map:
        return execute_stub(parsed)

    handler = handler_map.get(parsed.command)
    if handler is None:
        return execute_stub(parsed)

    return str(handler(parsed.args))


# Optional Evennia command wrappers (loaded only when Evennia exists in runtime).
try:
    from evennia import Command as EvenniaCommand
except Exception:  # pragma: no cover - Evennia may not be installed in unit-test env.
    EvenniaCommand = object  # type: ignore[misc,assignment]

Command = EvenniaCommand if isinstance(EvenniaCommand, type) else object


class CmdScan(Command):
    key = "scan"

    def func(self):  # type: ignore[override]
        self.caller.msg("You scan the area for threats and routes.")


class CmdTravel(Command):
    key = "travel"

    def func(self):  # type: ignore[override]
        self.caller.msg("Specify a destination port to travel.")


class CmdQuest(Command):
    key = "quest"

    def func(self):  # type: ignore[override]
        self.caller.msg("You review your current contracts.")


class CmdLook(Command):
    key = "look"

    def func(self):  # type: ignore[override]
        self.caller.msg("You take in your surroundings.")


class CmdGo(Command):
    key = "go"

    def func(self):  # type: ignore[override]
        self.caller.msg("You move toward your chosen exit.")


class CmdTalk(Command):
    key = "talk"

    def func(self):  # type: ignore[override]
        self.caller.msg("You start a conversation.")


class CmdInventory(Command):
    key = "inventory"

    def func(self):  # type: ignore[override]
        self.caller.msg("You check your gear and cargo.")


class CmdEquip(Command):
    key = "equip"

    def func(self):  # type: ignore[override]
        self.caller.msg("You ready your selected weapon.")


class CmdAttack(Command):
    key = "attack"

    def func(self):  # type: ignore[override]
        self.caller.msg("You launch a melee strike.")


class CmdParry(Command):
    key = "parry"

    def func(self):  # type: ignore[override]
        self.caller.msg("You angle your weapon for a parry.")


class CmdDodge(Command):
    key = "dodge"

    def func(self):  # type: ignore[override]
        self.caller.msg("You shift to evade incoming force.")
