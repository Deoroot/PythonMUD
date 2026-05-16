"""Editable world/content data for the initial vertical slice."""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Unified Shardfield (kael_cluster) — 80×32 grid construction helpers
# Helion Reach occupies x=0–31, void (asteroid field) x=32–47, Vanta IX x=48–79.
# ---------------------------------------------------------------------------

_HR_ROWS: list[str] = [
    "mmmmhh.f" ".f......" "....fhhh" "mmmmmmm.",  # y=0
    "mmmhh..f" ".f......" "....fhh." "mmmmmmmm",  # y=1
    "mmhh...f" ".f......" "....fhh." "mmmmmmm.",  # y=2
    "mhh....f" ".f......" "....fhh." "mmmmmm..",  # y=3
    ".h....f." ".f.....=" "....ch.." "mmmmm...",  # y=4
    ".h....f." ".f.....*" "....ch.." "mmmmm...",  # y=5  Helion Spaceport *
    ".h....f." ".f.....=" "....ch.." "mmmmm...",  # y=6
    ".f.....f" ".f.....=" "..f.ch.." "mmmmm...",  # y=7
    ".f.....f" ".f.....=" "..f.ch.." "ww.mmm..",  # y=8
    ".f.....f" ".f.....=" "..f.chw." "ww.wmm..",  # y=9
    ".f....f." ".f.....=" ".ff.chw." "www.mm..",  # y=10
    ".f...f.." ".f.....=" "fff.cww." "www.w...",  # y=11
    ".f..f..." ".f.....=" "fff.cww." "www.w...",  # y=12
    ".f.f...." ".f.....=" "fff.cwww" "wwwwi...",  # y=13
    ".f.f...." ".f.....=" "=======*" "wwwwiii.",  # y=14  Iron Covenant *
    ".f......" ".......w" "ww.....w" "wwwwiii.",  # y=15
    ".f......" ".......w" "ww..c..w" "wwwwiii.",  # y=16
    ".f..c..." ".......w" "ww....wi" "wwwwiiii",  # y=17
    ".f..c..." "..r....w" "ww...wii" "wwwwiiii",  # y=18
    "ff..c..." ".rr....w" "w....wii" ".wwwiiii",  # y=19
    "ff......" ".rr....." ".....wii" ".wwwiiii",  # y=20
    "ff......" "*...rii." "i...wiii" ".wwwiiii",  # y=21  Helion Warrens *
    "ff......" "r.....i." "i...wiii" "~wwwiiii",  # y=22
    "fff....." "rr....ii" "ii..wiii" "~~wwiii.",  # y=23
    "ff......" "rr....ii" "ii..~~~~" "~~~~iii.",  # y=24
    "f......." "rrr..iii" "ii..~~~~" "~~~~~ii.",  # y=25
    "f......." "rrr..iii" "iii~~~~~" "~~~~~~~.",  # y=26
    "........" "rrrr.iii" "~~~~...." "~~~~~~~.",  # y=27
    "........" "rrrr~~~~" "~~~~~~~~" "~~~~~~~.",  # y=28
    "........" "~~~~~~~~" "~~~~~~~~" "~~~~~~~.",  # y=29
    "........" "~~~~~~~~" "~~~~~~~~" "~~~~~~~.",  # y=30
    "........" "~~~~~~~~" "~~~~~~~~" "~~~~~~~.",  # y=31
]

_VX_ROWS: list[str] = [
    "mmmhhhh." ".f......" "s...hhhh" "mmmmmmmm",  # y=0
    "mmhhhh.." ".f......" "s...hhhm" "mmmmmmmm",  # y=1
    "mhhhh..." ".f......" "s...hh.." "mmmmmmmm",  # y=2
    "mhhh...." ".f......" "s...hh.." "mmmmmmm.",  # y=3
    ".hhh...f" ".f.....=" "s..fhh.." "mmmmm...",  # y=4
    ".hhh...f" ".f.....*" "s..fhh.." "mmmmm...",  # y=5  Vanta Customs *
    ".hhh...f" ".f.....=" "...fhh.." "mmmmm...",  # y=6
    ".ff....f" ".f.....=" "...fsh.." "mmmm....",  # y=7
    ".ff....f" ".f.....=" "...fss.." "mmmm....",  # y=8
    ".ff....f" "af.....=" "...fsss." "mmm.....",  # y=9
    ".ff...a." "af.....=" "...fsss." "mm......",  # y=10
    ".ff..aa." "af.....=" "..ffsss." "mm......",  # y=11
    ".ff.aaa." "af.....=" ".fRfsss." "m.......",  # y=12
    ".ffaaa.." "af.....=" "fRRfss.." "m.......",  # y=13
    ".ff....*" "af.....=" "fRRfss.." "m...c...",  # y=14  PSI Weavers *
    ".fff...." "af......" "RRRfss.." "m...c...",  # y=15
    ".fff...." "af......" "RRRRss.." "........",  # y=16
    ".fff...." "af......" "RRRRss.." "....c...",  # y=17
    ".fff...." ".f......" "RRRRsss." "....c...",  # y=18
    ".fff...." ".f......" "RRRssss." "....c...",  # y=19
    ".fff...." ".f......" "ssssss.." "........",  # y=20
    ".fff...." ".f......" "RRssss.." "........",  # y=21
    ".ff....." ".f......" "RRssss*." "~...c...",  # y=22  Glass Dunes *
    ".ff....." "........" "RRssss~." "~~..c...",  # y=23
    ".f......" "........" "sssss~~~" "~~~.....",  # y=24
    ".f......" "........" "ssss~~~~" "~~~~~~~~",  # y=25
    "........" "........" "~~~~...." "~~~~~~~~",  # y=26
    "........" "~~~~~~~~" "~~~~~~~~" "~~~~~~~~",  # y=27
    "........" "~~~~~~~~" "~~~~~~~~" "~~~~~~~~",  # y=28
    "........" "~~~~~~~~" "~~~~~~~~" "~~~~~~~~",  # y=29
    "~~~~~~~~" "~~~~~~~~" "~~~~~~~~" "~~~~~~~~",  # y=30
    "~~~~~~~~" "~~~~~~~~" "~~~~~~~~" "~~~~~~~~",  # y=31
]

# Void section: 16 cols of asteroid debris `:`, except y=20 (tradelane `=`)
_VOID_ROWS: list[str] = [
    "================" if y == 20 else "::::::::::::::::"
    for y in range(32)
]

# kael_cluster unified grid: 80 cols × 32 rows
# Helion (x=0–31) | Void/asteroid field (x=32–47) | Vanta (x=48–79)
_KAEL_MAP: list[str] = [
    _HR_ROWS[y] + _VOID_ROWS[y] + _VX_ROWS[y]
    for y in range(32)
]

# ---------------------------------------------------------------------------
# Character Background definitions
# Applied once at chargen; each background adjusts starting skills / attrs.
# ---------------------------------------------------------------------------

BACKGROUND_DATA: dict[str, dict] = {
    "colonial_recruit": {
        "name": "Colonial Recruit",
        "short": "Trained with the Helion marshal corps.",
        "desc": (
            "You served with the Helion marshal corps before your discharge or departure. "
            "Eight weeks of basic. Standard-issue vibroblade, three field exercises in the "
            "Cinder Warrens, and a service record that now means very little. "
            "You know how to hit, how to hold a guard, and when to stop asking questions."
        ),
        "skill_bonuses": {"melee": 3, "parry": 2},
        "attr_bonuses": {"con": 1},
        "credits": 0,
        "starting_weapon": "parrying_dagger",
        "off_hand_weapon": None,
        "rep_bonus": {"helion_colony": 25},
        "perk_desc": "5% buy discount at all vendors.",
    },
    "warrens_scavenger": {
        "name": "Warrens Scavenger",
        "short": "Raised in the Cinder Warrens industrial underbelly.",
        "desc": (
            "You grew up below the surface — the heat conduits, derelict generator housings, "
            "and service corridors of the Cinder Warrens. The Warren Raiders never owned you; "
            "you were just harder to catch. You know how to survive in cramped, hostile spaces, "
            "how to sleep in a generator housing, and what a shock baton sounds like before it swings."
        ),
        "skill_bonuses": {"bludgeons": 3, "camping": 4},
        "attr_bonuses": {"per": 1},
        "credits": 0,
        "starting_weapon": "shock_baton",
        "off_hand_weapon": None,
        "rep_bonus": {"helion_colony": 5, "vanta_clans": 10},
        "perk_desc": "Rest takes 14s instead of 20s.",
    },
    "clan_initiate": {
        "name": "Clan Initiate",
        "short": "Trained in Vanta Clan blade discipline.",
        "desc": (
            "You spent formative time among the Vanta Clans — whether born there, "
            "traded there, or earned the right to train there. "
            "The Clans' blade discipline is not taught; it is tested. "
            "You carry their footwork, their edge geometry, and their patience. "
            "They will not call you Clan. But they will not call you untrained, either."
        ),
        "skill_bonuses": {"blades": 4, "dodge": 2},
        "attr_bonuses": {"dex": 1},
        "credits": 0,
        "starting_weapon": "parrying_dagger",
        "off_hand_weapon": "training_vibroblade",
        "rep_bonus": {"vanta_clans": 25},
        "perk_desc": "+25% damage vs Glass Stalkers.",
    },
    "frontier_contractor": {
        "name": "Frontier Contractor",
        "short": "Independent operator, worked across the system.",
        "desc": (
            "You have worked jobs across the system since before you could count the reasons why. "
            "Transit manifests say contractor. Your ledger says something harder to describe. "
            "You are good with a sidearm, better at reading a room, and best at not being "
            "in the room when the accounting comes due."
        ),
        "skill_bonuses": {"ranged": 3},
        "attr_bonuses": {"cha": 1, "luck": 1},
        "credits": 30,
        "starting_weapon": "colony_sidearm",
        "off_hand_weapon": None,
        "rep_bonus": {"helion_colony": 10, "vanta_clans": 10},
        "perk_desc": "+5% sell bonus (raises sell cap to 0.65, stacks with CHA).",
    },
    "compact_remnant": {
        "name": "Compact Remnant",
        "short": "Descended from the Reach Compact's surveying corps.",
        "desc": (
            "The Reach Compact administered this system thirty years ago before it collapsed. "
            "You or your family served it — the bureaucracy, the survey teams, or the early "
            "colonists who catalogued things that shouldn't exist in these ruins. "
            "Some of it stayed with you: a sensitivity to the resonance fields, "
            "a tendency to hear things at the edge of signal range, and a PSI aptitude "
            "the colonial medical corps never quite knew what to do with."
        ),
        "skill_bonuses": {"melee": 1},
        "attr_bonuses": {"mind": 2},
        "credits": 0,
        "starting_weapon": "training_vibroblade",
        "off_hand_weapon": None,
        "rep_bonus": {"helion_colony": 15},
        "perk_desc": "PSI Heal costs 15 PSI instead of 20.",
    },
}

# Canonical display order for the chargen menu.
BACKGROUND_ORDER: list[str] = [
    "colonial_recruit",
    "warrens_scavenger",
    "clan_initiate",
    "frontier_contractor",
    "compact_remnant",
]

WORLD_DATA = {
    "planets": {
        "helion_reach": {
            "name": "Helion Reach",
            "areas": {
                "spaceport": {
                    "name": "Helion Spaceport",
                    "rooms": {
                        "helion_gate": {
                            "name": "Gate Concourse",
                            "room_type": "spaceport",
                            "exits": {"east": "helion_market", "south": "helion_shuttle_dock"},
                            "desc": (
                                "The main transit hub of Helion Reach. Scuffed plasteel columns frame the arrivals gate, "
                                "colonial insignia faded from years of grit. Personnel move past on shift rotations; "
                                "armed escorts keep position near the checkpoint arch. "
                                "The faint hum of the spaceport ventilation underscores everything."
                            ),
                        },
                        "helion_market": {
                            "name": "Dockside Market",
                            "room_type": "spaceport",
                            "exits": {"west": "helion_gate"},
                            "desc": (
                                "Vendor stalls line the market corridor in mismatched clusters, selling reclaimed parts, "
                                "rations, and field gear. The smell of recycled air and machine oil hangs over the space. "
                                "Salvagers and dock workers browse without urgency — everyone moving like they've done it a hundred times."
                            ),
                        },
                        "helion_shuttle_dock": {
                            "name": "Shuttle Dock A3",
                            "room_type": "spaceport",
                            "exits": {"north": "helion_gate", "board": "shuttle_airlock"},
                            "desc": (
                                "Dock A3 is a narrow bay at the far end of the spaceport, the boarding gantry sealed "
                                "against the hull of the Shardline shuttle. Status lights cycle amber. "
                                "A pressure warning plate on the wall reads: SHARDLINE ROUTE ACTIVE — BOARD WITH CLEARANCE."
                            ),
                        },
                    },
                },
                "guild_district": {
                    "name": "Iron Covenant District",
                    "rooms": {
                        "iron_covenant_hall": {
                            "name": "Iron Covenant Hall",
                            "room_type": "spaceport",
                            "exits": {},
                            "desc": (
                                "A vaulted hall of dark riveted iron, stripped of ornamentation. "
                                "Training racks line one wall — blades, mauls, and impact frames. "
                                "The air smells of machine oil and exertion. "
                                "At the far end, Guildmaster Varro stands behind a battered steel desk, "
                                "arms crossed, watching the door."
                            ),
                        },
                    },
                },
                "cinder_warrens": {
                    "name": "Cinder Warrens",
                    "rooms": {
                        "helion_warrens_entry": {
                            "name": "Service Tunnel Threshold",
                            "room_type": "industrial",
                            "exits": {},
                            "desc": (
                                "A reinforced hatch marks the descent into Helion's underbelly. The walls are raw durasteel, "
                                "cabling bundled along the ceiling in organized disorder. "
                                "The air grows warmer past the threshold — heat from the lower machinery seeping up. "
                                "Someone has scratched TURN BACK into the door frame."
                            ),
                        },
                        "helion_warrens_core": {
                            "name": "Cinder Warrens Core",
                            "room_type": "industrial",
                            "exits": {"east": "helion_warrens_forge", "south": "helion_warrens_depths"},
                            "desc": (
                                "The central chamber of the Cinder Warrens opens into a wide, low-ceilinged space choked "
                                "with old generator housings and salvage piles. Heat radiates from exposed conduit runs. "
                                "Movement echoes wrong here — sounds arrive from unexpected directions. This is raider territory. "
                                "A cracked maintenance hatch in the south wall leads further down."
                            ),
                        },
                        "helion_warrens_forge": {
                            "name": "Scrapforge Junction",
                            "room_type": "industrial",
                            "exits": {"west": "helion_warrens_core"},
                            "desc": (
                                "Three service corridors collapse into one at this junction. The floor is littered with fused slag "
                                "and stripped components from a derelict fabrication platform. "
                                "Sparks from a shorting panel strobe the room every few seconds. "
                                "Something large has been dragging itself through the debris."
                            ),
                        },
                        "helion_warrens_depths": {
                            "name": "Subsurface Conduit Run",
                            "room_type": "industrial",
                            "exits": {"north": "helion_warrens_core", "west": "helion_warrens_engine"},
                            "desc": (
                                "Below the main warren level the passage narrows to a crawl-width conduit run, "
                                "walls slick with mineral seepage. Coolant lines have long since ruptured — "
                                "the floor is ankle-deep in tepid chemical runoff. The heat is oppressive. "
                                "Scrap Crawlers — salvage drones gone feral — pick through the debris on corroded actuators. "
                                "Dim emergency lighting pulses amber in irregular intervals."
                            ),
                        },
                        "helion_warrens_engine": {
                            "name": "Dead Engine Room",
                            "room_type": "industrial",
                            "exits": {"east": "helion_warrens_depths", "south": "helion_warrens_nest"},
                            "desc": (
                                "A cavernous decommissioned engine room, the drive core long since stripped. "
                                "Massive support struts frame empty mounting bays. The silence here is total — "
                                "the kind that exists because everything that made noise is dead or gone. "
                                "Rust-colored staining on the bulkheads suggests this room saw violence before it saw silence. "
                                "A reinforced hatch to the south has been forced open from the other side."
                            ),
                        },
                        "helion_warrens_nest": {
                            "name": "Raider Stronghold",
                            "room_type": "industrial",
                            "exits": {"north": "helion_warrens_engine"},
                            "desc": (
                                "This chamber has been fortified: barricades of stripped plating, "
                                "stolen colonial supply crates stacked as cover, "
                                "and crude bioluminescent lanterns hanging from the overhead grid. "
                                "This is the Warren Raiders' command post — their captain operates from here, "
                                "backed by hardened fighters. The air smells of machine oil, sweat, and scorched circuitry. "
                                "A stolen colonial banner hangs above a makeshift command table, defaced with raider symbols."
                            ),
                        },
                    },
                }
            },
        },
        "vanta_ix": {
            "name": "Vanta IX",
            "areas": {
                "orbital_dock": {
                    "name": "Vanta Orbital Dock",
                    "rooms": {
                        "vanta_customs": {
                            "name": "Customs Ring",
                            "room_type": "orbital",
                            "exits": {"east": "vanta_bazaar", "south": "vanta_shuttle_dock"},
                            "desc": (
                                "A ring-shaped processing bay orbiting Vanta IX, pressurized and dim. "
                                "The colonial décor ends here — everything past customs is Clan jurisdiction. "
                                "Partitioned inspection lanes sit mostly unmanned; the Vanta Clans don't need formal "
                                "checkpoints when everyone already knows who's watching."
                            ),
                        },
                        "vanta_bazaar": {
                            "name": "Nocturne Bazaar",
                            "room_type": "orbital",
                            "exits": {"west": "vanta_customs"},
                            "desc": (
                                "The Nocturne Bazaar runs around the inner circumference of the orbital hub, "
                                "a permanent market built from modules stacked without plan. Holographic price boards flicker. "
                                "The clientele is quiet and deliberate — no one haggles loudly in Clan territory. "
                                "The goods speak for themselves: rare, old, expensive."
                            ),
                        },
                        "vanta_shuttle_dock": {
                            "name": "Orbital Berth C1",
                            "room_type": "orbital",
                            "exits": {"north": "vanta_customs", "board": "shuttle_airlock"},
                            "desc": (
                                "Berth C1 is a deep-access dock cut directly into the orbital hull. "
                                "The docking collar locks the Shardline shuttle in place with a magnetic clang that "
                                "resonates through the deck plating. A narrow viewport beside the gantry shows "
                                "the Glass Dunes far below, half in shadow."
                            ),
                        },
                    },
                },
                "psi_sanctum": {
                    "name": "PSI Weavers Sanctum",
                    "rooms": {
                        "psi_weavers_sanctum": {
                            "name": "PSI Weavers Sanctum",
                            "room_type": "orbital",
                            "exits": {},
                            "desc": (
                                "A circular chamber separated from the bazaar by a sound-dampening field. "
                                "The walls are hung with resonance conduit coils, faintly humming. "
                                "The floor is etched with focusing mandalas in pale phosphorescent ink. "
                                "Weaver Solen sits cross-legged at the center, eyes half-closed, "
                                "two PSI lenses orbiting her head in slow ellipses."
                            ),
                        },
                    },
                },
                "glass_dunes": {
                    "name": "Glass Dunes Ruins",
                    "rooms": {
                        "vanta_ruins_entry": {
                            "name": "Glass Dunes Access Lift",
                            "room_type": "ruins",
                            "exits": {},
                            "desc": (
                                "A heavy-lift platform descends through the orbital station's ventral hull into the ruins below. "
                                "The controls are worn smooth from use. The descent takes forty seconds, during which the "
                                "temperature drops noticeably and all station noise fades. "
                                "The lift opens onto wind-shaped glass formations as far as sensor range can map."
                            ),
                        },
                        "vanta_ruins_core": {
                            "name": "Glass Dunes Ruins",
                            "room_type": "ruins",
                            "exits": {"south": "vanta_ruins_vault", "east": "vanta_ruins_spire"},
                            "desc": (
                                "Fractured glass columns rise from the dune floor in irregular clusters, each a remnant of "
                                "whatever structure stood here before the collapse. Light refracts strangely, casting moving "
                                "prismatic patterns across the ground. Sound travels far and distorts. "
                                "Glass Stalkers hunt these formations by resonance. "
                                "A path of crushed glass leads east toward a massive intact spire."
                            ),
                        },
                        "vanta_ruins_vault": {
                            "name": "Shattered Relic Vault",
                            "room_type": "ruins",
                            "exits": {"north": "vanta_ruins_core"},
                            "desc": (
                                "A chamber formed by the collapse of a larger structure — walls of fused glass and crushed alloy. "
                                "At the center, a half-buried reliquary housing sits cracked open, contents partially scattered. "
                                "Whatever the empire stored here, not all of it is gone. "
                                "The air hums with residual field energy."
                            ),
                        },
                        "vanta_ruins_spire": {
                            "name": "Crystal Spire Interior",
                            "room_type": "ruins",
                            "exits": {"west": "vanta_ruins_core", "down": "vanta_ruins_deep"},
                            "desc": (
                                "The interior of the spire is a hollow column of fused crystal, "
                                "walls thick enough that outside sound becomes a subsonic hum. "
                                "Resonance patterns trace themselves in slow loops along the glass — "
                                "not structural, not natural. The builders used this space for something. "
                                "Crystal Wraiths inhabit the spire's upper chamber, their translucent forms "
                                "nearly invisible against the refracting walls until they move. "
                                "A shaft in the floor descends into older construction below."
                            ),
                        },
                        "vanta_ruins_deep": {
                            "name": "Subsurface Ruin Complex",
                            "room_type": "ruins",
                            "exits": {"up": "vanta_ruins_spire"},
                            "desc": (
                                "The lowest accessible level of the ruins: a series of vaulted chambers "
                                "built from a composite material no colonial analysis has fully categorised. "
                                "The architecture here is intact — the builders did not finish this space and leave; "
                                "they sealed it and departed. Whatever the seals were designed to contain "
                                "is no longer contained. Elder Stalkers patrol the deep chambers with a patience "
                                "that suggests they have been here since the seals broke. "
                                "Faint luminescent script runs along every surface — untranslated, but consistent."
                            ),
                        },
                    },
                }
            },
        },
    },
    "shuttle": {
        "name": "Shardline Shuttle",
        "rooms": {
            "shuttle_airlock": {
                "name": "Shuttle Airlock",
                "room_type": "shuttle",
                "exits": {"aft": "shuttle_cargo", "dock": "dynamic"},
                "desc": (
                    "A narrow staging compartment rated for six passengers, pressure seals lining both hatch frames. "
                    "A route display on the wall shows current docking status and destination. "
                    "The outer hull groans faintly as the shuttle adjusts position against the dock collar."
                ),
            },
            "shuttle_cargo": {
                "name": "Cargo Hold",
                "room_type": "shuttle",
                "exits": {"fore": "shuttle_airlock", "starboard": "shuttle_lounge"},
                "desc": (
                    "The aft section of the shuttle is given over to cargo — containers secured by mag-locks, "
                    "some stamped with colonial seals, others unmarked. Walking the hold feels like moving through "
                    "someone else's ledger. A crew access panel on the port side leads toward the passenger area."
                ),
            },
            "shuttle_lounge": {
                "name": "Passenger Lounge",
                "room_type": "shuttle",
                "exits": {"port": "shuttle_cargo", "up": "shuttle_observation"},
                "desc": (
                    "Four seat columns face the interior of the shuttle, upholstered in colonial gray. "
                    "A defunct refreshment unit is bolted to the starboard wall. The lounge is quiet between runs — "
                    "just recycled air and the low vibration of the drive core below deck. "
                    "Someone has left a manual on emergency decompression in one of the seat pockets."
                ),
            },
            "shuttle_observation": {
                "name": "Observation Deck",
                "room_type": "shuttle",
                "exits": {"down": "shuttle_lounge"},
                "desc": (
                    "A narrow upper deck with a continuous viewport running port to starboard. "
                    "During transit, stars track across the glass in slow arcs. The view of the Shardline corridor "
                    "is one of the few things on this route that isn't worn out. "
                    "A bench runs the full length of the viewport."
                ),
            },
        },
    },
    "npcs": [
        {
            "key": "helion_quartermaster",
            "name": "Quartermaster Vex",
            "room": "helion_market",
            "role": "vendor",
            "faction": "helion_colony",
            "dialogue": "Shield cells are scarce. Blades stay reliable.",
            "desc": "A stocky figure in worn colonial gray, Vex catalogues crates without looking up. A mono-edge blade hangs low on one hip.",
            "shop": ["mono_edge_blade", "parrying_dagger", "shock_baton", "colony_sidearm", "recruit_shield_battery",
                     "colony_helmet", "colony_vest", "colony_greaves", "colony_boots", "colony_maul"],
        },
        {
            "key": "helion_marshal",
            "name": "Marshal Kaine",
            "room": "helion_gate",
            "role": "quest_giver",
            "faction": "helion_colony",
            "dialogue": "The colony's eighty years old and still bleeding resources to Warrens scavengers. Clear them out, and we can talk about the Vanta contract.",
            "desc": "Marshal Kaine stands straight-backed near the gate terminal, arms crossed. Colony insignia on her shoulder pauldron is scratched but polished.",
        },
        {
            "key": "helion_scout",
            "name": "Scout Kess",
            "room": "helion_warrens_entry",
            "role": "information",
            "faction": "helion_colony",
            "dialogue": "Charge packs don't hold in the heat down here. Anything that needs a power source will fail you. Learn the blade.",
            "desc": "A lean figure in matte-black recon gear crouches near a junction panel. Eyes quick, posture ready.",
        },
        {
            "key": "vanta_blademaster",
            "name": "Blademaster Thorne",
            "room": "vanta_bazaar",
            "role": "trainer",
            "faction": "vanta_clans",
            "dialogue": "A clean parry is worth more than a hundred unstable shots.",
            "desc": "Thorne moves through a slow kata between market stalls, dual vantage blades trailing pale light. Clan tattoos mark both forearms.",
        },
        {
            "key": "vanta_broker",
            "name": "Broker Sorn",
            "room": "vanta_customs",
            "role": "vendor",
            "faction": "vanta_clans",
            "dialogue": "Artifacts, permits, and silence. Credits first.",
            "desc": "Sorn sits behind a scratched transparisteel partition, fingers steepled. A datapad rotates slowly between two fingers. No expression.",
            "shop": ["vanta_relic_shard", "heavy_arc_blade", "arc_lance", "vanta_pulse_rifle", "veteran_shield_upgrade",
                     "vanta_reave_helm", "vanta_reave_cuirass", "vanta_reave_legguards", "vanta_reave_boots",
                     "fracture_blade", "siege_plate"],
        },
        {
            "key": "vanta_elder",
            "name": "Elder Lyros",
            "room": "vanta_ruins_entry",
            "role": "information",
            "faction": "vanta_clans",
            "dialogue": "Whatever built these ruins was gone long before the first colony ship reached Helion. The Clans have studied them for generations. We still cannot say what they were.",
            "desc": "A gaunt elder in layered sand-colored robes. Deep-set eyes scan the ruins below with the patience of someone who has seen many expeditions not return.",
        },
        {
            "key": "helion_assessor",
            "name": "Tech-Assessor Mira",
            "room": "helion_market",
            "role": "appraiser",
            "faction": "helion_colony",
            "dialogue": "Materials science is all pattern recognition. Hand it over.",
            "desc": "A compact woman in a white technician's coat, magnification lens flipped up on her headband. She turns items slowly in her fingers before saying anything.",
        },
        {
            "key": "vanta_assessor",
            "name": "Relic-Assessor Dynn",
            "room": "vanta_customs",
            "role": "appraiser",
            "faction": "vanta_clans",
            "dialogue": "Colony steel is predictable. Vanta composite less so — that's the point.",
            "desc": "A wiry man in clan-pattern field gear, a portable spectral analyser clipped to his belt. He rarely makes eye contact but misses nothing.",
        },
        {
            "key": "iron_guildmaster",
            "name": "Guildmaster Varro",
            "room": "iron_covenant_hall",
            "role": "guildmaster",
            "guild": "iron_covenant",
            "faction": "helion_colony",
            "dialogue": "The Covenant doesn't take recruits. It takes soldiers. Prove you're worth the rank.",
            "desc": "A barrel-chested man in heavy iron-plate pauldrons, hands clasped behind his back. A scar crosses his jaw at an angle. He looks at everyone like they're a problem to be solved.",
        },
        {
            "key": "psi_guildmaster",
            "name": "Weaver Solen",
            "room": "psi_weavers_sanctum",
            "role": "guildmaster",
            "guild": "psi_weavers",
            "faction": "vanta_clans",
            "dialogue": "The weave is not a weapon. It is a language. Learn to speak it before you try to shout.",
            "desc": "A slender woman in layered void-silk, two small PSI lenses orbiting her head like slow moons. Her eyes are closed more often than open. When they open, they are unnervingly focused.",
        },
    ],
    "mobs": [
        {
            "key": "warren_raider",
            "room": "helion_warrens_core",
            "tier": "common",
            "level": 2,
            "respawn_time": 120,
            "stats": {"hp": 40, "shield_integrity": 30},
            "skills": {"melee": 15, "dodge": 8, "parry": 5},
            "xp": 25,
            "credit_drop": {"min": 3, "max": 8},
            "loot_table": [
                {"item": "colony_helmet", "chance": 0.15},
                {"item": "colony_greaves", "chance": 0.12},
                {"item": "parrying_dagger", "chance": 0.20},
            ],
            "desc": "A scavenger in mismatched armor plates. Hardened enough by Warren survival that their field reads above baseline. Moves fast and hits hard in close quarters.",
        },
        {
            "key": "slag_hound",
            "room": "helion_warrens_forge",
            "tier": "common",
            "level": 2,
            "respawn_time": 120,
            "stats": {"hp": 35, "shield_integrity": 20},
            "skills": {"melee": 20, "dodge": 12, "parry": 3},
            "xp": 20,
            "credit_drop": {"min": 2, "max": 6},
            "loot_table": [
                {"item": "shock_baton", "chance": 0.15},
                {"item": "colony_boots", "chance": 0.12},
            ],
            "desc": "A quadrupedal scrap-chassis predator, repurposed from mining automation. Overheated joints glow at the seams.",
        },
        {
            "key": "scrap_crawler",
            "room": "helion_warrens_depths",
            "tier": "common",
            "level": 4,
            "respawn_time": 150,
            "stats": {"hp": 65, "shield_integrity": 40},
            "skills": {"melee": 28, "dodge": 14, "parry": 8},
            "xp": 55,
            "credit_drop": {"min": 5, "max": 12},
            "loot_table": [
                {"item": "colony_vest", "chance": 0.15},
                {"item": "colony_greaves", "chance": 0.12},
                {"item": "shock_baton", "chance": 0.10},
            ],
            "weak_to": "bludgeons",
            "desc": "A salvage drone corrupted beyond its original programming — now a chassis-crawler that treats organic matter as debris to be processed. Reinforced actuator arms deliver punishing blows.",
        },
        {
            "key": "raider_captain",
            "room": "helion_warrens_nest",
            "tier": "elite",
            "level": 5,
            "respawn_time": 300,
            "stats": {"hp": 90, "shield_integrity": 60},
            "skills": {"melee": 38, "dodge": 20, "parry": 22},
            "xp": 110,
            "credit_drop": {"min": 15, "max": 30},
            "loot_table": [
                {"item": "reinforced_baton", "chance": 0.30},
                {"item": "colony_vest", "chance": 0.25},
                {"item": "colony_maul", "chance": 0.15},
            ],
            "on_hit_effect": {"name": "weakened", "ticks": 1},
            "desc": "The Warren Raiders' field commander — scarred, deliberate, wearing salvaged colonial plate. Reads every engagement before committing. The kind of fighter who got to be captain by making fewer mistakes than everyone else.",
        },
        {
            "key": "dock_saboteur",
            "room": "vanta_ruins_core",
            "tier": "common",
            "level": 3,
            "respawn_time": 120,
            "stats": {"hp": 50, "shield_integrity": 45},
            "skills": {"melee": 25, "dodge": 15, "parry": 10},
            "xp": 40,
            "credit_drop": {"min": 6, "max": 14},
            "loot_table": [
                {"item": "mono_edge_blade", "chance": 0.15},
                {"item": "colony_vest", "chance": 0.10},
                {"item": "colony_greaves", "chance": 0.10},
            ],
            "desc": "A compact operative in void-black gear. Their field reads developed — trained combat, not scavenger improvisation. Moves with deliberate economy — every step calculated.",
        },
        {
            "key": "glass_stalker",
            "room": "vanta_ruins_core",
            "tier": "elite",
            "level": 5,
            "respawn_time": 300,
            "stats": {"hp": 80, "shield_integrity": 70},
            "skills": {"melee": 35, "dodge": 22, "parry": 18},
            "xp": 100,
            "credit_drop": {"min": 18, "max": 35},
            "loot_table": [
                {"item": "vanta_relic_shard", "chance": 0.25},
                {"item": "vanta_reave_legguards", "chance": 0.20},
                {"item": "recruit_shield_battery", "chance": 0.20},
            ],
            "weak_to": "blades",
            "on_hit_effect": {"name": "bleed", "ticks": 2},
            "can_ambush": True,
            "desc": "A predatory xenomorph of uncertain origin, body partially translucent like stressed glass. Its biofield pulses in irregular bursts — the most powerful natural field recorded in any Shardfield organism.",
        },
        {
            "key": "ruin_sentinel",
            "room": "vanta_ruins_spire",
            "tier": "common",
            "level": 6,
            "respawn_time": 180,
            "stats": {"hp": 95, "shield_integrity": 80},
            "skills": {"melee": 40, "dodge": 18, "parry": 20},
            "xp": 130,
            "credit_drop": {"min": 14, "max": 28},
            "loot_table": [
                {"item": "vanta_reave_helm", "chance": 0.20},
                {"item": "vanta_reave_legguards", "chance": 0.18},
                {"item": "resonance_coil", "chance": 0.15},
            ],
            "desc": "An automated guardian of intermediate classification — less ancient than the Vault Guardian, but more refined than colonial-era security. Moves in careful geometric patterns, responding to motion with immediate targeting.",
        },
        {
            "key": "crystal_wraith",
            "room": "vanta_ruins_spire",
            "tier": "elite",
            "level": 8,
            "respawn_time": 360,
            "stats": {"hp": 130, "shield_integrity": 110},
            "skills": {"melee": 52, "dodge": 32, "parry": 25},
            "xp": 200,
            "credit_drop": {"min": 22, "max": 42},
            "loot_table": [
                {"item": "spire_fragment", "chance": 0.30},
                {"item": "vanta_reave_cuirass", "chance": 0.20},
                {"item": "veteran_shield_upgrade", "chance": 0.18},
            ],
            "weak_to": "polearms",
            "on_hit_effect": {"name": "weakened", "ticks": 2},
            "can_ambush": True,
            "desc": "A Glass Stalker variant that has undergone deep resonance imprinting — its body is now predominantly crystalline, nearly invisible against the spire walls. Moves by vibration detection alone. Strikes from angles that shouldn't be possible.",
        },
        {
            "key": "vault_guardian",
            "room": "vanta_ruins_vault",
            "tier": "elite",
            "level": 7,
            "respawn_time": 600,
            "stats": {"hp": 120, "shield_integrity": 100},
            "skills": {"melee": 45, "dodge": 18, "parry": 30},
            "xp": 175,
            "credit_drop": {"min": 20, "max": 40},
            "loot_table": [
                {"item": "heavy_arc_blade", "chance": 0.20},
                {"item": "vanta_reave_cuirass", "chance": 0.25},
                {"item": "veteran_shield_upgrade", "chance": 0.20},
            ],
            "weak_to": "bludgeons",
            "on_hit_effect": {"name": "weakened", "ticks": 2},
            "desc": "A massive automated sentinel anchored to the vault door — angular chassis of black composite, shield emitter cycling at full output. Colony-era security firmware: patient, systematic, merciless.",
        },
        {
            "key": "elder_stalker",
            "room": "vanta_ruins_deep",
            "tier": "elite",
            "level": 9,
            "respawn_time": 480,
            "stats": {"hp": 160, "shield_integrity": 130},
            "skills": {"melee": 60, "dodge": 38, "parry": 30},
            "xp": 260,
            "credit_drop": {"min": 30, "max": 55},
            "loot_table": [
                {"item": "deep_ruin_cache", "chance": 0.35},
                {"item": "spire_fragment", "chance": 0.25},
                {"item": "vanta_reave_boots", "chance": 0.20},
            ],
            "weak_to": "blades",
            "on_hit_effect": {"name": "bleed", "ticks": 3},
            "can_ambush": True,
            "desc": "The apex predator of the deep ruins. An ancient Glass Stalker specimen, body fully crystallised over decades of resonance saturation. Its biofield is indistinguishable from background ruin energy until it strikes. The Clans have a name for these. They do not say it lightly.",
        },
        {
            "key": "ancient_construct",
            "room": "vanta_ruins_deep",
            "tier": "elite",
            "level": 10,
            "respawn_time": 720,
            "stats": {"hp": 200, "shield_integrity": 170},
            "skills": {"melee": 68, "dodge": 28, "parry": 40},
            "xp": 350,
            "credit_drop": {"min": 40, "max": 70},
            "loot_table": [
                {"item": "construct_core", "chance": 0.40},
                {"item": "deep_ruin_cache", "chance": 0.30},
                {"item": "siege_plate", "chance": 0.15},
            ],
            "weak_to": "polearms",
            "on_hit_effect": {"name": "stun", "ticks": 1},
            "desc": "A full-class automated construct of the ruins' original builders — intact, operational, and hostile to all biological motion. Its chassis is the same uncatalogued composite as the deep ruin walls. The shield emitter runs on a power source that colonial engineering cannot identify. This is what the seals were containing.",
        },
    ],
    "items": {
        "training_vibroblade": {
            "name": "Training Vibroblade",
            "slots": ["main_hand"],
            "weapon_type": "blades",
            "damage_bonus": 0,
            "price": 0,
            "desc": "Standard-issue practice blade. Serviceable in a pinch, but outclassed by anything purpose-built.",
        },
        "mono_edge_blade": {
            "name": "Mono-Edge Blade",
            "slots": ["main_hand"],
            "weapon_type": "blades",
            "damage_bonus": 5,
            "price": 75,
            "desc": "Single-molecule cutting edge. Disrupts shield harmonics cleanly on controlled contact.",
        },
        "vanta_relic_shard": {
            "name": "Vanta Relic Shard",
            "slots": ["main_hand"],
            "weapon_type": "blades",
            "damage_bonus": 8,
            "price": 150,
            "desc": "A fractured glass relic pulsing with unstable resonance energy. Destabilizes shields efficiently.",
        },
        "parrying_dagger": {
            "name": "Parrying Dagger",
            "slots": ["off_hand", "main_hand"],
            "weapon_type": "blades",
            "damage_bonus": 2,
            "price": 50,
            "desc": "Short and fast. Useful as an off-hand weapon or a light main blade in a pinch.",
        },
        "heavy_arc_blade": {
            "name": "Heavy Arc Blade",
            "slots": ["main_hand"],
            "weapon_type": "blades",
            "damage_bonus": 14,
            "two_handed": True,
            "price": 200,
            "desc": "A massive arc-edged blade that demands both hands. Devastating but leaves no room for an off-hand.",
        },
        "shock_baton": {
            "name": "Shock Baton",
            "slots": ["main_hand", "off_hand"],
            "weapon_type": "bludgeons",
            "damage_bonus": 4,
            "price": 65,
            "desc": "A dense alloy rod with an electrostatic tip. Slow but punishing to shield integrity.",
        },
        "arc_lance": {
            "name": "Arc Lance",
            "slots": ["main_hand"],
            "weapon_type": "polearms",
            "damage_bonus": 9,
            "two_handed": True,
            "price": 140,
            "desc": "A two-handed polearm crackling with arc energy. Dominates opening exchanges before an enemy can close distance.",
        },
        "colony_sidearm": {
            "name": "Colony Sidearm",
            "slots": ["main_hand"],
            "weapon_type": "ranged",
            "damage_bonus": 7,
            "price": 110,
            "desc": "Compact colonial pistol. Useful for suppression and safer engagement at range against exposed targets.",
        },
        "vanta_pulse_rifle": {
            "name": "Vanta Pulse Rifle",
            "slots": ["main_hand"],
            "weapon_type": "ranged",
            "damage_bonus": 12,
            "two_handed": True,
            "price": 220,
            "desc": "Clan-refitted pulse rifle with stabilized coils. Expensive to feed, excellent for controlled ranged pressure.",
        },
        "recruit_shield_battery": {
            "name": "Recruit Field Brace",
            "slots": ["utility", "off_hand"],
            "shield_bonus": 20,
            "price": 40,
            "desc": "A colonial field amplifier. Couples with the body's natural biofield to extend effective combat capacity. Issued to new recruits. Can be braced in the off-hand.",
        },
        "veteran_shield_upgrade": {
            "name": "Veteran Field Brace",
            "slots": ["utility", "off_hand"],
            "shield_bonus": 40,
            "price": 100,
            "desc": "Military-grade biofield amplifier. Resonant coupling significantly extends a conditioned field's capacity. Can be braced in the off-hand.",
        },
        # --- Armor (head / torso / legs / feet) ---
        # Colony-grade (entry level, sold at Helion Quartermaster)
        # phys_reduction: flat damage reduction vs melee hits (applied in apply_hit)
        "colony_helmet": {
            "name": "Colony Helmet",
            "slots": ["head"],
            "armor_bonus": 10,
            "phys_reduction": 1,
            "price": 50,
            "desc": "Scuffed colonial-issue ballistic helmet. Dented, but rated for close-quarters fragmentation.",
        },
        "colony_vest": {
            "name": "Colony Vest",
            "slots": ["torso"],
            "armor_bonus": 25,
            "phys_reduction": 3,
            "price": 90,
            "desc": "Standard colonial ballistic vest. Heavy composite plates over a shock-absorbing underlayer.",
        },
        "colony_greaves": {
            "name": "Colony Greaves",
            "slots": ["legs"],
            "armor_bonus": 10,
            "phys_reduction": 1,
            "price": 50,
            "desc": "Reinforced leg guards, colonial infantry issue. Protection without sacrificing too much mobility.",
        },
        "colony_boots": {
            "name": "Colony Boots",
            "slots": ["feet"],
            "armor_bonus": 5,
            "phys_reduction": 1,
            "price": 25,
            "desc": "Heavy-soled boots with reinforced toe caps. Reliable footing on debris-strewn decks.",
        },
        # --- Grind-tier (priced above total quest credit rewards; requires mob farming) ---
        "colony_maul": {
            "name": "Colony Maul",
            "slots": ["main_hand"],
            "weapon_type": "bludgeons",
            "damage_bonus": 9,
            "price": 1100,
            "desc": "A reinforced industrial maul repurposed from mining equipment. Heavy and slow, but ideal for cracking shields and triggering the Concussion technique.",
        },
        "fracture_blade": {
            "name": "Fracture Blade",
            "slots": ["main_hand"],
            "weapon_type": "blades",
            "damage_bonus": 12,
            "price": 1200,
            "desc": "A single-hand blade with a stress-fracture edge — vibrates at high frequency on contact, shredding shield harmonics. Best 1H option available.",
        },
        "siege_plate": {
            "name": "Siege Plate",
            "slots": ["torso"],
            "armor_bonus": 60,
            "phys_reduction": 7,
            "price": 1250,
            "desc": "Reclaimed heavy-siege composite, originally fitted to automated assault units. Brutal protection with almost no flexibility — built for standing your ground.",
        },
        # Vanta-grade (advanced, sold at Vanta Broker)
        "vanta_reave_helm": {
            "name": "Vanta Reave Helm",
            "slots": ["head"],
            "armor_bonus": 20,
            "phys_reduction": 2,
            "price": 130,
            "desc": "Clan-worked composite helm, layered against energy and impact. Clan sigil etched at the brow.",
        },
        "vanta_reave_cuirass": {
            "name": "Vanta Reave Cuirass",
            "slots": ["torso"],
            "armor_bonus": 45,
            "phys_reduction": 5,
            "price": 200,
            "desc": "Full vanta cuirass of high-density composite over reactive underlayer. Heavy, reassuring, and intimidating in equal measure.",
        },
        "vanta_reave_legguards": {
            "name": "Vanta Reave Legguards",
            "slots": ["legs"],
            "armor_bonus": 20,
            "phys_reduction": 2,
            "price": 130,
            "desc": "Clan-pattern leg plates with integrated knee guards. Built for extended deep-ruin operations.",
        },
        "vanta_reave_boots": {
            "name": "Vanta Reave Boots",
            "slots": ["feet"],
            "armor_bonus": 10,
            "phys_reduction": 1,
            "price": 70,
            "desc": "Composite-soled vanta boots with mag-grip sole and ankle reinforcement. Standard clan field kit.",
        },
        # --- Mid-tier quest/drop rewards ---
        "reinforced_baton": {
            "name": "Reinforced Baton",
            "slots": ["main_hand"],
            "weapon_type": "bludgeons",
            "damage_bonus": 6,
            "price": 120,
            "desc": "A standard shock baton with additional alloy jacketing and a heavier head. The Warrens Captain's personal weapon — well-maintained, unlike most things down there.",
        },
        "resonance_coil": {
            "name": "Resonance Coil",
            "slots": ["utility"],
            "shield_bonus": 30,
            "price": 180,
            "desc": "A salvaged resonance coil recovered from the spire's inner workings. Pairs with a biofield amplifier to dramatically extend effective shield capacity.",
        },
        # --- High-tier drop items (deep ruin content) ---
        "spire_fragment": {
            "name": "Spire Fragment",
            "slots": ["main_hand"],
            "weapon_type": "blades",
            "damage_bonus": 16,
            "price": 350,
            "desc": "A shard of the crystal spire, edge-sharpened by resonance fracture. Cuts shield harmonics at a molecular level. The material is not catalogued. It should not be this sharp.",
        },
        "deep_ruin_cache": {
            "name": "Deep Ruin Cache",
            "slots": ["utility"],
            "shield_bonus": 55,
            "price": 400,
            "desc": "A sealed field-containment unit recovered from the deep ruins. Its original purpose is unclear, but coupled to a biofield it provides extraordinary shield extension.",
        },
        "construct_core": {
            "name": "Construct Core",
            "slots": ["utility"],
            "shield_bonus": 70,
            "armor_bonus": 20,
            "price": 600,
            "desc": "The power core of an ancient construct, still active. Interfacing it with human biofield technology is unstable and theoretically inadvisable. It works anyway. Substantial shield and HP bonuses — at a cost the Clans' medics prefer not to document.",
        },
        # --- Polearm (added to vendor inventory) ---
        "combat_lance": {
            "name": "Combat Lance",
            "slots": ["main_hand"],
            "weapon_type": "polearms",
            "damage_bonus": 11,
            "two_handed": True,
            "price": 260,
            "desc": "A heavier, purpose-built combat variant of the arc lance. Loses the arc emitter for a reinforced alloy tip — more reliable in sustained exchanges.",
        },
    },
    "quests": [
        {
            "key": "helion_intro_colony_defense",
            "name": "Helion Introduction: Colony Defense",
            "giver": "helion_marshal",
            "start_room": "helion_gate",
            "objectives": [
                "Talk to Marshal Kaine",
                "Defeat 2 Warren Raiders in Cinder Warrens",
                "Return to Marshal Kaine",
            ],
            "rewards": {"xp": 150, "credits": 50, "item": "recruit_shield_battery", "reputation": 20},
        },
        {
            "key": "vanta_expedition_artifact_recovery",
            "name": "Vanta Expedition: Artifact Recovery",
            "giver": "helion_marshal",
            "start_room": "helion_shuttle_dock",
            "requires": ["helion_intro_colony_defense"],
            "objectives": [
                "Board shuttle at Helion",
                "Arrive at Vanta IX",
                "Defeat 3 Glass Stalkers",
                "Recover relic from Shattered Relic Vault",
                "Return to Helion and report",
            ],
            "rewards": {"xp": 400, "credits": 200, "item": "veteran_shield_upgrade", "reputation": 30},
        },
        # --- Secondary quests (NPC-giver, one-step, no prereqs) ---------------
        {
            "key": "kess_clear_scrapforge",
            "name": "Kess: Clear the Scrapforge",
            "giver": "helion_scout",
            "start_room": "helion_warrens_entry",
            "objectives": [
                "Talk to Scout Kess in the Service Tunnel Threshold",
                "Defeat 2 Slag Hounds in Scrapforge Junction",
                "Return to Scout Kess",
            ],
            "rewards": {"xp": 100, "credits": 40, "reputation": 12},
        },
        {
            "key": "thorne_blade_trial",
            "name": "Thorne: Blade Trial",
            "giver": "vanta_blademaster",
            "start_room": "vanta_bazaar",
            "objectives": [
                "Talk to Blademaster Thorne in the Nocturne Bazaar",
                "Defeat 2 Glass Stalkers in the Glass Dunes",
                "Return to Blademaster Thorne",
            ],
            "rewards": {"xp": 200, "credits": 60, "skill_points": 2, "reputation": 15},
        },
        {
            "key": "lyros_vault_recon",
            "name": "Lyros: Vault Reconnaissance",
            "giver": "vanta_elder",
            "start_room": "vanta_ruins_entry",
            "objectives": [
                "Talk to Elder Lyros at the Glass Dunes Access Lift",
                "Reach the Shattered Relic Vault",
                "Return to Elder Lyros",
            ],
            "rewards": {"xp": 150, "credits": 50, "reputation": 12},
        },
        # --- Extended quests (mid-tier, require area progression) ---
        {
            "key": "varro_depths_cleansing",
            "name": "Varro: Depths Cleansing",
            "giver": "iron_guildmaster",
            "start_room": "iron_covenant_hall",
            "objectives": [
                "Talk to Guildmaster Varro at the Iron Covenant Hall",
                "Defeat 3 Scrap Crawlers in the Subsurface Conduit Run",
                "Return to Guildmaster Varro",
            ],
            "rewards": {"xp": 220, "credits": 80, "item": "reinforced_baton", "reputation": 18},
        },
        {
            "key": "varro_captain_bounty",
            "name": "Varro: Captain's Bounty",
            "giver": "iron_guildmaster",
            "start_room": "iron_covenant_hall",
            "requires": ["varro_depths_cleansing"],
            "objectives": [
                "Talk to Guildmaster Varro at the Iron Covenant Hall",
                "Defeat the Raider Captain in the Raider Stronghold",
                "Return to Guildmaster Varro",
            ],
            "rewards": {"xp": 350, "credits": 130, "item": "colony_maul", "reputation": 25},
        },
        {
            "key": "solen_spire_purge",
            "name": "Solen: Spire Purge",
            "giver": "psi_guildmaster",
            "start_room": "psi_weavers_sanctum",
            "objectives": [
                "Talk to Weaver Solen at the PSI Weavers Sanctum",
                "Defeat 3 Crystal Wraiths in the Crystal Spire Interior",
                "Return to Weaver Solen",
            ],
            "rewards": {"xp": 400, "credits": 150, "item": "resonance_coil", "reputation": 28},
        },
        {
            "key": "sorn_deep_salvage",
            "name": "Sorn: Deep Salvage",
            "giver": "vanta_broker",
            "start_room": "vanta_customs",
            "requires": ["vanta_expedition_artifact_recovery"],
            "objectives": [
                "Talk to Broker Sorn at the Customs Ring",
                "Reach the Subsurface Ruin Complex",
                "Return to Broker Sorn",
            ],
            "rewards": {"xp": 300, "credits": 120, "item": "combat_lance", "reputation": 20},
        },
        {
            "key": "lyros_ancient_record",
            "name": "Lyros: Ancient Record",
            "giver": "vanta_elder",
            "start_room": "vanta_ruins_entry",
            "requires": ["lyros_vault_recon"],
            "objectives": [
                "Talk to Elder Lyros at the Glass Dunes Access Lift",
                "Defeat the Ancient Construct in the Subsurface Ruin Complex",
                "Return to Elder Lyros",
            ],
            "rewards": {"xp": 500, "credits": 200, "item": "deep_ruin_cache", "reputation": 35},
        },
    ],
    # -----------------------------------------------------------------------
    # Guild system
    # -----------------------------------------------------------------------
    "guilds": {
        "iron_covenant": {
            "name": "Iron Covenant",
            "planet": "helion_reach",
            "hall_room": "iron_covenant_hall",
            "guildmaster_npc": "iron_guildmaster",
            "max_rank": 20,
            # Stat bonuses awarded each time the player advances one guild rank.
            "passive_per_rank": {"str": 1, "con": 1, "hp_max": 5},
            "skills": {
                # --- Ranks 1-10 (original skills, rank gates extended) ---
                "iron_stance": {
                    "name": "Iron Stance",
                    "desc": "Reinforce your guard — gain +1 phys_reduction per 20% trained (max +5).",
                    "type": "passive",
                    "effect": "phys_reduction",
                    "rank_gates": {1: 25, 3: 50, 6: 75, 9: 100},
                    "xp_cost_per_pct": 50,
                    "bonus_per_20pct": 1,
                },
                "throw_weight": {
                    "name": "Throw Weight",
                    "desc": "Leverage your mass — gain +1 weapon damage per 20% trained (max +5).",
                    "type": "passive",
                    "effect": "weapon_damage",
                    "rank_gates": {1: 25, 3: 50, 6: 75, 9: 100},
                    "xp_cost_per_pct": 50,
                    "bonus_per_20pct": 1,
                },
                "find_weakness": {
                    "name": "Find Weakness",
                    "desc": "Read your opponent — gain +1% crit chance per 10% trained (max +10%).",
                    "type": "passive",
                    "effect": "crit_chance",
                    "rank_gates": {1: 25, 4: 50, 7: 75, 10: 100},
                    "xp_cost_per_pct": 60,
                    "bonus_per_10pct": 0.01,
                },
                "enhanced_criticals": {
                    "name": "Enhanced Criticals",
                    "desc": "Strike through defenses — gain +1 raw crit damage per 25% trained (max +4).",
                    "type": "passive",
                    "effect": "crit_damage",
                    "rank_gates": {3: 25, 6: 50, 9: 100},
                    "xp_cost_per_pct": 75,
                    "bonus_per_25pct": 1,
                },
                "sunder_strike": {
                    "name": "Sunder Strike",
                    "desc": (
                        "Active: massive 2-round wind-up strike — deals 1.5× weapon damage + 10 flat "
                        "bonus, ignoring target parry. Costs 40 Stamina. Requires rank 5."
                    ),
                    "type": "active",
                    "rank_gates": {5: 100},
                    "xp_cost_per_pct": 100,
                },
                # --- Ranks 11-20 (advanced skills) ---
                "iron_will": {
                    "name": "Iron Will",
                    "desc": (
                        "Forge your resolve — gain +1 Stamina max per 10% trained (max +10 Stamina max). "
                        "Requires rank 11."
                    ),
                    "type": "passive",
                    "effect": "stamina_max",
                    "rank_gates": {11: 25, 13: 50, 16: 75, 19: 100},
                    "xp_cost_per_pct": 80,
                    "bonus_per_10pct": 1,
                },
                "bulwark": {
                    "name": "Bulwark",
                    "desc": (
                        "Stand your ground — gain +1 phys_reduction and +5 hp_max per 25% trained (max +4 reduction, +20 hp). "
                        "Requires rank 12."
                    ),
                    "type": "passive",
                    "effect": "phys_reduction",
                    "rank_gates": {12: 25, 14: 50, 17: 75, 20: 100},
                    "xp_cost_per_pct": 90,
                    "bonus_per_25pct": 1,
                },
                "warlord_strike": {
                    "name": "Warlord Strike",
                    "desc": (
                        "Active: a single crushing blow — deals 2.0× weapon damage + 20 flat, "
                        "ignores parry and shield armor reduction. Costs 55 Stamina. Requires rank 15."
                    ),
                    "type": "active",
                    "rank_gates": {15: 100},
                    "xp_cost_per_pct": 150,
                },
                "battle_mastery": {
                    "name": "Battle Mastery",
                    "desc": (
                        "The pinnacle of Covenant training — gain +2% crit chance and +2 crit damage "
                        "per 25% trained (max +8% crit, +8 damage). Requires rank 18."
                    ),
                    "type": "passive",
                    "effect": "crit_chance",
                    "rank_gates": {18: 25, 19: 50, 20: 100},
                    "xp_cost_per_pct": 120,
                    "bonus_per_25pct": 0.02,
                    "crit_damage_per_25pct": 2,
                },
            },
        },
        "psi_weavers": {
            "name": "PSI Weavers",
            "planet": "vanta_ix",
            "hall_room": "psi_weavers_sanctum",
            "guildmaster_npc": "psi_guildmaster",
            "max_rank": 20,
            # Stat bonuses awarded each time the player advances one guild rank.
            "passive_per_rank": {"mind": 1, "psi_max": 10},
            "skills": {
                # --- Ranks 1-10 (original skills) ---
                "focused_channel": {
                    "name": "Focused Channel",
                    "desc": "Deepen your inward focus — PSI Heal restores +2 HP per 25% trained (max +8).",
                    "type": "passive",
                    "effect": "psi_heal_bonus",
                    "rank_gates": {1: 25, 3: 50, 6: 75, 9: 100},
                    "xp_cost_per_pct": 50,
                    "bonus_per_25pct": 2,
                },
                "resonance_shield": {
                    "name": "Resonance Shield",
                    "desc": (
                        "Active (psi ward): erect a 1-round PSI barrier absorbing "
                        "20 + (rank × 2) incoming melee damage. Costs 30 PSI."
                    ),
                    "type": "active",
                    "rank_gates": {1: 100},
                    "xp_cost_per_pct": 50,
                },
                "psi_bolt": {
                    "name": "PSI Bolt",
                    "desc": (
                        "Active (psi bolt): concentrated PSI blast dealing "
                        "15 + 4 per MIND above 10. Costs 35 PSI. Requires rank 3."
                    ),
                    "type": "active",
                    "rank_gates": {3: 100},
                    "xp_cost_per_pct": 75,
                },
                "mind_shatter": {
                    "name": "Mind Shatter",
                    "desc": (
                        "Active (psi shatter): overwhelm neural defenses — deals "
                        "20 + 6 per MIND above 10 PSI damage and stuns 1 round. "
                        "Costs 50 PSI. Requires rank 6."
                    ),
                    "type": "active",
                    "rank_gates": {6: 100},
                    "xp_cost_per_pct": 100,
                },
                # --- Ranks 11-20 (advanced skills) ---
                "deep_resonance": {
                    "name": "Deep Resonance",
                    "desc": (
                        "Attune to the field layer — gain +5 PSI max and +1 PSI regen bonus per 25% trained "
                        "(max +20 PSI max, +4 regen). Requires rank 11."
                    ),
                    "type": "passive",
                    "effect": "psi_max",
                    "rank_gates": {11: 25, 13: 50, 16: 75, 19: 100},
                    "xp_cost_per_pct": 80,
                    "bonus_per_25pct": 5,
                },
                "void_lance": {
                    "name": "Void Lance",
                    "desc": (
                        "Active (psi lance): channel raw void energy — deals 30 + 8 per MIND above 10 "
                        "damage, bypasses shields entirely. Costs 70 PSI. Requires rank 13."
                    ),
                    "type": "active",
                    "rank_gates": {13: 100},
                    "xp_cost_per_pct": 120,
                },
                "psi_surge": {
                    "name": "PSI Surge",
                    "desc": (
                        "Amplify all PSI healing — PSI Heal, ward absorption, and sleep PSI restore "
                        "improved by +3 per 25% trained (max +12). Requires rank 15."
                    ),
                    "type": "passive",
                    "effect": "psi_heal_bonus",
                    "rank_gates": {15: 25, 17: 50, 19: 75, 20: 100},
                    "xp_cost_per_pct": 100,
                    "bonus_per_25pct": 3,
                },
                "mind_fortress": {
                    "name": "Mind Fortress",
                    "desc": (
                        "The pinnacle of Weaver training — passive permanent PSI ward absorbing "
                        "+3 damage per 25% trained (max +12 always-active absorption). Requires rank 18."
                    ),
                    "type": "passive",
                    "effect": "phys_reduction",
                    "rank_gates": {18: 25, 19: 50, 20: 100},
                    "xp_cost_per_pct": 120,
                    "bonus_per_25pct": 3,
                },
            },
        },
    },
    "overworld": {
        # -----------------------------------------------------------------------
        # The Shardfield (kael_cluster) — unified 80×32 grid
        # Helion Reach (x=0–31) | Asteroid Void (x=32–47) | Vanta IX (x=48–79)
        # Named locations — Helion side (x unchanged):
        #   Spaceport (15,5), Iron Covenant Hall (23,14), Helion Warrens (8,21)
        # Named locations — Vanta side (x shifted +48):
        #   Vanta Customs (63,5), PSI Weavers Sanctum (55,14), Glass Dunes (70,22)
        # Terrain glyphs (Helion): . h m f w r i = ~ c *
        # Terrain glyphs (Void):   : asteroid debris (impassable)  = tradelane (y=20)
        # Terrain glyphs (Vanta):  . f h m ~ a R = s c *
        # -----------------------------------------------------------------------
        "kael_cluster": {
            "planet_key": "kael_cluster",
            "planet_name": "The Shardfield",
            "entry_point": [15, 5],
            "map": _KAEL_MAP,
            "named_locations": [
                # Helion Reach side (x unchanged)
                {
                    "name": "Helion Spaceport",
                    "x": 15, "y": 5,
                    "room_key": "helion_gate",
                    "desc": (
                        "The silhouette of the Helion Spaceport rises from the dust — "
                        "a cluster of pressurized domes and antenna arrays. "
                        "The main gate is visible ahead."
                    ),
                },
                {
                    "name": "Iron Covenant Hall",
                    "x": 23, "y": 14,
                    "room_key": "iron_covenant_hall",
                    "desc": (
                        "A heavy iron structure dominates the ridge — the Iron Covenant guild hall. "
                        "Training sounds carry on the wind."
                    ),
                },
                {
                    "name": "Helion Warrens",
                    "x": 8, "y": 21,
                    "room_key": "helion_warrens_entry",
                    "desc": (
                        "A reinforced hatch set into cracked durasteel marks the entrance to "
                        "the Cinder Warrens below. Someone has scratched TURN BACK into the frame."
                    ),
                },
                # Vanta IX side (x shifted +48)
                {
                    "name": "Vanta Customs",
                    "x": 63, "y": 5,
                    "room_key": "vanta_customs",
                    "desc": (
                        "The ring-shaped silhouette of the Vanta Orbital Dock access lift. "
                        "A customs terminal marks the entrance to Clan territory."
                    ),
                },
                {
                    "name": "PSI Weavers Sanctum",
                    "x": 55, "y": 14,
                    "room_key": "psi_weavers_sanctum",
                    "desc": (
                        "A circular structure of resonance-conduit coils marks the PSI Weavers Sanctum. "
                        "The air hums and presses softly against your senses."
                    ),
                },
                {
                    "name": "Glass Dunes Ruins",
                    "x": 70, "y": 22,
                    "room_key": "vanta_ruins_entry",
                    "desc": (
                        "Shattered glass columns and half-buried walls mark the ancient ruin site. "
                        "A heavy-lift access platform descends into the excavation below."
                    ),
                },
            ],
        },
        # -----------------------------------------------------------------------
        # Glass Dunes Ruins — 20×14 area mini-overworld
        # Named locations: Access Lift (9,0), Ruins Core (4,8), Relic Vault (15,12)
        # Terrain glyphs: . open glass dune  f crystal formation  R ruin structure
        #                 s shattered glass floor  m crystal wall (impassable)
        #                 * named location
        # Layout: lift descends at top-center; ruins core mid-west;
        #         vault deep south-east via shattered glass approach.
        # -----------------------------------------------------------------------
        "glass_dunes_ruins": {
            "planet_key": "glass_dunes_ruins",
            "planet_name": "Glass Dunes Ruins",
            "entry_point": [9, 0],
            "map": [
                # y=0  Access Lift * at (9, 0)
                "mmmm.....*......mmmm",
                # y=1  Open glass dune corridor
                "mmm..............mmm",
                # y=2  Crystal formations flanking
                "mm....f.....f.....mm",
                # y=3
                "m.....f.....f......m",
                # y=4  Crystal clusters
                "m....ff....ff......m",
                # y=5  Corridor narrows through crystal
                "m..ff.......ff.....m",
                # y=6  Ruin structures begin
                "mm.fR.......Rf...mmm",
                # y=7  Ruin structures expand
                "mm..RRR....RRR....mm",
                # y=8  Ruins Core * at (4, 8)
                "mm..*RRR...RRR....mm",
                # y=9  Shattered glass appears east of ruins
                "m...RRRRss.RRR.....m",
                # y=10  Shattered glass spreads
                "m....sssss..ss.....m",
                # y=11  Approach to vault
                "mm...ssss....s.....m",
                # y=12  Relic Vault * at (15, 12)
                "mmmm.sssss.....*..mm",
                # y=13  Bottom edge
                "mmmm...sss.....mmmmm",
            ],
            "named_locations": [
                {
                    "name": "Access Lift",
                    "x": 9, "y": 0,
                    "room_key": "vanta_ruins_entry",
                    "desc": (
                        "A heavy-lift platform rises through the ceiling, "
                        "gantry lights cycling amber. The route back to the orbital station."
                    ),
                },
                {
                    "name": "Ruins Core",
                    "x": 4, "y": 8,
                    "room_key": "vanta_ruins_core",
                    "desc": (
                        "A cluster of fractured glass columns marks the main ruin formation. "
                        "Light refracts in prismatic patterns from the structure."
                    ),
                },
                {
                    "name": "Relic Vault",
                    "x": 15, "y": 12,
                    "room_key": "vanta_ruins_vault",
                    "desc": (
                        "A collapsed structure half-buried in shattered glass — "
                        "the relic vault. Field energy hums faintly from inside."
                    ),
                },
            ],
        },
        # -----------------------------------------------------------------------
        # Cinder Warrens — 20×14 area mini-overworld
        # Named locations: Entry Hatch (10,0), Warrens Core (5,8),
        #                  Scrapforge Junction (14,11)
        # Terrain glyphs: . tunnel corridor  g generator housing  s salvage pile
        #                 d heat duct  # collapsed passage (impassable)
        #                 * named location
        # Layout: entry hatch top-center; warrens core mid-left via generator
        #         corridor; scrapforge deep south-east via salvage field.
        # -----------------------------------------------------------------------
        "cinder_warrens": {
            "planet_key": "cinder_warrens",
            "planet_name": "Cinder Warrens",
            "entry_point": [10, 0],
            "map": [
                # y=0  Entry Hatch * at (10, 0)
                "####......*......###",
                # y=1  Main generator corridor descends
                "###.......g.......##",
                # y=2  Corridor opens into tunnels
                "##........g........#",
                # y=3  Generator housings begin east flank
                "#.........g.....g..#",
                # y=4  Branching tunnel west toward core
                "#...g.....g.....g..#",
                # y=5  Heat ducts cross the tunnel
                "#...g..d..g..d.g...#",
                # y=6  Deeper into warrens; salvage piles east
                "#...g..dd.g...g.ss.#",
                # y=7  Approach to core chamber
                "#...g...d.g...g.ss.#",
                # y=8  Warrens Core * at (5, 8)
                "#....*....g...g.ss.#",
                # y=9  Collapsed passage splits south; salvage field east
                "#.....#...s...ssss.#",
                # y=10 Scrapforge approach; heat ducts flank
                "#.....#.d.s...ssssd#",
                # y=11 Scrapforge Junction * at (14, 11)
                "#.....#...s...*....#",
                # y=12 South passage dead end
                "##....#...s....s...#",
                # y=13 Bottom edge
                "####..#...s......###",
            ],
            "named_locations": [
                {
                    "name": "Entry Hatch",
                    "x": 10, "y": 0,
                    "room_key": "helion_warrens_entry",
                    "desc": (
                        "A reinforced hatch opens upward into the service tunnel threshold. "
                        "The route back to the surface."
                    ),
                },
                {
                    "name": "Warrens Core",
                    "x": 5, "y": 8,
                    "room_key": "helion_warrens_core",
                    "desc": (
                        "The central chamber of the Cinder Warrens — a wide, low-ceilinged "
                        "space choked with generator housings and salvage piles."
                    ),
                },
                {
                    "name": "Scrapforge Junction",
                    "x": 14, "y": 11,
                    "room_key": "helion_warrens_forge",
                    "desc": (
                        "Three service corridors collapse into one at this junction. "
                        "Sparks from a shorting panel strobe the room every few seconds."
                    ),
                },
            ],
        },
    },
}
