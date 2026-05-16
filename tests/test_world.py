from mudgame.data.world_data import WORLD_DATA
from mudgame.world.builder import (
    flatten_rooms,
    path_exists,
    validate_exit_targets,
    validate_room_metadata,
)


def test_room_graph_has_no_missing_targets():
    rooms = flatten_rooms()
    assert validate_exit_targets(rooms) == []


def test_room_metadata_is_valid():
    rooms = flatten_rooms()
    assert validate_room_metadata(rooms) == []


def test_spaceport_cluster_connected():
    # helion_gate ↔ helion_market ↔ helion_shuttle_dock remain connected via static exits.
    rooms = flatten_rooms()
    assert path_exists("helion_gate", "helion_market", rooms)
    assert path_exists("helion_market", "helion_gate", rooms)
    assert path_exists("helion_gate", "helion_shuttle_dock", rooms)


def test_orbital_dock_cluster_connected():
    # vanta_customs ↔ vanta_bazaar ↔ vanta_shuttle_dock remain connected via static exits.
    rooms = flatten_rooms()
    assert path_exists("vanta_customs", "vanta_bazaar", rooms)
    assert path_exists("vanta_bazaar", "vanta_customs", rooms)
    assert path_exists("vanta_customs", "vanta_shuttle_dock", rooms)


def test_cinder_warrens_internal_route_exists():
    # helion_warrens_core ↔ helion_warrens_forge are connected east/west.
    rooms = flatten_rooms()
    assert path_exists("helion_warrens_core", "helion_warrens_forge", rooms)
    assert path_exists("helion_warrens_forge", "helion_warrens_core", rooms)


def test_shuttle_interior_route_exists():
    rooms = flatten_rooms()
    assert path_exists("shuttle_airlock", "shuttle_observation", rooms)


def test_content_has_two_quests_defined():
    quests = WORLD_DATA.get("quests", [])
    assert len(quests) >= 2


# ---------------------------------------------------------------------------
# Loot / credit-drop tests
# ---------------------------------------------------------------------------

def test_all_mobs_have_credit_drop():
    """Every mob must declare a credit_drop with min/max ints."""
    for mob in WORLD_DATA["mobs"]:
        drop = mob.get("credit_drop")
        assert drop is not None, f"{mob['key']} missing credit_drop"
        assert isinstance(drop["min"], int) and isinstance(drop["max"], int)
        assert drop["min"] >= 0
        assert drop["max"] >= drop["min"]


def test_elite_mobs_drop_more_than_common():
    """Elite mob credit_drop max must exceed all common mob credit_drop max."""
    common_max = max(
        m["credit_drop"]["max"]
        for m in WORLD_DATA["mobs"]
        if m["tier"] == "common"
    )
    for mob in WORLD_DATA["mobs"]:
        if mob["tier"] == "elite":
            assert mob["credit_drop"]["max"] > common_max, (
                f"{mob['key']} elite drop max ({mob['credit_drop']['max']}) "
                f"should exceed common max ({common_max})"
            )


# ---------------------------------------------------------------------------
# Grind-tier item catalog tests
# ---------------------------------------------------------------------------

GRIND_ITEMS = ["colony_maul", "fracture_blade", "siege_plate"]


def test_grind_tier_items_exist_in_catalog():
    items = WORLD_DATA["items"]
    for key in GRIND_ITEMS:
        assert key in items, f"Grind-tier item '{key}' missing from catalog"


def test_grind_tier_items_priced_above_quest_total():
    """Each grind-tier item must cost more than the total quest credit rewards (~400)."""
    quest_total = sum(q["rewards"].get("credits", 0) for q in WORLD_DATA["quests"])
    items = WORLD_DATA["items"]
    for key in GRIND_ITEMS:
        price = items[key]["price"]
        assert price > quest_total, (
            f"'{key}' price {price} should exceed quest total {quest_total}"
        )


def test_colony_maul_in_quartermaster_shop():
    vex = next(n for n in WORLD_DATA["npcs"] if n["key"] == "helion_quartermaster")
    assert "colony_maul" in vex["shop"]


def test_fracture_blade_and_siege_plate_in_broker_shop():
    sorn = next(n for n in WORLD_DATA["npcs"] if n["key"] == "vanta_broker")
    assert "fracture_blade" in sorn["shop"]
    assert "siege_plate" in sorn["shop"]


def test_grind_items_have_required_fields():
    items = WORLD_DATA["items"]
    for key in GRIND_ITEMS:
        item = items[key]
        assert "name" in item
        assert "slots" in item and len(item["slots"]) > 0
        assert "price" in item and item["price"] > 0
        assert "desc" in item and len(item["desc"]) > 0

