# Helion Vanta — MUD

Space-frontier MUD built on Evennia 4.5 / Python 3.12. Melee-first combat, bioelectric combat fields, a navigable 80×32 overworld grid spanning two planetoids through an impassable asteroid field, NPC tradelane ships traversing the void, quest system, real-time auto-combat, and a skill system that grows through use.

---

## The World

### The Shardfield

The Shardfield (world key: `kael_cluster`) is a dense asteroid cluster in the outer systems. Two large planetoid landmasses — **Helion Reach** (western half) and **Vanta IX** (eastern half) — are separated by roughly sixteen sectors of impassable asteroid void. The overworld is a unified 80×32 navigable grid:

```
x = 0–31   Helion Reach   (scrubland, dust flats, shale ridges, mountains)
x = 32–47  Asteroid Void  (debris field — impassable on foot; tradelane row at y=20)
x = 48–79  Vanta IX       (crystal formations, glass dunes, anomaly zones, ruins)
```

Eighty years ago the first colonial expansion ships reached The Shardfield under charter from the Reach Compact — a now-fragmented interstellar authority that once administered the outer systems. The Compact's collapse roughly thirty years ago left its colonial settlements autonomous. Helion did not fall apart; it adapted. The colonial marshal corps still enforces law, the civilian council still governs, and the spaceport still runs.

**Helion Reach** is the inhabited planetoid in the western cluster: cold, geologically stable, with a spaceport that has grown over eight decades into the primary settlement — population roughly forty thousand. It is self-sufficient in food, power, and basic manufacturing. What it lacks is new capital, new ideas, and reliable law in its industrial sectors.

**The Cinder Warrens** are the industrial underbelly of Helion — the original mining infrastructure, now partially derelict. A network of heat conduits, generator housings, and service corridors that runs beneath the overworld surface near the western settlement. The Warren Raiders, a loose coalition of scavengers and deserters, have claimed this space. The colonial marshal corps does not have the numbers to clear them out cleanly; instead, they contract it out.

---

### Interplanetary Transit

The void between Helion and Vanta IX is impassable on foot — asteroid debris and electromagnetic interference — at an intensity that overmatches any individual field — make unprotected surface crossing impossible. Colonial transport ships run the **y=20 tradelane** of the overworld grid, traversing 16 sectors (x=32–47) to connect the two planetoids.

Ships dock at **Helion Docking Bay** (grid [32,20]) and **Vanta Docking Bay** (grid [47,20]). Each ship spends roughly 2 minutes docked before departing, then crosses the void sector by sector at 40 seconds per tick. Transit time from dock to dock is approximately 10 minutes. Players board at a docking bay and ride the ship's cabin room to the other side.

The Clans tolerate the transit route because they profit from it. The colony depends on it because Vanta artifacts are the most valuable export the system produces.

---

### Vanta IX

Vanta IX is the eastern planetoid of The Shardfield, cold and partially geologically active. Most of the surface is unmapped. What is mapped is the **Glass Dunes** — a vast crater region blanketed in fused silicate formations: columns, arches, and dune-shaped ridges of glass rising from the ground in irregular clusters. The formations predate every survey instrument sent to measure them. Their origin is disputed; the leading theory is that they are the deliberate byproduct of Builder construction processes.

The Clan-built orbital ring above the planetoid serves as the transit hub and the primary point of contact between Clan and colonial interests — accessed via the `vanta_customs` named location on the overworld grid. The Glass Dunes themselves lie on the surface below, accessible via a heavy-lift platform through the station's ventral hull.

**Glass Stalkers** are native predators of Vanta IX — or possibly organisms left behind by the Builders; the distinction is not settled. Their bodies are partially translucent, structured like stressed glass, and they navigate the Dunes by resonance: they sense vibration through the terrain. They are difficult to detect until close. Their carapace is resilient against blunt force and energy dispersal but has structural weak points at the joints that bladed weapons can exploit. Their biofields pulse in irregular bursts — the most powerful natural fields recorded in any Shardfield organism, which reinforces the preference for blades among Dune expeditions.

---

### The Vanta Clans

The Clans arrived on Vanta IX approximately fifty years ago — before formal colonial survey — as independent prospectors, explorers, and groups who had left colonial jurisdiction deliberately. They are not colonial subjects and have resisted every attempt to make them so. The Reach Compact tried twice. The Clans are still here; the Compact is not.

There are six to eight distinct Clan groups, each holding different sections of the ruins territory under Clan law. External affairs are coordinated through a loose Clan Council, but internal disputes are handled within each Clan by its own customs. Clan roles — Blademaster, Elder, Broker — carry genuine authority within their domain and are not colonial honorifics.

The Clans trade with the colony because it is profitable, not out of alignment. Clan weapons and armor (the **Vanta Reave** series) are among the most capable field equipment available in the system, and the Clans sell them selectively. Clan assessors like Relic-Assessor Dynn evaluate and certify artifacts for export.

Clan melee culture developed independently of the colony's. The Clans had the same practical problem — maintaining energy weapons in hostile, resource-constrained terrain is expensive — and reached the same conclusion.

---

### The Builders

Whatever built the ruins on Vanta IX is gone. They are referred to in Clan tradition as **the Prior** — a translation of a Clan term meaning roughly "those who were here before." Colonial academic usage sometimes says "the Ancients," which the Clans consider presumptuous.

The Prior's architecture uses materials and geometric principles inconsistent with any known civilization. The ruins show no signs of catastrophic destruction — the Prior appear to have simply left, taking most of what they built with them and leaving behind the glass formations, certain sealed structures, and the **Vault Guardians**.

Vault Guardians are automated security sentinels that have been running continuously since the Prior departed. Their power source is unknown. They defend sealed reliquary chambers — vaults containing stored artifacts, the purpose and nature of which varies. Defeating a Vault Guardian requires sustained physical combat; they are heavily armored, shielded, and patient.

Artifacts recovered from the vaults range from inert fragments to functional devices that colonial engineers have not been able to fully reverse-engineer. The relics are valuable primarily because they are rare and because the handful of functional ones suggest capabilities that would be significant if understood. The colony's interest in them is economic. The Clans' interest is older and more complicated.

The Glass Dunes themselves may be Prior infrastructure — a deliberate surface treatment rather than a natural phenomenon. The Clans do not commit to an interpretation. The colonial survey teams who suggested the Dunes were decorative did not receive a follow-up grant.

---

### Why Melee Dominates

Energy weapons function in the Helion system. They are not banned or mythologized. They are simply impractical at the frontier scale.

**Manufacturing cost.** Energy weapons and their power cells are produced in inner-world facilities. Freight to the outer systems adds significant cost. Frontier colonies do not have the capital infrastructure to produce them locally.

**Logistics.** Power cells must be replenished, stored, and protected from temperature extremes. In the Cinder Warrens, ambient heat degrades charge packs in hours. On Vanta IX, the Glass Stalkers' resonance-based hunting means a humming power pack is a beacon.

**Shield physics.** Every complex organism in the Shardfield generates a low-level bioelectric field — an evolutionary adaptation to the system's intense electromagnetic environment. In untrained individuals it is negligible. Physical conditioning and sustained combat experience develop it into a functional defense layer capable of dispersing kinetic impact and directed energy fire. Colonists call it a shield. The Clans have older words for it. The mechanism is the same.

A field developed through combat training absorbs roughly two-thirds of any ranged energy or projectile impact. Against melee contact it absorbs the full strike — until depleted. Vibro-edged and mono-filament blades disrupt the biofield at its harmonic resonance frequency, breaking integrity on contact. This is not a secret; it is why blade training is a core colonial security curriculum, and why the Clans reached the same conclusion independently.

Shock batons exploit a different mechanism: electrostatic discharge overwhelms the biofield's output, draining integrity faster than impact alone. Polearms offer reach advantage — a fighter with sufficient training can land a first strike before an opponent with a shorter weapon closes distance.

Ranged weapons remain in use for suppression and area denial. They are not the primary combat tool because the field dispersal math makes blades more reliable per contact than a ranged weapon that loses two-thirds of its energy to a well-developed field.

---

### Factions

| Faction | Description | Present In |
|---|---|---|
| **Helion Colony** | Colonial self-government; marshal corps enforces law, civilian council governs. Underfunded, pragmatic, eighty years of accumulated culture. | Helion Reach |
| **Vanta Clans** | Confederation of semi-nomadic groups holding Vanta IX territory. Independent, commercially engaged, internally governed by Clan law. | Vanta IX |
| **Warren Raiders** | Scavengers and deserters controlling the Cinder Warrens. No central leadership; loosely coordinated around territorial control. | Cinder Warrens |
| **Dock Saboteurs** | Operatives of unclear affiliation disrupting docking bay access and Dune excavation operations. Possibly inner-world corporate agents seeking relic access control. The Clans officially deny involvement. | Vanta ruins |

---

## Guilds

Two guilds are available, each with a hall that must be visited to join or advance. Guild rank confers passive stat bonuses per rank and unlocks guild skills trainable with XP.

### Iron Covenant
**Location:** Iron Covenant Hall (Helion Reach, grid [23,14])  
**Passive per rank:** +1 STR · +1 CON · +5 HP max  
**Guild skills:**

| Skill | Type | Rank Req | Effect |
|---|---|---|---|
| Iron Stance | Passive | 1 | +1 phys_reduction per 20% trained (max +5) |
| Throw Weight | Passive | 1 | +1 weapon damage per 20% trained (max +5) |
| Find Weakness | Passive | 1 | +1% crit chance per 10% trained (max +10%) |
| Enhanced Criticals | Passive | 3 | +1 raw crit damage per 25% trained (max +4) |
| Sunder Strike | Active | 5 | 2-round wind-up: 1.5× weapon damage +10 flat, ignores parry; costs 40 Stamina |

### PSI Weavers
**Location:** PSI Weavers Sanctum (Vanta IX, grid [55,14])  
**Passive per rank:** +1 MIND · +10 PSI max  
**Guild skills:**

| Skill | Type | Rank Req | Effect |
|---|---|---|---|
| Focused Channel | Passive | 1 | PSI Heal restores +2 HP per 25% trained (max +8 bonus) |
| Resonance Shield (`psi ward`) | Active | 1 | 1-round PSI barrier absorbing 20 + (rank×2) melee damage; costs 30 PSI |
| PSI Bolt (`psi bolt`) | Active | 3 | Concentrated PSI blast stronger than shock; costs 35 PSI |
| Mind Shatter (`psi shatter`) | Active | 6 | Massive PSI burst + stuns target 1 round; costs 50 PSI |

---

## World Layout

### Overworld — The Shardfield (80×32 grid)

```
 HELION REACH (x=0–31)      ASTEROID VOID (x=32–47)   VANTA IX (x=48–79)
 ─────────────────────────  ────────────────────────   ──────────────────────────
 (15, 5) *  Helion Spaceport                           (63, 5) *  Vanta Customs Ring
 (23,14) *  Iron Covenant Hall                         (55,14) *  PSI Weavers Sanctum
  (8,21) *  Cinder Warrens Entry                       (70,22) *  Glass Dunes Entry

                              y=20 tradelane (=)
            [32,20] Helion Docking Bay ═══════════════ [47,20] Vanta Docking Bay
                        ↑ NPC transport ships traverse x=32→47 (or reverse) ↑
```

`*` glyphs on the overworld are named locations — step on one and `enter` to enter the instanced area. Mountains (`m`) and toxin flats (`~`) are impassable. Asteroid debris (`:`) and the tradelane (`=`) in the void zone are impassable on foot.

### Instanced Areas

```
HELION REACH                              VANTA IX
────────────────────────────────────────  ────────────────────────────────────────
[Gate Concourse] ─east─ [Dockside         [Customs Ring] ─east─ [Nocturne Bazaar]
      Market]
        │south                            [PSI Weavers Sanctum]  (standalone)
[Helion Docking Bay] ──board──┐
                               │           [Glass Dunes Access Lift]
                    [Ship Cabin] ──────────       │down
                    (NPC transport)         [Glass Dunes Ruins]
                               │                  │south
                               └── [Vanta Docking Bay]    [Shattered Relic Vault]

CINDER WARRENS (underground, below Helion surface)
  [Service Tunnel Threshold]
        │east
  [Cinder Warrens Core] ─east─ [Scrapforge Junction]

IRON COVENANT HALL (standalone, Helion surface)
```

---

## NPCs

| NPC | Role | Location | Faction | Notes |
|---|---|---|---|---|
| Marshal Kaine | Quest giver | Gate Concourse | Helion Colony | Gives and closes both quests via `talk` |
| Quartermaster Vex | Vendor | Dockside Market | Helion Colony | Sells colony-tier gear |
| Scout Kess | Information | Service Tunnel Threshold | Helion Colony | Intel on Warren Raiders |
| Tech-Assessor Mira | Appraiser | Dockside Market | Helion Colony | Reveals hidden item stats via `appraise` |
| Blademaster Thorne | Trainer | Nocturne Bazaar | Vanta Clans | Skill training info |
| Broker Sorn | Vendor | Customs Ring | Vanta Clans | Sells Vanta-tier gear |
| Elder Lyros | Information | Glass Dunes Access Lift | Vanta Clans | Intel on Glass Stalkers and the Prior |
| Relic-Assessor Dynn | Appraiser | Customs Ring | Vanta Clans | Reveals hidden item stats via `appraise` |

---

## Mobs

| Key | Name | Location | Level | HP | Shield | XP | Tier | Weak To | On-Hit Effect |
|---|---|---|---|---|---|---|---|---|---|
| `warren_raider` | Warren Raider | Cinder Warrens Core | 2 | 40 | 30 | 25 | common | — | — |
| `slag_hound` | Slag Hound | Scrapforge Junction | 2 | 35 | 20 | 20 | common | — | — |
| `dock_saboteur` | Dock Saboteur | Glass Dunes Ruins | 3 | 50 | 45 | 40 | common | — | — |
| `glass_stalker` | Glass Stalker | Glass Dunes Ruins | 5 | 80 | 70 | 100 | elite | blades | bleed (2 ticks) |
| `vault_guardian` | Vault Guardian | Shattered Relic Vault | 7 | 120 | 100 | 175 | elite | bludgeons | weakened (2 ticks) |

Mobs respawn 120 seconds after death in their origin room.

Elite mobs have a `weak_to` weapon type: when the player's equipped weapon matches, damage is multiplied by 1.25 and the combat log shows `[WEAKNESS: <type>]`.

---

## Quests

### Helion Introduction: Colony Defense
**Giver:** Marshal Kaine (Gate Concourse)  
**Accept:** Talk to Marshal Kaine, or `quest accept intro`  
- Defeat 2 Warren Raiders in the Cinder Warrens  
- Return to Marshal Kaine  

**Rewards:** 150 XP · 50 credits · Recruit Field Brace

---

### Vanta Expedition: Artifact Recovery
**Giver:** Marshal Kaine  
**Requires:** Colony Defense complete  
**Accept:** Talk to Marshal Kaine, or `quest accept vanta` from Shuttle Dock A3  
- Board the Shardline shuttle at Helion  
- Arrive at Vanta IX  
- Defeat 3 Glass Stalkers  
- Recover relic from the Shattered Relic Vault (defeat Vault Guardian)  
- Return to Helion and report to Marshal Kaine  

**Rewards:** 400 XP · 200 credits · Veteran Field Brace

---

## Combat System

Combat is real-time and tick-based: one round every 3 seconds via Evennia's `TICKER_HANDLER`.

### Round Display
```
******************** Round 3 ********************
[######  ] You badly wound Glass Stalker.  [WEAKNESS: blades]
[###     ] Glass Stalker hits you.  [BLEED applied]
Bleed: you lose 4 HP.
Glass Stalker is noticeably hurt (54%).
72H 60SH 85ST 60P>
```

The compact prompt line (`72H 60SH 85ST 60P>`) appears after every combat round and after every regen tick while resources are below maximum. Values are color-coded: green ≥ 60 %, yellow ≥ 30 %, red < 30 %.

### Hit Chance
```
hit_chance = min(90, 65 + skill_melee // 2 + stamina // 15 + weapon_type_skill // 4)
```
At L1 (melee 10, full stamina, weapon_type_skill 0): ~76% to hit. Hard ceiling: 90%.

DEX above 10 adds to effective `skill_melee` (+1 per 5 DEX) and effective `skill_dodge` (+1 per 4 DEX).

### Passive Defense (resolved in order, one per round)
| Layer | Trigger | Effect | Stamina Cost |
|---|---|---|---|
| Avoid | Pure reflex, Focus-boosted (max ~10%) | Full miss | 0 |
| Dodge | skill_dodge + Focus bonus (cap +30 pp) | Full miss | 4 |
| Parry | skill_parry + Focus bonus (cap +35 pp total, shield parry +15) | 50% damage reduction | 3 |
| Hit | Nothing triggered | Full damage lands | — |

### Damage & Shields
- Shields absorb melee hits at face value. Overflow goes to HP.
- Ranged attacks deal 1/3 damage (shield dispersal).
- `phys_reduction` from armor is subtracted from raw melee damage before shield calculation (floor 1).
- At shield 0 → **SHIELD BREAK** event; all subsequent hits deal full HP damage.

### Critical Hits
Base crit chance: 18%. Each point of LUCK above 10 adds 1 % (capped effectively around LUCK 20 for ~28 %). A crit deals +8 raw damage and shows `[CRITICAL HIT!]`.

### Weakness Bonus
When the player's active weapon type matches `mob_data["weak_to"]`: `×1.25` damage, `[WEAKNESS: <type>]` tag in combat line.

### Damage Bars & Hit Verbs
| Damage | Bar | Verb |
|---|---|---|
| 0 | — | misses |
| 1–3 | `[#       ]` | grazes |
| 4–8 | `[###     ]` | hits |
| 9–15 | `[#####   ]` | wounds |
| 16–25 | `[######  ]` | badly wounds |
| 26+ | `[########]` | devastates |

### Mob Health Labels
| % HP | Label |
|---|---|
| 90–100% | in excellent shape |
| 70–89% | slightly hurt |
| 50–69% | noticeably hurt |
| 30–49% | not in good shape |
| 15–29% | badly wounded |
| <15% | near death |

---

## Status Effects

Applied by techniques and mob on-hit abilities. Multiple effects can be active simultaneously; re-applying keeps whichever duration is longer (no stacking).

| Effect | Source | Mechanical Impact |
|---|---|---|
| **Bleed** | Glass Stalker on-hit; player `slash` technique | Deals 4 HP damage per combat tick (bypasses shields and armor) |
| **Stun** | Player `concussion` technique | Mob skips its attack action that round |
| **Weakened** | Vault Guardian on-hit; player `lunge` technique | −10 penalty to dodge and parry skill for N rounds |

---

## Techniques

Queued during active combat. Each has a wind-up period (rounds) before it fires. Only one technique can be queued at a time.

**Requirements:** the matching weapon type must be equipped in `main_hand`, and the corresponding weapon-type skill must be ≥ 20. Skills grow automatically through combat — no manual unlock step.

| Command | Weapon Req | Skill Req | Wind-Up | Effect |
|---|---|---|---|---|
| `slash` | blades | blades ≥ 20 | 1 round | Applies **bleed** (3 ticks) to target |
| `concussion` | bludgeons | bludgeons ≥ 20 | 2 rounds | Applies **stun** (1 tick) — mob loses next attack |
| `lunge` | polearms or blades | polearms/blades ≥ 20 | 1 round | Damage + applies **weakened** (2 ticks); 50% of damage pierces shield to HP |

---

## Character Backgrounds

Chosen once during character creation via an EvMenu walkthrough that fires automatically on first login.  Each background applies starting bonuses to skills and/or attributes; bonuses are permanent and stack naturally with guild ranks and level-up gains.

| Background | Starting Bonuses | Flavour |
|---|---|---|
| **Colonial Recruit** | melee +3 · parry +2 · CON +1 (→ +3 HP max) | Former Helion marshal corps. Knows the Warrens, knows the drill. |
| **Warrens Scavenger** | bludgeons +3 · camping +4 · PER +1 | Grew up below the surface in the Cinder Warrens industrial underbelly. |
| **Clan Initiate** | blades +4 · dodge +2 · DEX +1 | Trained in Vanta Clan blade discipline. Earned, not given. |
| **Frontier Contractor** | ranged +3 · CHA +1 · LUCK +1 · +30 credits | Independent operator. Worked jobs across the system. Good at leaving. |
| **Compact Remnant** | melee +1 · MIND +2 (→ PSI max 70) | Descended from the Reach Compact's survey corps. Unusual PSI sensitivity. |

Background is displayed on the `score` sheet.  Pre-existing characters (created before this system) retain their flat defaults and are not asked to choose.

---

## Character Stats & Progression

### Resources (Level 1 base)
| Resource | Base Max | Description |
|---|---|---|
| HP | 100 | Hit points. CON scales max (+3 per CON point trained). |
| Shield | 100 | Bioelectric combat field. Absorbs melee/ranged hits before HP is touched. Grows with conditioning and experience. |
| Stamina | 100 | Drained by passive defense actions; recovers between rounds. |
| Focus | 50 | Boosts all passive defense thresholds. |
| PSI | 60 | Ability resource. Base: `10 + MIND × 5`. Regens at `2 + (MIND−10)//5` per tick. |
| XP | — | Persistent; checked against level threshold on each kill and quest completion. |
| Credits | — | Currency for vendors. |

### Attributes
Seven attributes, all starting at 10, hard cap 30. Displayed on `score` and `skills`.

| Attr | Effect |
|---|---|
| STR | +1 weapon_damage_bonus per 3 STR above 10 |
| DEX | +1 effective melee per 5 DEX above 10; +1 effective dodge per 4 DEX above 10 |
| CON | +3 HP max when trained; scales HP regen: `1 + (CON−10) // 5` per tick |
| MIND | +5 PSI max when trained; scales PSI regen: `2 + (MIND−10) // 5` per tick |
| CHA | Vendor negotiation: improves buy/sell rates via `shop` / `buy` / `sell` |
| PER | PER ≥ 12: `(enhanced scan active)` note on `scan`; PER ≥ 15: mob health states shown in `scan` |
| LUCK | Crit chance: `0.18 + max(0, LUCK−10) × 0.01` |

### Level Progression
| Level | XP Required | Stat Gains | Attr / Skill Gains |
|---|---|---|---|
| 2 | 200 | +10 HP · +10 Shield · +8 Stamina · +5 Focus | +1 all 7 attrs (auto); CON +1 → +3 HP max, MIND +1 → +5 PSI max · +3 skill pts |
| 3 | 500 | (same) | (same) |
| 4 | 1,000 | (same) | (same) |
| 5 | 2,000 | (same) | (same) |
| 6 | 3,500 | (same) | +2 attr points to spend via `train <attr>` · +3 skill pts |
| 7 | 5,500 | (same) | (same as 6) |
| 8 | 8,000 | (same) | (same as 6) |
| 9 | 11,000 | (same) | (same as 6) |
| 10 | 15,000 | (same) | (same as 6) |

All resources fully restored on level-up (including PSI). Skill points are spent via `train <skill>`; attr points via `train <attr>` (level 6+ only).

### Regeneration (every 5 seconds)
| State | HP | Shield | Stamina | Focus | PSI |
|---|---|---|---|---|---|
| Out of combat | `1 + (CON−10)//5` | +1 | +3 | +2 | `2 + (MIND−10)//5` |
| In combat | 0 | 0 | +1 | +1 | 0 |

At base CON 10 / MIND 10: +1 HP/tick and +2 PSI/tick out of combat. A compact prompt (`72H 60SH 85ST 60P>`) is sent after each tick when any resource is below maximum.

**Sleep / Rest:** `sleep` (aliases: `rest`, `camp`, `meditate`) starts a 20-second timer. On natural wake: lump-sum recovery of `20 + camping//2` HP, `30 + camping//2` Stamina, `15 + camping//2` Shield. Early wake via `wake` gives half. Sleep does **not** alter the regen tick rate; it is additive on top.

---

## Skill System

### Combat Skills (melee / dodge / parry)
Grow passively through use (25% chance per successful trigger, up to soft cap 60). Above 60, spend skill points via `train`.

| Skill | Grows by | Soft Cap | Max (with points) |
|---|---|---|---|
| melee | Landing a hit | 60 | 100 |
| dodge | Successfully dodging | 60 | 100 |
| parry | Successfully parrying | 60 | 100 |

Displayed on `score` as adjectives: **poor → weak → fair → solid → strong → excellent → masterful**.

### Weapon-Type Skills (blades / bludgeons / polearms / ranged)
Grow the same way as combat skills (25% chance per relevant use, same soft cap). Feed into hit chance (`+weapon_type_skill // 4`). Reaching skill ≥ 20 unlocks the corresponding technique. Displayed as raw numbers.

| Type | Bonus Mechanic | Technique Unlocked at 20 |
|---|---|---|
| blades | No passive bonus; feeds hit chance and unlocks slash/lunge | `slash`, `lunge` |
| bludgeons | +damage against shields per round; bonus scales with skill | `concussion` |
| polearms | First-strike bonus damage on round 1 of combat | `lunge` |
| ranged | Uses ranged damage path (shield-dispersed at 1/3 while shield is active) | — |

### Survival Skills
| Skill | Grows by | Effect |
|---|---|---|
| camping | Spend skill points via `train camping` | Increases lump-sum rest recovery: `+camping//2` to HP/Stamina/Shield |

### Mob Skill Levels
| Mob | Melee | Dodge | Parry |
|---|---|---|---|
| Warren Raider | 15 | 8 | 5 |
| Slag Hound | 20 | 12 | 3 |
| Dock Saboteur | 25 | 15 | 10 |
| Glass Stalker | 35 | 22 | 18 |
| Vault Guardian | 45 | 18 | 30 |

Mobs without explicit stat entries derive stats from `stats_from_level(level)`:
`hp = 14 + level×13`, `shield = 4 + level×13`, `melee = 5 + level×5`, `dodge = 2 + level×3`, `parry = 1 + level×2`, `xp = level×15`.

---

## Equipment

### Slots
`head · torso · legs · feet · main_hand · off_hand · utility`

Two-handed weapons occupy both `main_hand` and `off_hand`. Shield batteries fit `utility` or `off_hand`. Dual-wielding (two one-handed weapons) penalises the off-hand attack (`OFFHAND_HIT_PENALTY = 15`). Shields in `off_hand` grant `shield_parry_bonus = 15` to the parry cap.

### Armor

`armor_bonus` raises `hp_max` while equipped (reversed on unequip). `phys_reduction` reduces raw melee damage taken each hit (floor 1, computed from all equipped armor slots each round).

**Colony tier** (sold at Dockside Market, Helion)

| Key | Slot | HP Bonus | Phys Reduction | Price |
|---|---|---|---|---|
| `colony_helmet` | head | +10 | 1 | 50 cr |
| `colony_vest` | torso | +25 | 3 | 90 cr |
| `colony_greaves` | legs | +10 | 1 | 50 cr |
| `colony_boots` | feet | +5 | 1 | 25 cr |

Full colony set: +50 HP max, 6 phys_reduction total.

**Vanta Reave tier** (sold at Customs Ring, Vanta IX)

| Key | Slot | HP Bonus | Phys Reduction | Price |
|---|---|---|---|---|
| `vanta_reave_helm` | head | +20 | 2 | 130 cr |
| `vanta_reave_cuirass` | torso | +45 | 5 | 200 cr |
| `vanta_reave_legguards` | legs | +20 | 2 | 130 cr |
| `vanta_reave_boots` | feet | +10 | 1 | 70 cr |

Full Vanta Reave set: +95 HP max, 10 phys_reduction total.

Hidden stats (`phys_reduction`, `damage_bonus`) are not shown in `shop` or `eq`. Use `appraise <item>` near an appraiser NPC (Tech-Assessor Mira on Helion, Relic-Assessor Dynn on Vanta) to reveal them as adjective descriptions.

### Weapons

| Key | Type | Hands | Damage Bonus | Price | Notes |
|---|---|---|---|---|---|
| `training_vibroblade` | blades | 1H | +0 | — | Default starting weapon |
| `parrying_dagger` | blades | 1H | +2 | 50 cr | Fits main or off-hand |
| `shock_baton` | bludgeons | 1H | +4 | 65 cr | Fits main or off-hand |
| `mono_edge_blade` | blades | 1H | +5 | 75 cr | |
| `arc_lance` | polearms | 2H | +9 | 140 cr | First-strike bonus round 1 |
| `vanta_relic_shard` | blades | 1H | +8 | 150 cr | Vanta-only |
| `heavy_arc_blade` | blades | 2H | +14 | 200 cr | Vanta-only |
| `colony_sidearm` | ranged | 1H | +7 | 110 cr | Colony vendor |
| `vanta_pulse_rifle` | ranged | 2H | +12 | 220 cr | Vanta vendor |

### Shield Modules

| Key | Slot | Shield Bonus | Price |
|---|---|---|---|
| `recruit_shield_battery` | utility / off_hand | +20 shield max | 40 cr |
| `veteran_shield_upgrade` | utility / off_hand | +40 shield max | 100 cr |

---

## Commands

### Navigation
| Command | Description |
|---|---|
| `n s e w` | Move cardinally (overworld or instanced area) |
| `ne nw se sw` | Diagonal movement |
| `8 2 4 6 7 9 1 3` | Numpad movement |
| `5` | Look (numpad centre) |
| `map` | 21×15 zoomed overworld minimap centred on current position |
| `enter` | Enter the named location (`*`) at current overworld cell |
| `board` | Board a docked NPC transport ship at a docking bay |

### Combat
| Command | Description |
|---|---|
| `attack <target>` | Start auto-combat (aliases: `kill`, `fight`, `k`) |
| `attack stop` | Disengage |
| `slash` | Queue Slash technique — requires blades ≥ 20, blades weapon equipped |
| `concussion` | Queue Concussion technique — requires bludgeons ≥ 20, bludgeons weapon equipped |
| `lunge` | Queue Lunge technique — requires polearms/blades ≥ 20, matching weapon equipped |

### Information
| Command | Description |
|---|---|
| `look` / `l` | Room description and exits |
| `look <target>` / `la <target>` | Inspect mob or NPC (health label, description) |
| `scan` | Tactical overview: planet, area, room type, hostiles; PER ≥ 15 shows mob health states |
| `status` / `score` / `stats` | Full stat sheet — BatMUD-style `[ val / max ]` resource blocks, adjective skills |
| `consider <target>` / `con` | Threat assessment: 6-tier adjective scale + quality of mob's offence and footwork |
| `appraise <item>` | Reveal hidden item stats as adjectives (requires appraiser NPC in room) |

### Quests & Social
| Command | Description |
|---|---|
| `quest` | View contract board |
| `quest accept <key>` | Accept a quest (aliases: `intro`, `vanta`) |
| `quest progress` | Active quest objectives |
| `quest turnin <key>` | Turn in completed quest |
| `tasks` | Alias for `quest progress` — show active objectives |
| `talk <npc>` | Talk to NPC; Marshal Kaine auto-accepts and closes quests in conversation |

### Guilds
| Command | Description |
|---|---|
| `guilds` | List available guilds, your membership, and current rank |
| `join <guild>` | Join a guild (must be at that guild's hall) |
| `advance` | Spend XP to gain one rank in your guild (at the guild hall) |
| `leaveguild` | Leave your current guild |
| `sunder` | Iron Covenant active: massive 2-round wind-up strike ignoring parry (rank 5+, costs 40 Stamina) |

### Skills & Attributes
| Command | Description |
|---|---|
| `skills` / `sk` | Current skill levels, unspent skill/attr points, and full attribute block |
| `train <skill>` | Spend 1 skill point to raise a skill (melee, dodge, parry, blades, bludgeons, polearms, camping) |
| `train <attr>` | Spend 1 attr point to raise an attribute (str, dex, con, mind, cha, per, luck) — level 6+ only |
| `psi` | View PSI pool, MIND stat, and all available PSI abilities with costs |
| `psi heal` | Channel PSI inward to restore HP (any time; costs 20 PSI) |
| `psi shock` | Discharge PSI at combat target, bypassing armor (costs 25 PSI) |
| `psi ward` | PSI Weavers rank 1+: erect a 1-round barrier absorbing melee damage (costs 30 PSI) |
| `psi bolt` | PSI Weavers rank 3+: concentrated PSI blast, stronger than shock (costs 35 PSI) |
| `psi shatter` | PSI Weavers rank 6+: massive PSI burst + stuns target 1 round (costs 50 PSI) |

### Character Reincarnation
| Command | Description |
|---|---|
| `recreate confirm` | Wipe character to level 1 and restart chargen; credits and inventory preserved |
| `reincarnate` | Preview reincarnation cost and soul pool at a Soul Archive (Helion Gate or Vanta Customs) |
| `reincarnate confirm` | Pay the credit fee; bank XP into Soul Pool; reset to level 1; inventory and credits preserved |
| `claimlevels` | After chargen, spend banked Soul Pool XP to reclaim levels one at a time |

### Recovery & Inventory
| Command | Description |
|---|---|
| `sleep` / `rest` / `camp` | Sleep for 20 s; wake with lump-sum HP/Stamina/Shield recovery (Camping skill scales amount) |
| `wake` / `stand` | Wake early — half recovery |
| `inventory` / `inv` / `i` | List carried items and equipped slots |
| `eq` | Equipment overview (slots, equipped items) |
| `equip <item>` | Equip an item from inventory |
| `unequip <slot>` | Unequip item from a slot |

### Economy
| Command | Description |
|---|---|
| `shop` / `browse` | List vendor wares and prices |
| `buy <item>` / `purchase` | Buy from vendor in current room |
| `sell <item>` | Sell an unequipped item to vendor (price scales with CHA) |
| `reputation` / `rep` / `factions` | Show Helion Colony and Vanta Clans standings |

### Admin
| Command | Description |
|---|---|
| `mudbuild` | Build or refresh world (Builder permission) |
| `mudbuild reset` | Force rebuild all rooms, mobs, and NPCs |

---

## Economy

Credits are earned from quest rewards and mob kills. Common mobs drop 3–8 credits; elite mobs drop 20–40. The intended loop:

> Complete intro quest (50 cr) → buy colony boots or a shock baton → complete Vanta expedition (200 cr) → buy Vanta Reave armor → tackle elite content

---

## Tech Stack

| | |
|---|---|
| Framework | Evennia 4.5.0 |
| Python | 3.12 (venv at `.venv312`) |
| Database | SQLite (`helionvanta/evennia.db3`) |
| Ports | Telnet 4000 · Web 4001 · WebSocket 4002 |

### Startup
```powershell
cd helionvanta
..\.venv312\Scripts\python.exe ..\tools\evennia_cli.py start
..\.venv312\Scripts\python.exe ..\tools\evennia_cli.py reload
..\.venv312\Scripts\python.exe ..\tools\evennia_cli.py status
..\.venv312\Scripts\python.exe ..\tools\evennia_cli.py stop
```

### First-Time Setup
```powershell
.\tools\setup-evennia-env.ps1      # create venv and install deps
cd helionvanta
..\.venv312\Scripts\python.exe ..\tools\evennia_cli.py migrate
..\.venv312\Scripts\python.exe ..\tools\evennia_cli.py start
# in-game as superuser:
mudbuild
```

### Tests
```powershell
# from repo root
.venv312\Scripts\python.exe -m pytest tests/ -q
```
668 passing tests (~0.4 s), 0 failures.

---

## File Map

```
mudgame/
  contracts.py              CharacterStats dataclass (7 attr fields), EQUIPMENT_SLOTS, default_equipped()
  data/world_data.py        All world content: rooms, NPCs, mobs, items, quests, overworld grids
                            (_HR_ROWS, _VX_ROWS, _VOID_ROWS → _KAEL_MAP unified 80×32 grid)
  systems/combat.py         resolve_attack_passive(), apply_hit() (phys_reduction, STR/DEX/LUCK wired)
  systems/overworld.py      Terrain defs (HELION_TERRAIN, VANTA_TERRAIN, VOID_TERRAIN, PLANET_TERRAIN),
                            zone-aware colour dispatch (_colour), minimap renderer, encounter roller
  systems/status_effects.py tick_effects(), apply_effect(), is_stunned(), defense_penalty()
  systems/techniques.py     TECHNIQUE_DEFS (weapon_type_req, skill_req), resolve_technique(),
                            check_technique_requirements()
  systems/mobs.py           stats_from_level(level) — stat derivation from mob level

helionvanta/
  commands/cmd_utils.py             Shared helpers, constants, and utility functions (no Command classes);
                                    _format_prompt(), _send_prompt(), _regen_tick(), LEVEL_XP_TABLE, etc.
  commands/guild_commands.py        CmdGuilds, CmdJoin, CmdAdvance, CmdLeaveGuild, CmdSunder, CmdWarlordStrike
  commands/admin_commands.py        CmdMudBuild, CmdResetChar, CmdClaimLevels, CmdGrantShip
  commands/inventory_commands.py    CmdInventory, CmdGet, CmdEquip, CmdShop, CmdBuy, CmdSell,
                                    CmdEquipment, CmdSkills, CmdTrain, CmdTechnique
  commands/social_commands.py       CmdScan, CmdConsider, CmdAppraise, CmdStatus, CmdReputation,
                                    CmdLook, CmdMoveAlias, CmdTalk
  commands/quest_commands.py        CmdQuest, CmdTasks, CmdTravel, CmdMap
  commands/char_commands.py         CmdRecreate, CmdReincarnate, _do_character_reset, _reincarnation_fee
  commands/combat_commands.py       Full combat engine (_run_combat_round, _combat_tick, regen ticker)
                                    + CmdAttack, CmdKick, CmdSleep, CmdWake, CmdAmbush;
                                    ambush session flag; warlord_strike technique handler;
                                    guild stamina_max/psi_max bonuses applied at regen/sleep time
  commands/psi_commands.py          CmdPsi (psi heal / shock / ward / bolt / shatter / lance);
                                    `psi lance` routes to _psi_lance() — direct HP damage bypassing shields
  commands/mud_commands.py          Deprecated tombstone — safe to delete
  commands/overworld_commands.py    CmdOverworldMove (n/ne/e/…), CmdOverworldMap (21×15 view),
                                    CmdOverworldEnter (enter named location), CmdOverworldLook
  commands/default_cmdsets.py       Cmdset registrations
  typeclasses/characters.py         Character typeclass (7 attrs, PSI, status_string BatMUD style)
  typeclasses/rooms.py              Room typeclass (exit display, actor list with colour)
  typeclasses/overworld_room.py     OverworldRoom typeclass — manages overworld cmdset, encounter-mob
                                    listing in return_appearance()
  typeclasses/ship.py               NpcTransportShip — tick-based grid traversal along SHIP_GRID_ROUTE
                                    (y=20 tradelane, x=32–47); SHIP_GRID_ROUTE, DOCK_TICKS, SHIP_TICK_INTERVAL
  world/mud_bootstrap.py            World builder (rooms, exits, NPCs, mobs, overworld room, named locations)
  world/corridor_bootstrap.py       Docking bay rooms + NPC ship creation
  world/runtime_state.py            (legacy shuttle state machine — superseded by NpcTransportShip)
  world/help_entries.py             In-game help content
  server/conf/settings.py           Evennia settings
  server/conf/connection_screens.py Connect screen (lore + login instructions)
  server/conf/at_server_startstop.py at_server_cold_start: clears regen flags, auto-builds world
  server/.static/webclient/js/plugins/oob.js
                                    OOB plugin: silences room_update/stats_update noise;
                                    onText converts raw \x1b[NNm ANSI (overworld colours) to
                                    inline spans before default_out.js appends them

tests/
  test_combat.py            Combat mechanics: hit chance, phys_reduction, stats_from_level
  test_techniques.py        Technique gate (check_technique_requirements), schema, resolve smoke tests
  test_status_effects.py    Status effect and technique tests
  test_world.py             World data integrity
  test_travel.py            Shuttle state machine
  test_commands.py          Command integration
  test_overworld.py         Overworld terrain, colour dispatch, minimap rendering, encounter roll,
                            ship tick logic, named location coords

tools/
  evennia_cli.py            Evennia lifecycle wrapper
  setup-evennia-env.ps1     Python 3.12 venv bootstrap

client.html                 Standalone custom HTML MUD client (connects via WebSocket directly);
                            evenniaClassToInline() converts Evennia markup spans to inline styles;
                            ansiToHtml() converts raw \x1b[NNm ANSI (overworld map) to inline styles
```

---

## Implementation Status

### Complete

| System | Notes |
|---|---|
| World build | 23 instanced rooms across 8 areas (Helion, Cinder Warrens, Glass Dunes, Subsurface Ruin Complex, Vanta, docking bays); overworld room (80×32 kael_cluster grid); ship cabin; 10 NPCs, 11 mobs |
| Overworld system | 80×32 unified grid; zone-aware terrain/colour; encounter spawning; 21×15 minimap; named-location entry |
| NPC transport ships | Cell-by-cell grid traversal (y=20 tradelane, x=32–47); dock/depart cycle; player boarding |
| Room descriptions | Atmospheric text on all 16 rooms |
| Character typeclass | HP / Shield / Stamina / Focus / PSI / XP / Level / Credits / 7 Attrs persisted |
| Level system | L1–L10 main cap (`MAIN_LEVEL_CAP`); XP table extended to L40 (guild advancement); stat gains, attr auto-gains (L2–L5) + attr points (L6+), full restore on level-up, +3 skill points/level |
| Attribute system | STR/DEX/CON/MIND/CHA/PER/LUCK; base 10, cap 30; wired to combat, regen, scan, crit |
| PSI pool | 10 + MIND×5 base; MIND-derived regen; displayed in score and prompt |
| Combat ticker | 3 s/round via TICKER_HANDLER; BatMUD-style display |
| Shield mechanics | Ranged 1/3 damage, melee full, shield break event, phys_reduction from armor |
| Passive defense | Avoid / Dodge / Parry with Focus and stamina interaction |
| Critical hits | Base 18% + 1% per LUCK above 10; +8 raw damage on crit |
| Status effects | Bleed, Stun, Weakened — tick each round, player and mob sources |
| Techniques | Slash (bleed), Concussion (stun), Lunge (damage + weakened); wind-up queue; gated by weapon type and skill ≥ 20 |
| Skill system | melee / dodge / parry — use-based growth (25%), soft cap 60, points above cap |
| Weapon-type skills | blades / bludgeons / polearms / ranged — grow with use, feed hit chance, type bonuses, unlock techniques at ≥ 20 |
| Camping skill | Scales lump-sum sleep recovery |
| Armor system | 8 pieces (colony + Vanta Reave); armor_bonus raises hp_max; phys_reduction reduces melee damage |
| Equipment slots | 7 slots; dual, shield, and two-handed combat styles |
| Item catalog | 29 items (weapons, shield modules, armor pieces, grind-tier gear); grind-tier priced above total quest credit pool (1,080 cr) to require mob farming |
| Vendor system | Quartermaster Vex (Helion), Broker Sorn (Vanta); grind-tier gear priced above quest total |
| `consider` command | 6-tier threat scale + mob offence/footwork quality |
| `appraise` command | Reveals phys_reduction / damage_bonus as adjectives; requires appraiser NPC |
| Appraiser NPCs | Tech-Assessor Mira (Helion market), Relic-Assessor Dynn (Vanta customs) |
| `score` display | BatMUD-style `=-=+` cyan border; `[ val / max ]` color-coded pool blocks; adjective combat skills; attr brackets |
| Compact prompt | `72H 60SH 85ST 60P>` after each combat round and regen tick (when below max); color-coded |
| `map` command | Local compass grid, 1-step radius |
| Quest system | 10 quests (2 main + 8 secondary) with prerequisites/progression; accept/progress/turnin via command or NPC talk |
| Shuttle travel | State machine Helion ↔ Vanta; board / travel commands |
| Mob respawn | 120 s delay, restored stats, returns to origin room |
| Regen ticker | 5 s interval; 2 states (in-combat / out-of-combat); CON-derived HP regen; MIND-derived PSI regen |
| Sleep / rest | `sleep` command: 20 s timer, lump-sum recovery on wake; camping skill scales amount; partial recovery on early `wake` |
| Relic objective | Triggers on first entry to Shattered Relic Vault with guardian alive |
| Connect screen | Themed lore hook + login instructions |
| In-game help | `help background`, `help combat`, `help skills`, `help equipment`, `help techniques`, `help status effects`, `help quests`, `help travel`, `help economy` |
| Auto-build on cold start | `at_server_cold_start` calls `build_vertical_slice()` |
| Mob credit drops | Randomised credit range on every mob kill (3–8 common, 20–40 elite); awarded alongside XP |
| Character backgrounds | 5 backgrounds (Colonial Recruit, Warrens Scavenger, Clan Initiate, Frontier Contractor, Compact Remnant); EvMenu on first login; skill + attr bonuses; displayed on `score` |
| Guild system | Iron Covenant (Helion) and PSI Weavers (Vanta); rank 1–20 (cap 20); max 30 tokens total across both guilds; passive per-rank stat bonuses (rank 11–20 via unified `bonus_per_N` scalar dispatch); trainable guild skills; `sunder` (Iron, rank 5+) and `warlord` (Iron, rank 15+) active skills |
| PSI abilities | `psi heal / shock / ward / bolt / shatter / lance`; `psi lance` bypasses shields entirely (rank 13, `void_lance` skill > 0%) |
| Ambush system | `alertness` stat; `ambush` command; mobs with `can_ambush: true` may surprise-attack on room entry; ambush flag blocks defender parry |
| In-game help | 17 entries: `background`, `combat`, `skills`, `equipment`, `techniques`, `status effects`, `quests`, `travel`, `economy`, `guilds`, `advancement`, `psi`, `overworld`, `reincarnation`, `commands`, `abilities`, `techniques advanced` |
| Reincarnation system | `reincarnate` at Soul Archive: pays credit fee, banks XP into Soul Pool, resets to L1, preserves inventory; `claimlevels` post-chargen; +2 skill point bonus per past reincarnation (cap 10) |
| 668 passing tests | 0 failures |

### Not Yet Implemented

| Feature | Notes |
|---|---|
| PvP combat | No player-vs-player support |
| Crafting | No item crafting or modification system |
| Advanced reputation effects | Reputation is tracked/displayed; no content-gating or unique unlock tables yet |

---

## Graphical Client Integration

This section is for developers building a graphical or native client that connects to the Helion Vanta server.

### Server Ports

| Port | Protocol | Purpose |
|------|----------|---------|
| 4000 | TCP (Telnet) | Plain-text MUD client |
| 4001 | HTTP | Evennia web interface (admin, docs) |
| 4002 | WebSocket | Graphical / browser client |

The reference HTML client (`client.html`) connects to **port 4002**.

### WebSocket Message Format

All messages are JSON arrays: `[msgtype, args, kwargs]`

**Sending a command** (client → server):
```json
["text", ["look"], {}]
```

**Session registration** — send one empty frame immediately after `ws.onopen` so Evennia registers the session before the login prompt:
```json
["text", [""], {}]
```

### Server → Client Messages

| `msgtype` | `args` | `kwargs` | Description |
|-----------|--------|----------|-------------|
| `"text"` | `["<html string>"]` | `{}` | Game output (room descriptions, combat, dialogue, etc.) |
| `"prompt"` | `["<html string>"]` | `{}` | Compact stat prompt (same rendering as `"text"`) |
| `"room_update"` | `[]` | See below | Sent on every room entry |
| `"stats_update"` | `[]` | See below | Sent after every combat round, regen tick, and sleep recovery |

#### `room_update` kwargs

```json
{
  "room_key":    "helion_market",
  "display_name": "Helion Market District",
  "area":        "helion",
  "planet":      "Helion Reach",
  "room_type":   "market"
}
```

Use `room_key` as a stable identifier (never changes). `area` groups rooms for the auto-mapper.

#### `stats_update` kwargs

```json
{
  "hp":          72,
  "hp_max":      100,
  "shield":      60,
  "shield_max":  80,
  "stamina":     85,
  "stamina_max": 100,
  "psi":         60,
  "psi_max":     80
}
```

### Text Rendering Pipeline

Game text arrives as HTML strings. Two colour systems are in use and must both be handled:

**1. Evennia markup colours** (`|r`, `|g`, `|y`, etc.)
The server converts markup to `<span class="color-NNN">` before sending. Since a graphical client will not load `webclient.css`, convert these to inline styles using the xterm-256 palette. The reference mapping is `_EVENNIA_CLASS_COLOR` in `client.html:582`.

**2. Raw ANSI escape codes** (`\x1b[NNm`)
Used by `overworld.py` for the terrain map. These arrive as literal escape bytes inside the JSON string. Convert them to styled `<span>` elements using the palette in `client.html:527` (`_ANSI_CSS`). The same palette is duplicated in `oob.js` for the stock Evennia webclient.

Both conversions are implemented as pure functions in `client.html` (`evenniaClassToInline` and `ansiToHtml`) and can be ported directly.

### OOB Plugin (`oob.js`)

The file `helionvanta/server/.static/webclient/js/plugins/oob.js` is loaded by the **stock Evennia webclient** (port 4001). It:
- Silences `room_update` / `stats_update` OOB packets (consumed by custom clients; would otherwise show "Unhandled event" in the stock client)
- Pre-processes raw ANSI codes before `default_out.js` inserts them into the DOM

A native graphical client does **not** need this plugin — implement the two rendering steps directly.

### Auto-Mapper Protocol

The reference client (`client.html`) builds an auto-map from `room_update` packets:

1. On first sight of a `room_key` for an area, assign a grid position based on the direction the player just moved (`pendingDir`).
2. If the player enters a new area or no direction was recorded, place the room below the existing cluster.
3. Draw edges between consecutively visited rooms in the same area.

Direction offsets:
```
n/s/e/w → ±1 on x or y   ne/nw/se/sw → diagonal ±1
u → y−2   d → y+2
```

Grid coordinates are client-side only and not stored on the server.

### What a Graphical Client Needs to Implement

| Feature | Notes |
|---------|-------|
| WebSocket connection to port 4002 | Evennia's websocket interface |
| Session registration frame on connect | `["text", [""], {}]` immediately after open |
| Command sending | `["text", ["<command>"], {}]` |
| Text display with two-pass colour rendering | Evennia class spans + raw ANSI codes |
| `stats_update` handler | Render HP / Shield / Stamina / PSI bars |
| `room_update` handler | Update room name display; optionally feed auto-mapper |
| Input history (↑/↓) | Improves usability; not provided by server |
| Scroll-lock / auto-scroll | Lock when user scrolls up; resume on new output |

The `client.html` file is a complete working reference implementation (~930 lines, no external dependencies beyond Evennia's WebSocket endpoint).
