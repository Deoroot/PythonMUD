"""Tests for the overworld system — terrain definitions, map rendering,
encounter tables, passability, and named location resolution.

All tests are pure Python (no Evennia imports) and verify:
  - WORLD_DATA["overworld"] structure (kael_cluster unified 80×32 grid, mini-overworlds)
  - mudgame.systems.overworld functions: get_terrain_def, get_glyph,
    get_available_exits, get_named_location, roll_encounter,
    render_minimap_plain, generate_room_description
"""

from __future__ import annotations

import os
import random
import sys

import pytest

# ---------------------------------------------------------------------------
# sys.path setup — no Evennia needed for these tests.
# ---------------------------------------------------------------------------

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from mudgame.data.world_data import WORLD_DATA
from mudgame.systems.overworld import (
    DIRECTIONS,
    DIRECTION_NAMES,
    CINDER_WARRENS_TERRAIN,
    GLASS_DUNES_TERRAIN,
    HELION_TERRAIN,
    PLANET_TERRAIN,
    VANTA_TERRAIN,
    VOID_TERRAIN,
    EncounterEntry,
    TerrainDef,
    generate_room_description,
    get_available_exits,
    get_glyph,
    get_named_location,
    get_terrain_def,
    render_minimap_plain,
    roll_encounter,
)

OW = WORLD_DATA["overworld"]
KC = OW["kael_cluster"]        # unified 80×32 grid (Helion + Void + Vanta)
GD = OW["glass_dunes_ruins"]
CW = OW["cinder_warrens"]


# ---------------------------------------------------------------------------
# world_data schema tests
# ---------------------------------------------------------------------------

class TestOverworldDataSchema:
    """Validate the WORLD_DATA['overworld'] structure."""

    def test_kael_cluster_present(self):
        assert "kael_cluster" in OW

    def test_required_keys_kael_cluster(self):
        for key in ("planet_key", "planet_name", "entry_point", "map", "named_locations"):
            assert key in KC, f"kael_cluster missing: {key}"

    def test_kael_cluster_map_row_count(self):
        assert len(KC["map"]) == 32, f"Expected 32 rows, got {len(KC['map'])}"

    def test_kael_cluster_map_row_widths(self):
        for y, row in enumerate(KC["map"]):
            assert len(row) == 80, (
                f"kael_cluster row y={y} has {len(row)} chars (expected 80): {row!r}"
            )

    def test_kael_cluster_entry_point(self):
        ep = KC["entry_point"]
        assert ep == [15, 5]

    # Named location coordinates — Helion side (x unchanged)
    def test_helion_named_location_spaceport(self):
        loc = next(l for l in KC["named_locations"] if l["room_key"] == "helion_gate")
        assert loc["x"] == 15
        assert loc["y"] == 5

    def test_helion_named_location_iron_covenant(self):
        loc = next(l for l in KC["named_locations"] if l["room_key"] == "iron_covenant_hall")
        assert loc["x"] == 23
        assert loc["y"] == 14

    def test_helion_named_location_warrens(self):
        loc = next(l for l in KC["named_locations"] if l["room_key"] == "helion_warrens_entry")
        assert loc["x"] == 8
        assert loc["y"] == 21

    # Named location coordinates — Vanta side (x shifted +48 in unified grid)
    def test_vanta_named_location_customs(self):
        loc = next(l for l in KC["named_locations"] if l["room_key"] == "vanta_customs")
        assert loc["x"] == 63
        assert loc["y"] == 5

    def test_vanta_named_location_psi_sanctum(self):
        loc = next(l for l in KC["named_locations"] if l["room_key"] == "psi_weavers_sanctum")
        assert loc["x"] == 55
        assert loc["y"] == 14

    def test_vanta_named_location_ruins(self):
        loc = next(l for l in KC["named_locations"] if l["room_key"] == "vanta_ruins_entry")
        assert loc["x"] == 70
        assert loc["y"] == 22

    # Named locations must correspond to '*' glyphs in the map.
    def test_all_named_location_glyphs_are_star(self):
        for loc in KC["named_locations"]:
            glyph = get_glyph(KC["map"], loc["x"], loc["y"])
            assert glyph == "*", (
                f"kael_cluster ({loc['x']},{loc['y']}) expected '*', got {glyph!r}"
            )


# ---------------------------------------------------------------------------
# Terrain definition tests
# ---------------------------------------------------------------------------

class TestTerrainDefs:
    """Validate HELION_TERRAIN, VANTA_TERRAIN, and VOID_TERRAIN entries."""

    def test_helion_has_required_glyphs(self):
        for glyph in (".", "h", "m", "f", "w", "r", "i", "=", "~", "c", "*"):
            assert glyph in HELION_TERRAIN, f"HELION_TERRAIN missing glyph {glyph!r}"

    def test_vanta_has_required_glyphs(self):
        for glyph in (".", "f", "h", "m", "~", "a", "R", "=", "s", "c", "*"):
            assert glyph in VANTA_TERRAIN, f"VANTA_TERRAIN missing glyph {glyph!r}"

    def test_void_has_required_glyphs(self):
        for glyph in (":", "="):
            assert glyph in VOID_TERRAIN, f"VOID_TERRAIN missing glyph {glyph!r}"

    def test_helion_mountain_impassable(self):
        tdef = get_terrain_def("helion_reach", "m")
        assert not tdef.passable

    def test_helion_toxin_impassable(self):
        tdef = get_terrain_def("helion_reach", "~")
        assert not tdef.passable

    def test_vanta_void_peak_impassable(self):
        tdef = get_terrain_def("vanta_ix", "m")
        assert not tdef.passable

    def test_vanta_null_sea_impassable(self):
        tdef = get_terrain_def("vanta_ix", "~")
        assert not tdef.passable

    def test_void_asteroid_impassable(self):
        tdef = get_terrain_def("kael_cluster", ":", x=32)
        assert not tdef.passable

    def test_void_tradelane_impassable(self):
        tdef = get_terrain_def("kael_cluster", "=", x=39)
        assert not tdef.passable

    def test_void_has_impassable_messages(self):
        for glyph in (":", "="):
            tdef = get_terrain_def("kael_cluster", glyph, x=35)
            assert tdef.impassable_msg, f"void/{glyph} has no impassable_msg"

    def test_helion_dust_passable(self):
        tdef = get_terrain_def("helion_reach", ".")
        assert tdef.passable

    def test_vanta_glass_dunes_passable(self):
        tdef = get_terrain_def("vanta_ix", ".")
        assert tdef.passable

    def test_impassable_terrain_has_message(self):
        for planet in ("helion_reach", "vanta_ix"):
            for glyph in ("m", "~"):
                tdef = get_terrain_def(planet, glyph)
                assert tdef.impassable_msg, (
                    f"{planet}/{glyph} impassable but no impassable_msg"
                )

    def test_encounter_entries_have_valid_chances(self):
        for planet_key, tmap in PLANET_TERRAIN.items():
            for glyph, tdef in tmap.items():
                for enc in tdef.encounters:
                    assert 0.0 < enc.chance_per_step <= 1.0, (
                        f"{planet_key}/{glyph} encounter chance out of range: {enc.chance_per_step}"
                    )

    def test_unknown_glyph_fallback(self):
        tdef = get_terrain_def("helion_reach", "?")
        assert isinstance(tdef, TerrainDef)
        assert tdef.passable  # unknown defaults to passable

    def test_planet_terrain_map_keys(self):
        assert "helion_reach" in PLANET_TERRAIN
        assert "vanta_ix" in PLANET_TERRAIN
        assert "kael_cluster" in PLANET_TERRAIN


# ---------------------------------------------------------------------------
# get_glyph tests
# ---------------------------------------------------------------------------

class TestGetGlyph:
    """Test map coordinate access on the unified kael_cluster grid."""

    # Helion side (x=0–31)
    def test_glyph_at_spaceport(self):
        assert get_glyph(KC["map"], 15, 5) == "*"

    def test_glyph_at_iron_covenant(self):
        assert get_glyph(KC["map"], 23, 14) == "*"

    def test_glyph_at_warrens(self):
        assert get_glyph(KC["map"], 8, 21) == "*"

    # Vanta side (x=48–79, shifted +48 from old per-planet coords)
    def test_glyph_at_vanta_customs(self):
        assert get_glyph(KC["map"], 63, 5) == "*"

    def test_glyph_at_psi_sanctum(self):
        assert get_glyph(KC["map"], 55, 14) == "*"

    def test_glyph_at_ruins(self):
        assert get_glyph(KC["map"], 70, 22) == "*"

    def test_out_of_bounds_returns_space(self):
        assert get_glyph(KC["map"], -1, 0) == " "
        assert get_glyph(KC["map"], 0, -1) == " "
        assert get_glyph(KC["map"], 80, 0) == " "   # grid is 80 wide
        assert get_glyph(KC["map"], 0, 32) == " "   # grid is 32 tall

    def test_corner_positions(self):
        # top-left and bottom-right should be valid chars (not out-of-bounds space).
        assert get_glyph(KC["map"], 0, 0) != " "
        assert get_glyph(KC["map"], 79, 31) != " "


# ---------------------------------------------------------------------------
# get_available_exits tests
# ---------------------------------------------------------------------------

class TestGetAvailableExits:
    """Test exit availability based on terrain passability."""

    def test_exits_at_spaceport(self):
        exits = get_available_exits("kael_cluster", KC["map"], 15, 5)
        assert isinstance(exits, list)
        assert len(exits) > 0, "Expected at least one exit from spaceport"

    def test_no_exits_into_mountains_from_y0_x0(self):
        # (0,0) should have very limited exits (NW corner is mountains).
        exits = get_available_exits("kael_cluster", KC["map"], 0, 0)
        # Can only go e/se/s from top-left; NW/N/W are out of bounds.
        for d in exits:
            assert d in ("e", "se", "s"), f"Unexpected exit {d!r} from (0,0)"

    def test_impassable_not_in_exits(self):
        # Find a position adjacent to toxin or mountain and verify it's excluded.
        # (14, 31) on helion side is '~', so from (14, 30) south exit should not exist.
        glyph_south = get_glyph(KC["map"], 14, 31)
        if glyph_south == "~":
            exits = get_available_exits("kael_cluster", KC["map"], 14, 30)
            assert "s" not in exits

    def test_exits_include_all_passable_directions(self):
        # From a central dust position, should have at least some exits.
        exits = get_available_exits("kael_cluster", KC["map"], 15, 10)
        assert len(exits) > 0


# ---------------------------------------------------------------------------
# get_named_location tests
# ---------------------------------------------------------------------------

class TestGetNamedLocation:
    """Test named location resolution on the unified kael_cluster grid."""

    def test_finds_spaceport(self):
        loc = get_named_location("kael_cluster", 15, 5, KC)
        assert loc is not None
        assert loc["room_key"] == "helion_gate"

    def test_finds_iron_covenant(self):
        loc = get_named_location("kael_cluster", 23, 14, KC)
        assert loc is not None
        assert loc["room_key"] == "iron_covenant_hall"

    def test_finds_warrens(self):
        loc = get_named_location("kael_cluster", 8, 21, KC)
        assert loc is not None
        assert loc["room_key"] == "helion_warrens_entry"

    def test_finds_vanta_customs(self):
        loc = get_named_location("kael_cluster", 63, 5, KC)
        assert loc is not None
        assert loc["room_key"] == "vanta_customs"

    def test_finds_psi_sanctum(self):
        loc = get_named_location("kael_cluster", 55, 14, KC)
        assert loc is not None
        assert loc["room_key"] == "psi_weavers_sanctum"

    def test_finds_ruins(self):
        loc = get_named_location("kael_cluster", 70, 22, KC)
        assert loc is not None
        assert loc["room_key"] == "vanta_ruins_entry"

    def test_returns_none_for_plain_terrain(self):
        # Most cells are not named locations.
        loc = get_named_location("kael_cluster", 0, 10, KC)
        assert loc is None

    def test_named_locations_have_required_keys(self):
        for loc in KC["named_locations"]:
            for k in ("name", "x", "y", "room_key", "desc"):
                assert k in loc, (
                    f"kael_cluster named_location missing key {k!r}: {loc}"
                )


# ---------------------------------------------------------------------------
# roll_encounter tests
# ---------------------------------------------------------------------------

class TestRollEncounter:
    """Test encounter rolling with seeded RNG."""

    def _always_rng(self) -> random.Random:
        """RNG that always returns 0.0 → always triggers encounter."""
        rng = random.Random()
        rng.random = lambda: 0.0
        return rng

    def _never_rng(self) -> random.Random:
        """RNG that always returns 1.0 → never triggers encounter."""
        rng = random.Random()
        rng.random = lambda: 1.0
        return rng

    def test_always_rng_triggers_encounter_on_hostile_terrain(self):
        # Dust flats have encounters.
        result = roll_encounter("helion_reach", ".", rng=self._always_rng())
        assert isinstance(result, EncounterEntry)

    def test_never_rng_returns_none(self):
        result = roll_encounter("helion_reach", ".", rng=self._never_rng())
        assert result is None

    def test_settlement_has_no_encounters(self):
        # Settlements are safe; even always-rng should yield None.
        result = roll_encounter("helion_reach", "c", rng=self._always_rng())
        assert result is None

    def test_named_loc_has_no_encounters(self):
        result = roll_encounter("helion_reach", "*", rng=self._always_rng())
        assert result is None

    def test_impassable_terrain_encounter_no_crash(self):
        # Mountain is impassable but roll_encounter should not crash.
        result = roll_encounter("helion_reach", "m", rng=self._never_rng())
        assert result is None

    def test_returns_encounter_entry_fields(self):
        result = roll_encounter("helion_reach", ".", rng=self._always_rng())
        assert result is not None
        assert hasattr(result, "mob_key")
        assert hasattr(result, "chance_per_step")
        assert hasattr(result, "aggro")
        assert hasattr(result, "aggro_delay")

    def test_vanta_anomaly_triggers_encounter(self):
        result = roll_encounter("vanta_ix", "a", rng=self._always_rng())
        assert isinstance(result, EncounterEntry)


# ---------------------------------------------------------------------------
# render_minimap_plain tests
# ---------------------------------------------------------------------------

class TestRenderMinimapPlain:
    """Test minimap rendering (plain text, no ANSI)."""

    def test_returns_9_rows(self):
        rows = render_minimap_plain(KC["map"], 15, 5)
        assert len(rows) == 9, f"Expected 9 rows, got {len(rows)}"

    def test_each_row_is_13_chars(self):
        rows = render_minimap_plain(KC["map"], 15, 5)
        for i, row in enumerate(rows):
            assert len(row) == 13, (
                f"Row {i} has {len(row)} chars (expected 13): {row!r}"
            )

    def test_player_at_centre(self):
        rows = render_minimap_plain(KC["map"], 15, 5)
        centre_row = rows[4]   # half_h=4 → player at row index 4
        centre_col = centre_row[6]  # half_w=6 → player at col index 6
        assert centre_col == "@", f"Expected '@' at centre, got {centre_col!r}"

    def test_no_ansi_codes(self):
        rows = render_minimap_plain(KC["map"], 15, 5)
        for row in rows:
            assert "\033" not in row, "Plain minimap should not contain ANSI codes"

    def test_out_of_bounds_edge_shows_space(self):
        # Player at (0, 0) → cells to the NW are out of bounds → should be ' '.
        rows = render_minimap_plain(KC["map"], 0, 0)
        # Top-left cell of the viewport is at (-6, -4) — out of bounds.
        assert rows[0][0] == " ", "Out-of-bounds cells should be ' '"

    def test_viewport_clips_correctly_at_bottom_right(self):
        rows = render_minimap_plain(KC["map"], 79, 31)
        # Player is at lower-right corner; most of the viewport extends OOB.
        assert rows[4][6] == "@"


# ---------------------------------------------------------------------------
# generate_room_description tests
# ---------------------------------------------------------------------------

class TestGenerateRoomDescription:
    """Test full room description generation on the kael_cluster grid."""

    def test_returns_string(self):
        desc = generate_room_description(
            "kael_cluster", "The Shardfield", KC["map"], 15, 5, KC, colour=False
        )
        assert isinstance(desc, str)
        assert len(desc) > 0

    def test_contains_terrain_name(self):
        desc = generate_room_description(
            "kael_cluster", "The Shardfield", KC["map"], 15, 5, KC, colour=False
        )
        # (15,5) is '*' = Named Location
        assert "Named Location" in desc or "Helion Spaceport" in desc or "enter" in desc.lower()

    def test_contains_exits_line(self):
        desc = generate_room_description(
            "kael_cluster", "The Shardfield", KC["map"], 16, 10, KC, colour=False
        )
        assert "Exits:" in desc

    def test_contains_planet_name_in_header(self):
        desc = generate_room_description(
            "kael_cluster", "The Shardfield", KC["map"], 16, 10, KC, colour=False
        )
        assert "The Shardfield" in desc

    def test_named_location_shows_enter_hint(self):
        desc = generate_room_description(
            "kael_cluster", "The Shardfield", KC["map"], 15, 5, KC, colour=False
        )
        assert "enter" in desc.lower()

    def test_no_crash_at_edge(self):
        # Should not raise even at map edge.
        desc = generate_room_description(
            "kael_cluster", "The Shardfield", KC["map"], 0, 0, KC, colour=False
        )
        assert isinstance(desc, str)

    def test_vanta_section_desc_works(self):
        # Test at Vanta Customs (63, 5) on the unified grid.
        desc = generate_room_description(
            "kael_cluster", "The Shardfield", KC["map"], 63, 5, KC, colour=False
        )
        assert "The Shardfield" in desc


# ---------------------------------------------------------------------------
# Direction helpers tests
# ---------------------------------------------------------------------------

class TestDirectionHelpers:
    """Validate DIRECTIONS and DIRECTION_NAMES dicts."""

    def test_all_8_directions_present(self):
        for d in ("n", "ne", "e", "se", "s", "sw", "w", "nw"):
            assert d in DIRECTIONS
            assert d in DIRECTION_NAMES

    def test_opposite_directions_cancel(self):
        for d1, d2 in (("n", "s"), ("e", "w"), ("ne", "sw"), ("nw", "se")):
            dx1, dy1 = DIRECTIONS[d1]
            dx2, dy2 = DIRECTIONS[d2]
            assert dx1 + dx2 == 0
            assert dy1 + dy2 == 0


# ---------------------------------------------------------------------------
# Glass Dunes mini-overworld — data schema tests
# ---------------------------------------------------------------------------

class TestGlassDunesDataSchema:
    """Validate WORLD_DATA['overworld']['glass_dunes_ruins'] structure."""

    def test_glass_dunes_present_in_overworld(self):
        assert "glass_dunes_ruins" in OW

    def test_required_keys(self):
        for key in ("planet_key", "planet_name", "entry_point", "map", "named_locations"):
            assert key in GD, f"glass_dunes_ruins missing: {key}"

    def test_planet_key_value(self):
        assert GD["planet_key"] == "glass_dunes_ruins"

    def test_planet_name_value(self):
        assert GD["planet_name"] == "Glass Dunes Ruins"

    def test_entry_point(self):
        assert GD["entry_point"] == [9, 0]

    def test_map_row_count(self):
        assert len(GD["map"]) == 14, f"Expected 14 rows, got {len(GD['map'])}"

    def test_map_row_widths(self):
        for y, row in enumerate(GD["map"]):
            assert len(row) == 20, (
                f"glass_dunes_ruins row y={y} has {len(row)} chars (expected 20): {row!r}"
            )

    def test_three_named_locations(self):
        assert len(GD["named_locations"]) == 3

    def test_named_location_lift(self):
        loc = next(l for l in GD["named_locations"] if l["room_key"] == "vanta_ruins_entry")
        assert loc["x"] == 9
        assert loc["y"] == 0

    def test_named_location_ruins_core(self):
        loc = next(l for l in GD["named_locations"] if l["room_key"] == "vanta_ruins_core")
        assert loc["x"] == 4
        assert loc["y"] == 8

    def test_named_location_vault(self):
        loc = next(l for l in GD["named_locations"] if l["room_key"] == "vanta_ruins_vault")
        assert loc["x"] == 15
        assert loc["y"] == 12

    def test_named_location_glyphs_are_star(self):
        for loc in GD["named_locations"]:
            glyph = get_glyph(GD["map"], loc["x"], loc["y"])
            assert glyph == "*", (
                f"glass_dunes_ruins ({loc['x']},{loc['y']}) expected '*', got {glyph!r}"
            )

    def test_entry_point_glyph_is_star(self):
        ex, ey = GD["entry_point"]
        glyph = get_glyph(GD["map"], ex, ey)
        assert glyph == "*", f"Entry point ({ex},{ey}) expected '*', got {glyph!r}"


# ---------------------------------------------------------------------------
# Glass Dunes — terrain definition tests
# ---------------------------------------------------------------------------

class TestGlassDunesTerrain:
    """Validate GLASS_DUNES_TERRAIN entries and PLANET_TERRAIN registration."""

    def test_glass_dunes_in_planet_terrain(self):
        assert "glass_dunes_ruins" in PLANET_TERRAIN

    def test_required_glyphs(self):
        for glyph in (".", "f", "R", "s", "m", "*"):
            assert glyph in GLASS_DUNES_TERRAIN, (
                f"GLASS_DUNES_TERRAIN missing glyph {glyph!r}"
            )

    def test_crystal_wall_impassable(self):
        tdef = get_terrain_def("glass_dunes_ruins", "m")
        assert not tdef.passable

    def test_crystal_wall_has_message(self):
        tdef = get_terrain_def("glass_dunes_ruins", "m")
        assert tdef.impassable_msg

    def test_open_dune_passable(self):
        tdef = get_terrain_def("glass_dunes_ruins", ".")
        assert tdef.passable

    def test_crystal_formation_passable(self):
        tdef = get_terrain_def("glass_dunes_ruins", "f")
        assert tdef.passable

    def test_ruin_structure_passable(self):
        tdef = get_terrain_def("glass_dunes_ruins", "R")
        assert tdef.passable

    def test_shattered_glass_passable(self):
        tdef = get_terrain_def("glass_dunes_ruins", "s")
        assert tdef.passable

    def test_encounter_chances_in_range(self):
        for glyph, tdef in GLASS_DUNES_TERRAIN.items():
            for enc in tdef.encounters:
                assert 0.0 < enc.chance_per_step <= 1.0, (
                    f"glass_dunes_ruins/{glyph} encounter chance out of range: "
                    f"{enc.chance_per_step}"
                )

    def test_named_location_no_encounters(self):
        tdef = get_terrain_def("glass_dunes_ruins", "*")
        assert tdef.encounters == []

    def test_unknown_glyph_falls_back(self):
        tdef = get_terrain_def("glass_dunes_ruins", "?")
        assert isinstance(tdef, TerrainDef)
        assert tdef.passable


# ---------------------------------------------------------------------------
# Glass Dunes — glyph and encounter tests
# ---------------------------------------------------------------------------

class TestGlassDunesGlyphs:
    """Test glyph lookups and encounter rolling on the Glass Dunes map."""

    def test_lift_glyph_is_star(self):
        assert get_glyph(GD["map"], 9, 0) == "*"

    def test_ruins_core_glyph_is_star(self):
        assert get_glyph(GD["map"], 4, 8) == "*"

    def test_vault_glyph_is_star(self):
        assert get_glyph(GD["map"], 15, 12) == "*"

    def test_open_dune_glyph(self):
        # (9, 1) should be open dune '.'
        assert get_glyph(GD["map"], 9, 1) == "."

    def test_crystal_wall_glyph(self):
        # (0, 0) top-left corner is crystal wall 'm'
        assert get_glyph(GD["map"], 0, 0) == "m"

    def test_out_of_bounds_is_space(self):
        assert get_glyph(GD["map"], -1, 0) == " "
        assert get_glyph(GD["map"], 0, -1) == " "
        assert get_glyph(GD["map"], 20, 0) == " "
        assert get_glyph(GD["map"], 0, 14) == " "

    def _always_rng(self):
        class _AlwaysHit:
            def random(self):
                return 0.0
        return _AlwaysHit()

    def _never_rng(self):
        class _NeverHit:
            def random(self):
                return 1.0
        return _NeverHit()

    def test_open_dune_encounter_triggers(self):
        result = roll_encounter("glass_dunes_ruins", ".", rng=self._always_rng())
        assert isinstance(result, EncounterEntry)

    def test_crystal_formation_encounter_triggers(self):
        result = roll_encounter("glass_dunes_ruins", "f", rng=self._always_rng())
        assert isinstance(result, EncounterEntry)

    def test_ruin_structure_encounter_triggers(self):
        result = roll_encounter("glass_dunes_ruins", "R", rng=self._always_rng())
        assert isinstance(result, EncounterEntry)

    def test_shattered_glass_encounter_triggers(self):
        result = roll_encounter("glass_dunes_ruins", "s", rng=self._always_rng())
        assert isinstance(result, EncounterEntry)

    def test_no_encounter_on_crystal_wall(self):
        result = roll_encounter("glass_dunes_ruins", "m", rng=self._always_rng())
        assert result is None

    def test_no_encounter_on_named_location(self):
        result = roll_encounter("glass_dunes_ruins", "*", rng=self._always_rng())
        assert result is None

    def test_encounter_miss(self):
        result = roll_encounter("glass_dunes_ruins", ".", rng=self._never_rng())
        assert result is None

    def test_glass_stalker_is_primary_encounter(self):
        result = roll_encounter("glass_dunes_ruins", ".", rng=self._always_rng())
        assert result is not None
        assert result.mob_key == "glass_stalker"

    def test_shattered_glass_highest_encounter_rate(self):
        # Shattered glass ('s') should have the highest single encounter chance.
        s_chance = max(e.chance_per_step for e in GLASS_DUNES_TERRAIN["s"].encounters)
        dot_chance = max(e.chance_per_step for e in GLASS_DUNES_TERRAIN["."].encounters)
        assert s_chance >= dot_chance


# ---------------------------------------------------------------------------
# Glass Dunes — named location resolution tests
# ---------------------------------------------------------------------------

class TestGlassDunesNamedLocations:
    """Test get_named_location on the Glass Dunes mini-overworld."""

    def test_lift_resolves(self):
        loc = get_named_location("glass_dunes_ruins", 9, 0, GD)
        assert loc is not None
        assert loc["room_key"] == "vanta_ruins_entry"

    def test_ruins_core_resolves(self):
        loc = get_named_location("glass_dunes_ruins", 4, 8, GD)
        assert loc is not None
        assert loc["room_key"] == "vanta_ruins_core"

    def test_vault_resolves(self):
        loc = get_named_location("glass_dunes_ruins", 15, 12, GD)
        assert loc is not None
        assert loc["room_key"] == "vanta_ruins_vault"

    def test_non_location_returns_none(self):
        loc = get_named_location("glass_dunes_ruins", 9, 1, GD)
        assert loc is None

    def test_out_of_bounds_returns_none(self):
        loc = get_named_location("glass_dunes_ruins", 99, 99, GD)
        assert loc is None


# ---------------------------------------------------------------------------
# Glass Dunes — room description generation
# ---------------------------------------------------------------------------

class TestGlassDunesRoomDescription:
    """Test generate_room_description on the Glass Dunes mini-overworld."""

    def test_returns_string(self):
        desc = generate_room_description(
            "glass_dunes_ruins", "Glass Dunes Ruins", GD["map"], 9, 1, GD, colour=False
        )
        assert isinstance(desc, str) and len(desc) > 0

    def test_contains_area_name(self):
        desc = generate_room_description(
            "glass_dunes_ruins", "Glass Dunes Ruins", GD["map"], 9, 1, GD, colour=False
        )
        assert "Glass Dunes Ruins" in desc

    def test_contains_exits_line(self):
        desc = generate_room_description(
            "glass_dunes_ruins", "Glass Dunes Ruins", GD["map"], 9, 1, GD, colour=False
        )
        assert "Exits:" in desc

    def test_named_location_shows_enter_hint(self):
        desc = generate_room_description(
            "glass_dunes_ruins", "Glass Dunes Ruins", GD["map"], 9, 0, GD, colour=False
        )
        assert "enter" in desc.lower()

    def test_no_crash_at_edge(self):
        desc = generate_room_description(
            "glass_dunes_ruins", "Glass Dunes Ruins", GD["map"], 0, 0, GD, colour=False
        )
        assert isinstance(desc, str)


# ---------------------------------------------------------------------------
# Cinder Warrens mini-overworld — data schema tests
# ---------------------------------------------------------------------------

class TestCinderWarrensDataSchema:
    """Validate WORLD_DATA['overworld']['cinder_warrens'] structure."""

    def test_cinder_warrens_present_in_overworld(self):
        assert "cinder_warrens" in OW

    def test_required_keys(self):
        for key in ("planet_key", "planet_name", "entry_point", "map", "named_locations"):
            assert key in CW, f"cinder_warrens missing: {key}"

    def test_planet_key_value(self):
        assert CW["planet_key"] == "cinder_warrens"

    def test_planet_name_value(self):
        assert CW["planet_name"] == "Cinder Warrens"

    def test_entry_point(self):
        assert CW["entry_point"] == [10, 0]

    def test_map_row_count(self):
        assert len(CW["map"]) == 14, f"Expected 14 rows, got {len(CW['map'])}"

    def test_map_row_widths(self):
        for y, row in enumerate(CW["map"]):
            assert len(row) == 20, (
                f"cinder_warrens row y={y} has {len(row)} chars (expected 20): {row!r}"
            )

    def test_three_named_locations(self):
        assert len(CW["named_locations"]) == 3

    def test_named_location_entry_hatch(self):
        loc = next(l for l in CW["named_locations"] if l["room_key"] == "helion_warrens_entry")
        assert loc["x"] == 10
        assert loc["y"] == 0

    def test_named_location_warrens_core(self):
        loc = next(l for l in CW["named_locations"] if l["room_key"] == "helion_warrens_core")
        assert loc["x"] == 5
        assert loc["y"] == 8

    def test_named_location_scrapforge(self):
        loc = next(l for l in CW["named_locations"] if l["room_key"] == "helion_warrens_forge")
        assert loc["x"] == 14
        assert loc["y"] == 11

    def test_named_location_glyphs_are_star(self):
        for loc in CW["named_locations"]:
            glyph = get_glyph(CW["map"], loc["x"], loc["y"])
            assert glyph == "*", (
                f"cinder_warrens ({loc['x']},{loc['y']}) expected '*', got {glyph!r}"
            )

    def test_entry_point_glyph_is_star(self):
        ex, ey = CW["entry_point"]
        glyph = get_glyph(CW["map"], ex, ey)
        assert glyph == "*", f"Entry point ({ex},{ey}) expected '*', got {glyph!r}"

    def test_named_locations_have_required_keys(self):
        for loc in CW["named_locations"]:
            for k in ("name", "x", "y", "room_key", "desc"):
                assert k in loc, f"cinder_warrens named_location missing key {k!r}: {loc}"


# ---------------------------------------------------------------------------
# Cinder Warrens — terrain definition tests
# ---------------------------------------------------------------------------

class TestCinderWarrensTerrain:
    """Validate CINDER_WARRENS_TERRAIN entries and PLANET_TERRAIN registration."""

    def test_cinder_warrens_in_planet_terrain(self):
        assert "cinder_warrens" in PLANET_TERRAIN

    def test_required_glyphs(self):
        for glyph in (".", "g", "s", "d", "#", "*"):
            assert glyph in CINDER_WARRENS_TERRAIN, (
                f"CINDER_WARRENS_TERRAIN missing glyph {glyph!r}"
            )

    def test_collapsed_passage_impassable(self):
        tdef = get_terrain_def("cinder_warrens", "#")
        assert not tdef.passable

    def test_collapsed_passage_has_message(self):
        tdef = get_terrain_def("cinder_warrens", "#")
        assert tdef.impassable_msg

    def test_tunnel_corridor_passable(self):
        tdef = get_terrain_def("cinder_warrens", ".")
        assert tdef.passable

    def test_generator_housing_passable(self):
        tdef = get_terrain_def("cinder_warrens", "g")
        assert tdef.passable

    def test_salvage_pile_passable(self):
        tdef = get_terrain_def("cinder_warrens", "s")
        assert tdef.passable

    def test_heat_duct_passable(self):
        tdef = get_terrain_def("cinder_warrens", "d")
        assert tdef.passable

    def test_encounter_chances_in_range(self):
        for glyph, tdef in CINDER_WARRENS_TERRAIN.items():
            for enc in tdef.encounters:
                assert 0.0 < enc.chance_per_step <= 1.0, (
                    f"cinder_warrens/{glyph} encounter chance out of range: "
                    f"{enc.chance_per_step}"
                )

    def test_named_location_no_encounters(self):
        tdef = get_terrain_def("cinder_warrens", "*")
        assert tdef.encounters == []

    def test_unknown_glyph_falls_back(self):
        tdef = get_terrain_def("cinder_warrens", "?")
        assert isinstance(tdef, TerrainDef)
        assert tdef.passable


# ---------------------------------------------------------------------------
# Cinder Warrens — glyph and encounter tests
# ---------------------------------------------------------------------------

class TestCinderWarrensGlyphs:
    """Test glyph lookups and encounter rolling on the Cinder Warrens map."""

    def test_entry_hatch_glyph_is_star(self):
        assert get_glyph(CW["map"], 10, 0) == "*"

    def test_warrens_core_glyph_is_star(self):
        assert get_glyph(CW["map"], 5, 8) == "*"

    def test_scrapforge_glyph_is_star(self):
        assert get_glyph(CW["map"], 14, 11) == "*"

    def test_tunnel_corridor_glyph(self):
        # (9, 1) should be tunnel corridor '.'
        assert get_glyph(CW["map"], 9, 1) == "."

    def test_collapsed_passage_glyph_at_border(self):
        # (0, 0) top-left corner is collapsed passage '#'
        assert get_glyph(CW["map"], 0, 0) == "#"

    def test_generator_housing_glyph(self):
        # (10, 1) should be generator housing 'g'
        assert get_glyph(CW["map"], 10, 1) == "g"

    def test_out_of_bounds_is_space(self):
        assert get_glyph(CW["map"], -1, 0) == " "
        assert get_glyph(CW["map"], 0, -1) == " "
        assert get_glyph(CW["map"], 20, 0) == " "
        assert get_glyph(CW["map"], 0, 14) == " "

    def _always_rng(self):
        class _AlwaysHit:
            def random(self):
                return 0.0
        return _AlwaysHit()

    def _never_rng(self):
        class _NeverHit:
            def random(self):
                return 1.0
        return _NeverHit()

    def test_tunnel_corridor_encounter_triggers(self):
        result = roll_encounter("cinder_warrens", ".", rng=self._always_rng())
        assert isinstance(result, EncounterEntry)

    def test_generator_housing_encounter_triggers(self):
        result = roll_encounter("cinder_warrens", "g", rng=self._always_rng())
        assert isinstance(result, EncounterEntry)

    def test_salvage_pile_encounter_triggers(self):
        result = roll_encounter("cinder_warrens", "s", rng=self._always_rng())
        assert isinstance(result, EncounterEntry)

    def test_heat_duct_encounter_triggers(self):
        result = roll_encounter("cinder_warrens", "d", rng=self._always_rng())
        assert isinstance(result, EncounterEntry)

    def test_no_encounter_on_collapsed_passage(self):
        result = roll_encounter("cinder_warrens", "#", rng=self._always_rng())
        assert result is None

    def test_no_encounter_on_named_location(self):
        result = roll_encounter("cinder_warrens", "*", rng=self._always_rng())
        assert result is None

    def test_encounter_miss(self):
        result = roll_encounter("cinder_warrens", ".", rng=self._never_rng())
        assert result is None

    def test_warren_raider_is_tunnel_encounter(self):
        result = roll_encounter("cinder_warrens", ".", rng=self._always_rng())
        assert result is not None
        assert result.mob_key == "warren_raider"

    def test_slag_hound_is_salvage_encounter(self):
        result = roll_encounter("cinder_warrens", "s", rng=self._always_rng())
        assert result is not None
        assert result.mob_key == "slag_hound"

    def test_generator_housing_higher_encounter_rate_than_tunnel(self):
        # Generator housing ('g') should have a higher single encounter chance than tunnel ('.').
        g_chance = max(e.chance_per_step for e in CINDER_WARRENS_TERRAIN["g"].encounters)
        dot_chance = max(e.chance_per_step for e in CINDER_WARRENS_TERRAIN["."].encounters)
        assert g_chance >= dot_chance


# ---------------------------------------------------------------------------
# Cinder Warrens — named location resolution tests
# ---------------------------------------------------------------------------

class TestCinderWarrensNamedLocations:
    """Test get_named_location on the Cinder Warrens mini-overworld."""

    def test_entry_hatch_resolves(self):
        loc = get_named_location("cinder_warrens", 10, 0, CW)
        assert loc is not None
        assert loc["room_key"] == "helion_warrens_entry"

    def test_warrens_core_resolves(self):
        loc = get_named_location("cinder_warrens", 5, 8, CW)
        assert loc is not None
        assert loc["room_key"] == "helion_warrens_core"

    def test_scrapforge_resolves(self):
        loc = get_named_location("cinder_warrens", 14, 11, CW)
        assert loc is not None
        assert loc["room_key"] == "helion_warrens_forge"

    def test_non_location_returns_none(self):
        loc = get_named_location("cinder_warrens", 10, 1, CW)
        assert loc is None

    def test_out_of_bounds_returns_none(self):
        loc = get_named_location("cinder_warrens", 99, 99, CW)
        assert loc is None


# ---------------------------------------------------------------------------
# Cinder Warrens — room description generation
# ---------------------------------------------------------------------------

class TestCinderWarrensRoomDescription:
    """Test generate_room_description on the Cinder Warrens mini-overworld."""

    def test_returns_string(self):
        desc = generate_room_description(
            "cinder_warrens", "Cinder Warrens", CW["map"], 10, 1, CW, colour=False
        )
        assert isinstance(desc, str) and len(desc) > 0

    def test_contains_area_name(self):
        desc = generate_room_description(
            "cinder_warrens", "Cinder Warrens", CW["map"], 10, 1, CW, colour=False
        )
        assert "Cinder Warrens" in desc

    def test_contains_exits_line(self):
        desc = generate_room_description(
            "cinder_warrens", "Cinder Warrens", CW["map"], 10, 1, CW, colour=False
        )
        assert "Exits:" in desc

    def test_named_location_shows_enter_hint(self):
        desc = generate_room_description(
            "cinder_warrens", "Cinder Warrens", CW["map"], 10, 0, CW, colour=False
        )
        assert "enter" in desc.lower()

    def test_no_crash_at_edge(self):
        desc = generate_room_description(
            "cinder_warrens", "Cinder Warrens", CW["map"], 0, 0, CW, colour=False
        )
        assert isinstance(desc, str)
