import pytest

from mudgame.systems.travel import ShuttleRouteMachine


def test_shuttle_state_machine_happy_path():
    machine = ShuttleRouteMachine(shuttle_key="shardline")

    assert machine.state == "docked"
    machine.begin_boarding()
    assert machine.state == "boarding"
    machine.depart()
    assert machine.state == "in_transit"
    machine.arrive()
    assert machine.state == "arrived"
    machine.reset_docked()
    assert machine.state == "docked"


def test_depart_requires_boarding():
    machine = ShuttleRouteMachine(shuttle_key="shardline")
    with pytest.raises(ValueError):
        machine.depart()


def test_board_and_disembark_permissions_by_state():
    machine = ShuttleRouteMachine(shuttle_key="shardline")
    assert machine.can_board() is True
    assert machine.can_disembark() is True

    machine.begin_boarding()
    assert machine.can_board() is True

    machine.depart()
    assert machine.can_board() is False
    assert machine.can_disembark() is False

    machine.arrive()
    assert machine.can_disembark() is True


def test_airlock_target_locked_during_transit():
    machine = ShuttleRouteMachine(shuttle_key="shardline")
    machine.begin_boarding()
    machine.depart()
    assert machine.get_airlock_dock_target() == "locked"
