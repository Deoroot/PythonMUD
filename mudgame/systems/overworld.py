"""Overworld system — terrain definitions, map rendering, encounter logic.

Architecture:
  * One OverworldRoom Evennia object exists for the kael_cluster (The Shardfield).
  * Player position is stored in caller.db.overworld_pos = {"planet": str, "x": int, "y": int}.
  * Terrain and encounter data live in this module (pure Python, no Evennia).
  * The unified 80×32 grid lives in world_data.WORLD_DATA["overworld"]["kael_cluster"]["map"].
    - x=0–31:  Helion Reach   (HELION_TERRAIN)
    - x=32–47: Asteroid Void  (VOID_TERRAIN)   ← impassable on foot
    - x=48–79: Vanta IX       (VANTA_TERRAIN)

Terrain glyphs
--------------
Helion Reach (x<32):  . h m f w r i = ~ c *
Asteroid Void (32≤x<48): : (debris, impassable)  = (tradelane, impassable)
Vanta IX (x≥48):      . f h m ~ a R = s c *

Special glyphs (shared):
  *  Named Location (gateway to instanced area)
  m  Mountain / Void Peak — impassable
  ~  Toxin Flats / Null Sea — impassable

get_terrain_def() accepts an optional *x* keyword argument used for kael_cluster
x-dispatch.  All callers that may be on kael_cluster should pass x=<col>.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Optional

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class EncounterEntry:
    """One entry in a terrain encounter table."""

    mob_key: str           # key used to identify the mob template
    chance_per_step: float # 0.0–1.0 probability each move step
    aggro: bool            # True → mob attacks after aggro_delay
    aggro_delay: int       # rounds (3 s each) before attack; 0 = instant


@dataclass
class TerrainDef:
    """Definition for a single terrain glyph."""

    glyph: str
    name: str
    desc: str                          # one-sentence flavour used in room description
    passable: bool = True
    impassable_msg: str = ""           # shown when player tries to enter
    encounters: list[EncounterEntry] = field(default_factory=list)
    stamina_cost: int = 0              # stamina drained each step on this terrain (0 = free)


# ---------------------------------------------------------------------------
# Helion Reach terrain definitions
# ---------------------------------------------------------------------------

HELION_TERRAIN: dict[str, TerrainDef] = {
    ".": TerrainDef(
        glyph=".",
        name="Dust Flats",
        desc=(
            "A wide expanse of pale amber dust, cracked and windswept. "
            "The silence here is heavy — only the scrape of grit across your boots."
        ),
        encounters=[
            EncounterEntry("ow_dust_scavenger", 0.15, aggro=False, aggro_delay=0),
            EncounterEntry("ow_plains_raider",  0.10, aggro=True,  aggro_delay=1),
        ],
    ),
    "h": TerrainDef(
        glyph="h",
        name="Shale Ridge",
        desc=(
            "A series of broken shale ridges — sharp footing, short sightlines. "
            "Nothing comfortable here, but the cover draws opportunists."
        ),
        encounters=[
            EncounterEntry("ow_shale_ambusher", 0.18, aggro=True, aggro_delay=0),
            EncounterEntry("ow_shale_crawler",  0.20, aggro=True,  aggro_delay=0),
        ],
        stamina_cost=2,
    ),
    "m": TerrainDef(
        glyph="m",
        name="Mountain Peak",
        desc="Sheer rock faces rise thousands of metres — no path leads through.",
        passable=False,
        impassable_msg="The mountain peak is sheer and impassable.",
    ),
    "f": TerrainDef(
        glyph="f",
        name="Scrubland",
        desc=(
            "Twisted shrubs and brittle grass cling to cracked earth. "
            "Something moves in the underbrush — you can't tell what."
        ),
        encounters=[
            EncounterEntry("ow_dust_scavenger", 0.10, aggro=False, aggro_delay=0),
            EncounterEntry("ow_scrub_predator", 0.12, aggro=True,  aggro_delay=1),
        ],
    ),
    "w": TerrainDef(
        glyph="w",
        name="Wasteland",
        desc=(
            "Scorched terrain stripped of all life. Debris from an old industrial collapse "
            "juts from the ground at irregular intervals."
        ),
        encounters=[
            EncounterEntry("ow_plains_raider",   0.18, aggro=True,  aggro_delay=0),
            EncounterEntry("ow_waste_scavenger", 0.12, aggro=False, aggro_delay=0),
        ],
        stamina_cost=1,
    ),
    "r": TerrainDef(
        glyph="r",
        name="Runoff Channel",
        desc=(
            "A shallow gully where chemical runoff once pooled. "
            "The ground is stained rust-red; the air tastes metallic."
        ),
        encounters=[
            EncounterEntry("ow_runoff_lurker", 0.22, aggro=True, aggro_delay=1),
        ],
        stamina_cost=1,
    ),
    "i": TerrainDef(
        glyph="i",
        name="Industrial Ruins",
        desc=(
            "The skeleton of a collapsed processing facility. "
            "Rusted struts and shattered wall panels create a maze of cover and dead ends."
        ),
        encounters=[
            EncounterEntry("ow_ruin_scavenger",  0.15, aggro=False, aggro_delay=0),
            EncounterEntry("ow_scrap_enforcer",  0.18, aggro=True,  aggro_delay=0),
        ],
        stamina_cost=1,
    ),
    "=": TerrainDef(
        glyph="=",
        name="Trade Road",
        desc=(
            "A maintained stretch of compressed regolith reinforced with duracrete panels. "
            "The easiest path between settlements — but not the safest."
        ),
        encounters=[
            EncounterEntry("ow_road_brigand", 0.12, aggro=True, aggro_delay=1),
        ],
    ),
    "~": TerrainDef(
        glyph="~",
        name="Toxin Flats",
        desc="A low plain of yellowish chemical deposit — acrid and lethal to traverse unprotected.",
        passable=False,
        impassable_msg="The toxin flats are impassable without hazard gear.",
    ),
    "c": TerrainDef(
        glyph="c",
        name="Settlement",
        desc=(
            "A cluster of prefab structures surrounded by a low perimeter wall. "
            "A few colonists move between shelters. The lights are on."
        ),
        encounters=[],  # settlements are safe
    ),
    "*": TerrainDef(
        glyph="*",
        name="Named Location",
        desc="A gateway to a known area.",
        encounters=[],
    ),
}

# ---------------------------------------------------------------------------
# Vanta IX terrain definitions
# ---------------------------------------------------------------------------

VANTA_TERRAIN: dict[str, TerrainDef] = {
    ".": TerrainDef(
        glyph=".",
        name="Glass Dunes",
        desc=(
            "Smooth dunes of pulverised silicate glass, fused into a pale, "
            "reflective surface by ancient heat. The horizon shimmers."
        ),
        encounters=[
            EncounterEntry("ow_glass_stalker",   0.18, aggro=True,  aggro_delay=1),
            EncounterEntry("ow_dune_scavenger",  0.10, aggro=False, aggro_delay=0),
        ],
        stamina_cost=1,
    ),
    "f": TerrainDef(
        glyph="f",
        name="Crystal Spires",
        desc=(
            "Tall crystal formations jut from the ground at odd angles, "
            "chiming faintly in the wind. The resonance is disorienting."
        ),
        encounters=[
            EncounterEntry("ow_spire_wasp",    0.20, aggro=True, aggro_delay=0),
            EncounterEntry("ow_crystal_hermit", 0.08, aggro=False, aggro_delay=0),
        ],
        stamina_cost=2,
    ),
    "h": TerrainDef(
        glyph="h",
        name="Obsidian Hills",
        desc=(
            "Black volcanic rock worn smooth by centuries of wind erosion. "
            "Footing is secure but the terrain offers no cover."
        ),
        encounters=[
            EncounterEntry("ow_obsidian_predator", 0.18, aggro=True, aggro_delay=0),
        ],
        stamina_cost=2,
    ),
    "m": TerrainDef(
        glyph="m",
        name="Void Peak",
        desc="Black peaks that pierce the upper atmosphere — there is no way through.",
        passable=False,
        impassable_msg="The void peaks are sheer and impassable.",
    ),
    "~": TerrainDef(
        glyph="~",
        name="Null Sea",
        desc="A dead, flat expanse of inert mineral salt. Nothing lives here; nothing can.",
        passable=False,
        impassable_msg="The null sea is impassable — no traction on the mineral crust.",
    ),
    "a": TerrainDef(
        glyph="a",
        name="Anomaly Zone",
        desc=(
            "Space warps subtly here — distant objects appear closer, sounds arrive late. "
            "PSI-sensitive individuals feel it as pressure behind the eyes."
        ),
        encounters=[
            EncounterEntry("ow_anomaly_wraith",  0.22, aggro=True,  aggro_delay=0),
            EncounterEntry("ow_psi_fragment",    0.15, aggro=False, aggro_delay=0),
        ],
        stamina_cost=3,
    ),
    "R": TerrainDef(
        glyph="R",
        name="Ancient Ruins",
        desc=(
            "Shattered walls of a pre-colony structure, alien in proportion. "
            "Inscriptions survive on scattered blocks, language unrecognised."
        ),
        encounters=[
            EncounterEntry("ow_ruin_guardian",   0.20, aggro=True,  aggro_delay=0),
            EncounterEntry("ow_ruin_scavenger",  0.12, aggro=False, aggro_delay=0),
        ],
        stamina_cost=1,
    ),
    "=": TerrainDef(
        glyph="=",
        name="Carved Path",
        desc=(
            "A smooth path cut by clan labourers through the glass and rock. "
            "Efficient and fast, though exposed."
        ),
        encounters=[
            EncounterEntry("ow_path_enforcer", 0.10, aggro=True, aggro_delay=1),
        ],
    ),
    "s": TerrainDef(
        glyph="s",
        name="Shattered Ground",
        desc=(
            "The ground here is cracked into irregular blocks by seismic activity. "
            "Each step requires care; a stumble means a fall into a dark fissure."
        ),
        encounters=[
            EncounterEntry("ow_fissure_stalker", 0.20, aggro=True, aggro_delay=0),
        ],
        stamina_cost=2,
    ),
    "c": TerrainDef(
        glyph="c",
        name="Clan Outpost",
        desc=(
            "A fortified clan position — thick walls of compressed glass aggregate "
            "and recycled hull plating. Clan colours hang at the gate."
        ),
        encounters=[],
    ),
    "*": TerrainDef(
        glyph="*",
        name="Named Location",
        desc="A gateway to a known area.",
        encounters=[],
    ),
}

# ---------------------------------------------------------------------------
# Void / Asteroid Field terrain definitions (kael_cluster x=32–47)
# ---------------------------------------------------------------------------

VOID_TERRAIN: dict[str, TerrainDef] = {
    ":": TerrainDef(
        glyph=":",
        name="Asteroid Debris",
        desc="A dense field of tumbling rock and ice — utterly impassable on foot.",
        passable=False,
        impassable_msg="The asteroid debris field is impassable on foot. You need a ship.",
    ),
    "=": TerrainDef(
        glyph="=",
        name="Tradelane",
        desc=(
            "A marked ship corridor through the asteroid field. "
            "NPC transports use this route."
        ),
        passable=False,
        impassable_msg="The tradelane is for ships only. Board a transport to cross.",
    ),
}

# ---------------------------------------------------------------------------
# Glass Dunes Ruins area mini-overworld terrain definitions
# ---------------------------------------------------------------------------

GLASS_DUNES_TERRAIN: dict[str, TerrainDef] = {
    ".": TerrainDef(
        glyph=".",
        name="Open Dune Floor",
        desc=(
            "A smooth expanse of fused silicate glass, pale and reflective underfoot. "
            "The ruins are quiet here — but the glass carries sound further than it should."
        ),
        encounters=[
            EncounterEntry("glass_stalker", 0.15, aggro=True,  aggro_delay=1),
        ],
        stamina_cost=1,
    ),
    "f": TerrainDef(
        glyph="f",
        name="Crystal Formation",
        desc=(
            "Irregular crystal clusters jut from the dune floor, chiming faintly with "
            "harmonic resonance. Something sensitive to that frequency uses them to hunt."
        ),
        encounters=[
            EncounterEntry("glass_stalker", 0.22, aggro=True,  aggro_delay=0),
        ],
        stamina_cost=2,
    ),
    "R": TerrainDef(
        glyph="R",
        name="Ruin Structure",
        desc=(
            "Collapsed walls and fractured archways of a pre-colony structure. "
            "Inscriptions on scattered blocks remain unread. Movement echoes strangely here."
        ),
        encounters=[
            EncounterEntry("glass_stalker",  0.18, aggro=True,  aggro_delay=0),
            EncounterEntry("dock_saboteur",  0.10, aggro=True,  aggro_delay=1),
        ],
        stamina_cost=1,
    ),
    "s": TerrainDef(
        glyph="s",
        name="Shattered Glass Floor",
        desc=(
            "The floor here is a field of fractured glass plates, edges upturned. "
            "Each step grinds and shifts. The instability makes withdrawal difficult — "
            "and Glass Stalkers have learned to wait in the debris."
        ),
        encounters=[
            EncounterEntry("glass_stalker", 0.25, aggro=True, aggro_delay=0),
        ],
        stamina_cost=2,
    ),
    "m": TerrainDef(
        glyph="m",
        name="Crystal Wall",
        desc="A dense formation of fused crystal — no gap, no footing, no way through.",
        passable=False,
        impassable_msg="The crystal wall is solid and impassable.",
    ),
    "*": TerrainDef(
        glyph="*",
        name="Named Location",
        desc="A recognisable structure within the ruins.",
        encounters=[],
    ),
}

# ---------------------------------------------------------------------------
# Cinder Warrens area mini-overworld terrain definitions
# ---------------------------------------------------------------------------

CINDER_WARRENS_TERRAIN: dict[str, TerrainDef] = {
    ".": TerrainDef(
        glyph=".",
        name="Tunnel Corridor",
        desc=(
            "A low, durasteel-lined passage — cabling runs overhead in bundled conduit. "
            "The air is hot and smells of machine oil. Sound carries unpredictably."
        ),
        encounters=[
            EncounterEntry("warren_raider", 0.15, aggro=True,  aggro_delay=1),
        ],
    ),
    "g": TerrainDef(
        glyph="g",
        name="Generator Housing",
        desc=(
            "Massive generator units line the walls, humming at high frequency. "
            "Heat radiates from exposed coolant lines. Something is using these as cover."
        ),
        encounters=[
            EncounterEntry("warren_raider", 0.20, aggro=True,  aggro_delay=0),
        ],
    ),
    "s": TerrainDef(
        glyph="s",
        name="Salvage Pile",
        desc=(
            "Heaps of stripped components and fused slag — stripped from derelict "
            "fabrication platforms. Unstable footing. Slag Hounds nest in the debris."
        ),
        encounters=[
            EncounterEntry("slag_hound", 0.22, aggro=True, aggro_delay=0),
        ],
        stamina_cost=2,
    ),
    "d": TerrainDef(
        glyph="d",
        name="Heat Duct",
        desc=(
            "A wide industrial duct venting superheated air from the lower machinery. "
            "The floor is warm underfoot; the air shimmers. Footing is treacherous."
        ),
        encounters=[
            EncounterEntry("slag_hound", 0.18, aggro=True, aggro_delay=1),
        ],
        stamina_cost=2,
    ),
    "#": TerrainDef(
        glyph="#",
        name="Collapsed Passage",
        desc="A section of tunnel collapsed under its own weight — rubble floor to ceiling.",
        passable=False,
        impassable_msg="The collapsed passage is completely blocked by rubble.",
    ),
    "*": TerrainDef(
        glyph="*",
        name="Named Location",
        desc="A recognisable structure within the warrens.",
        encounters=[],
    ),
}

# Map planet key → terrain dict
# "kael_cluster" entry is a merged legend dict used for display only;
# actual gameplay terrain lookup uses get_terrain_def() with x-dispatch.
PLANET_TERRAIN: dict[str, dict[str, TerrainDef]] = {
    "helion_reach":     HELION_TERRAIN,       # legacy key — kept for test compat
    "vanta_ix":         VANTA_TERRAIN,        # legacy key — kept for test compat
    "kael_cluster":     {**VANTA_TERRAIN, **HELION_TERRAIN, **VOID_TERRAIN},
    "glass_dunes_ruins": GLASS_DUNES_TERRAIN,
    "cinder_warrens":   CINDER_WARRENS_TERRAIN,
}

# ---------------------------------------------------------------------------
# Direction helpers
# ---------------------------------------------------------------------------

#: Maps compass name → (dx, dy) where +x is east, +y is south (row index).
DIRECTIONS: dict[str, tuple[int, int]] = {
    "n":  ( 0, -1),
    "ne": ( 1, -1),
    "e":  ( 1,  0),
    "se": ( 1,  1),
    "s":  ( 0,  1),
    "sw": (-1,  1),
    "w":  (-1,  0),
    "nw": (-1, -1),
}

DIRECTION_NAMES: dict[str, str] = {
    "n":  "north",
    "ne": "northeast",
    "e":  "east",
    "se": "southeast",
    "s":  "south",
    "sw": "southwest",
    "w":  "west",
    "nw": "northwest",
}

# ---------------------------------------------------------------------------
# Core lookup helpers
# ---------------------------------------------------------------------------


def get_terrain_def(planet_key: str, glyph: str, x: int = 0) -> TerrainDef:
    """Return the TerrainDef for *glyph* on *planet_key*.

    For ``planet_key == "kael_cluster"`` the *x* coordinate selects the
    correct sub-terrain:
      * x <  32  → Helion Reach  (HELION_TERRAIN)
      * 32 ≤ x < 48 → Asteroid Void (VOID_TERRAIN)
      * x ≥  48  → Vanta IX     (VANTA_TERRAIN)

    Falls back to a generic passable TerrainDef for unknown glyphs.
    """
    if planet_key == "kael_cluster":
        if x < 32:
            terrain_map: dict[str, TerrainDef] = HELION_TERRAIN
        elif x < 48:
            terrain_map = VOID_TERRAIN
        else:
            terrain_map = VANTA_TERRAIN
    else:
        terrain_map = PLANET_TERRAIN.get(planet_key, HELION_TERRAIN)
    if glyph in terrain_map:
        return terrain_map[glyph]
    return TerrainDef(glyph=glyph, name="Unknown Terrain", desc="Featureless ground.")


def get_glyph(planet_map: list[str], x: int, y: int) -> str:
    """Return the single-character glyph at grid position (x, y).

    x is the column (east), y is the row (south).  Returns " " for
    out-of-bounds positions.
    """
    if y < 0 or y >= len(planet_map):
        return " "
    row = planet_map[y]
    if x < 0 or x >= len(row):
        return " "
    return row[x]


def get_available_exits(
    planet_key: str,
    planet_map: list[str],
    x: int,
    y: int,
) -> list[str]:
    """Return a list of direction keys that are in-bounds and passable."""
    result = []
    for direction, (dx, dy) in DIRECTIONS.items():
        nx, ny = x + dx, y + dy
        glyph = get_glyph(planet_map, nx, ny)
        if glyph == " ":
            continue
        tdef = get_terrain_def(planet_key, glyph, x=nx)
        if tdef.passable:
            result.append(direction)
    return result


# ---------------------------------------------------------------------------
# Named location resolution
# ---------------------------------------------------------------------------


def get_named_location(
    planet_key: str,
    x: int,
    y: int,
    overworld_data: dict,
) -> Optional[dict]:
    """Return the named location entry at (x, y) for *planet_key*, or None.

    *overworld_data* is WORLD_DATA["overworld"][planet_key].
    Named location dicts have keys: name, room_key, x, y, desc.
    """
    for loc in overworld_data.get("named_locations", []):
        if loc["x"] == x and loc["y"] == y:
            return loc
    return None


# ---------------------------------------------------------------------------
# Encounter rolling
# ---------------------------------------------------------------------------


def roll_encounter(
    planet_key: str,
    glyph: str,
    rng: Optional[random.Random] = None,
    x: int = 0,
) -> Optional[EncounterEntry]:
    """Roll for an encounter on the given terrain.

    Returns an EncounterEntry if an encounter is triggered, or None.
    Multiple entries are checked independently; the first that triggers wins.
    Uses *rng* if supplied (for deterministic tests), otherwise random.random().
    *x* is passed to get_terrain_def() for kael_cluster x-dispatch.
    """
    tdef = get_terrain_def(planet_key, glyph, x=x)
    _random = rng.random if rng is not None else random.random
    for entry in tdef.encounters:
        if _random() < entry.chance_per_step:
            return entry
    return None


# ---------------------------------------------------------------------------
# Mini-map rendering
# ---------------------------------------------------------------------------

# Viewport size (tiles visible around the player).
_MAP_HALF_W = 6   # 6 left + player + 6 right = 13 wide
_MAP_HALF_H = 4   # 4 above + player + 4 below  = 9 tall

# ANSI colour codes for glyphs (terminal-safe; no Evennia dependency).
# _GLYPH_COLOUR is the shared fallback used for non-kael_cluster worlds and
# for special glyphs (@, *) that appear in every zone.
_GLYPH_COLOUR: dict[str, str] = {
    ".":  "\033[33m",   # amber      — dust/glass (generic)
    "h":  "\033[37m",   # light grey — shale/obsidian (generic)
    "m":  "\033[90m",   # dark grey  — mountains (generic, impassable)
    "f":  "\033[32m",   # green      — scrubland/spires (generic)
    "w":  "\033[31m",   # dark red   — wasteland (generic)
    "r":  "\033[31m",   # dark red   — runoff (generic)
    "i":  "\033[90m",   # dark grey  — industrial ruins (generic)
    "=":  "\033[36m",   # cyan       — roads/paths (generic)
    "~":  "\033[34m",   # blue       — toxin/null sea (generic, impassable)
    "c":  "\033[93m",   # gold       — settlement/outpost (generic)
    "a":  "\033[35m",   # magenta    — anomaly zone (generic)
    "R":  "\033[90m",   # dark grey  — ancient ruins (generic)
    "s":  "\033[37m",   # light grey — shattered ground (generic)
    ":":  "\033[90m",   # dark grey  — asteroid debris (generic)
    "g":  "\033[90m",   # dark grey  — generator housing (cinder warrens)
    "d":  "\033[31m",   # dark red   — heat duct (cinder warrens)
    "#":  "\033[90m",   # dark grey  — collapsed passage (cinder warrens)
    "*":  "\033[97m",   # bright white — named location
    "@":  "\033[92m",   # bright green — player
}

# Zone-specific colour palettes for the unified kael_cluster grid.
# Helion Reach (x < 32): warm, arid — amber, red, green
_HELION_GLYPH_COLOUR: dict[str, str] = {
    ".":  "\033[33m",   # amber        — Dust Flats
    "h":  "\033[37m",   # light grey   — Shale Ridge
    "m":  "\033[90m",   # dark grey    — Mountain Peak (impassable)
    "f":  "\033[32m",   # green        — Scrubland
    "w":  "\033[91m",   # bright red   — Wasteland
    "r":  "\033[31m",   # dark red     — Runoff Channel
    "i":  "\033[36m",   # cyan         — Industrial Ruins
    "=":  "\033[96m",   # bright cyan  — Trade Road
    "~":  "\033[34m",   # blue         — Toxin Flats (impassable)
    "c":  "\033[93m",   # gold         — Settlement
    "*":  "\033[97m",   # bright white — Named Location
    "@":  "\033[92m",   # bright green — Player
}

# Vanta IX (x >= 48): alien, cool — cyan, magenta, dark
_VANTA_GLYPH_COLOUR: dict[str, str] = {
    ".":  "\033[96m",   # bright cyan    — Glass Dunes
    "f":  "\033[95m",   # bright magenta — Crystal Spires
    "h":  "\033[90m",   # dark grey      — Obsidian Hills
    "m":  "\033[90m",   # dark grey      — Void Peak (impassable)
    "~":  "\033[34m",   # blue           — Null Sea (impassable)
    "a":  "\033[35m",   # magenta        — Anomaly Zone
    "R":  "\033[33m",   # amber          — Ancient Ruins
    "=":  "\033[96m",   # bright cyan    — Carved Path
    "s":  "\033[37m",   # light grey     — Shattered Ground
    "c":  "\033[93m",   # gold           — Clan Outpost
    "*":  "\033[97m",   # bright white   — Named Location
    "@":  "\033[92m",   # bright green   — Player
}

# Asteroid Void (32 <= x < 48): dark, foreboding
_VOID_GLYPH_COLOUR: dict[str, str] = {
    ":":  "\033[90m",   # dark grey    — Asteroid Debris (impassable)
    "=":  "\033[36m",   # cyan         — Tradelane (ships only)
    "*":  "\033[97m",   # bright white — Named Location
    "@":  "\033[92m",   # bright green — Player
}

_RESET = "\033[0m"
_BORDER_COLOUR = "\033[36m"   # cyan borders


def _colour(glyph: str, x: int = -1, planet_key: str = "") -> str:
    """Return an ANSI-coloured glyph string.

    When *planet_key* is ``"kael_cluster"`` and *x* >= 0, the colour is
    chosen from the appropriate zone palette:
      * x <  32  → _HELION_GLYPH_COLOUR
      * 32 ≤ x < 48 → _VOID_GLYPH_COLOUR
      * x ≥  48  → _VANTA_GLYPH_COLOUR
    Falls back to _GLYPH_COLOUR for unknown glyphs in any zone.
    All other planet keys use _GLYPH_COLOUR directly.
    """
    if planet_key == "kael_cluster" and x >= 0:
        if x < 32:
            zone_dict = _HELION_GLYPH_COLOUR
        elif x < 48:
            zone_dict = _VOID_GLYPH_COLOUR
        else:
            zone_dict = _VANTA_GLYPH_COLOUR
        col = zone_dict.get(glyph) or _GLYPH_COLOUR.get(glyph, "")
    else:
        col = _GLYPH_COLOUR.get(glyph, "")
    return f"{col}{glyph}{_RESET}" if col else glyph


def render_minimap(
    planet_map: list[str],
    player_x: int,
    player_y: int,
    colour: bool = True,
    planet_key: str = "",
) -> list[str]:
    """Render a 13×9 viewport of the map centred on the player.

    Returns a list of strings (one per row), each 13 chars wide
    (plus ANSI codes if colour=True).  The player is shown as '@'.

    *planet_key* is passed to :func:`_colour` to enable zone-aware
    colouring for ``"kael_cluster"`` grids.

    The border rows ('<------^------>' / '<------v------>') are NOT
    included here — they are added by the caller so the room description
    text can be appended beside the map.
    """
    rows: list[str] = []
    for dy in range(-_MAP_HALF_H, _MAP_HALF_H + 1):
        row_chars = []
        for dx in range(-_MAP_HALF_W, _MAP_HALF_W + 1):
            gx = player_x + dx
            gy = player_y + dy
            if dx == 0 and dy == 0:
                ch = _colour("@", x=player_x, planet_key=planet_key) if colour else "@"
            else:
                glyph = get_glyph(planet_map, gx, gy)
                ch = _colour(glyph, x=gx, planet_key=planet_key) if colour else glyph
            row_chars.append(ch)
        rows.append("".join(row_chars))
    return rows


def render_minimap_plain(
    planet_map: list[str],
    player_x: int,
    player_y: int,
) -> list[str]:
    """Return a plain-text (no ANSI) 13×9 map viewport.  Useful for tests."""
    return render_minimap(planet_map, player_x, player_y, colour=False)


def render_full_display(
    planet_name: str,
    planet_map: list[str],
    player_x: int,
    player_y: int,
    terrain_name: str,
    room_desc: str,
    named_loc_name: Optional[str] = None,
    planet_key: str = "",
    colour: bool = True,
) -> str:
    """Compose the full overworld display string.

    Layout::

        <--- Helion Reach --->
        <------^------>  |  Dust Flats (15, 8)
        .......@.......  |  A wide expanse of pale amber dust...
        ...............  |
        ...............  |  [Spaceport - enter to access]
        <------v------>  |

    The map portion is 13 chars wide; separator is '  |  '; text portion is 45
    chars wide (soft-wrapped).  Total line width ~65 chars.
    """
    _bc = _BORDER_COLOUR if colour else ""
    _rc = _RESET if colour else ""

    map_rows = render_minimap(planet_map, player_x, player_y, colour=colour, planet_key=planet_key)

    # Build text lines for the right column.
    header_text = f"{terrain_name} ({player_x}, {player_y})"
    text_lines: list[str] = [header_text, room_desc]
    if named_loc_name:
        text_lines.append("")
        text_lines.append(f"[{named_loc_name} — type 'enter' to access]")

    # Pad text to match map height (9 rows).
    while len(text_lines) < len(map_rows):
        text_lines.append("")

    top_border    = f"{_bc}<------^------>{_rc}"
    bottom_border = f"{_bc}<------v------>{_rc}"
    sep           = "  |  "

    title_line = f"{_bc}<--- {planet_name} --->{_rc}"

    lines: list[str] = [title_line]
    lines.append(f"{top_border}{sep}{text_lines[0]}")
    for i, map_row in enumerate(map_rows):
        txt = text_lines[i + 1] if (i + 1) < len(text_lines) else ""
        lines.append(f"{map_row}{sep}{txt}")
    lines.append(f"{bottom_border}{sep}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Room description generation
# ---------------------------------------------------------------------------


def generate_room_description(
    planet_key: str,
    planet_name: str,
    planet_map: list[str],
    x: int,
    y: int,
    overworld_data: dict,
    colour: bool = True,
) -> str:
    """Generate the full room description string for position (x, y).

    This is the string sent to the player when they look or move.
    """
    glyph = get_glyph(planet_map, x, y)
    tdef = get_terrain_def(planet_key, glyph, x=x)

    named_loc = get_named_location(planet_key, x, y, overworld_data)
    named_loc_name = named_loc["name"] if named_loc else None

    exits = get_available_exits(planet_key, planet_map, x, y)
    exit_str = "  ".join(d.upper() for d in sorted(exits)) if exits else "none"

    display = render_full_display(
        planet_name=planet_name,
        planet_map=planet_map,
        player_x=x,
        player_y=y,
        terrain_name=tdef.name,
        room_desc=tdef.desc,
        named_loc_name=named_loc_name,
        planet_key=planet_key,
        colour=colour,
    )

    return f"{display}\nExits: {exit_str}"
