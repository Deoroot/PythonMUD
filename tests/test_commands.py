from mudgame.commands.base import dispatch_command, parse_player_input, validate_command


def test_command_alias_parsing():
    parsed = parse_player_input("atk raider")
    assert parsed.command == "attack"
    assert parsed.args == ["raider"]


def test_extended_alias_parsing():
    parsed = parse_player_input("evade")
    assert parsed.command == "dodge"


def test_command_validation_and_dispatch():
    parsed = parse_player_input("travel vanta")
    ok, _ = validate_command(parsed)
    assert ok is True
    assert "shuttle routes" in dispatch_command(parsed)


def test_command_validation_requires_arguments():
    parsed = parse_player_input("go")
    ok, message = validate_command(parsed)
    assert ok is False
    assert "requires at least" in message


def test_dispatch_with_custom_handler_map():
    parsed = parse_player_input("attack raider")
    output = dispatch_command(parsed, handler_map={"attack": lambda args: f"handled {args[0]}"})
    assert output == "handled raider"
