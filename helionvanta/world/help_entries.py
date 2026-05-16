"""
Game-specific file-based help entries for Helion-Vanta.

Loaded by Evennia via FILE_HELP_ENTRY_MODULES = ["world.help_entries"] in settings.py.
"""

HELP_ENTRY_DICTS = [
    # ------------------------------------------------------------------
    {
        "key": "combat",
        "aliases": ["fighting", "battle"],
        "category": "Combat",
        "text": """
Combat in Helion-Vanta is automatic and tick-based.

Usage:
  attack <target>     Start auto-combat against a mob.
  attack stop         Disengage from combat.

Combat resolves every 3 seconds. Each round you and your target
exchange attacks. Shields absorb most damage until depleted; once
broken, every hit deals HP damage directly.

Hit chance is based on your Melee skill + Stamina + weapon-type skill + LUCK bonus.
Defense is passive: Avoid, Dodge, and Parry trigger automatically
based on your skills. Higher Focus (boosted by MIND) raises defensive thresholds.

# subtopics

## Actions

Each round your character picks from: attack, heavy, feint.
  attack   Standard strike (14 + weapon bonus base damage).
  heavy    Powerful swing (24 + weapon bonus, more stamina).
  feint    Drains the target's Focus even on a miss.

Parried hits deal ~50% damage. Dodged/avoided attacks deal 0.

## Criticals

Any hit has an 18% base chance to deal +8 bonus damage (player),
or 12% to deal +6 (mobs). Criticals are marked [CRITICAL HIT!].
LUCK raises player crit chance: +1% per LUCK above 10 (e.g. LUCK 15 = 23%).

## Defeat

If your HP reaches 0 you wake at helion_gate with reduced stats.
""",
    },
    # ------------------------------------------------------------------
    {
        "key": "techniques",
        "aliases": ["technique", "slash", "concussion", "lunge"],
        "category": "Combat",
        "text": """
Techniques are special combat moves you can queue during a fight.

Usage:
  slash          Queue Slash  (1-round wind-up)
  concussion     Queue Concussion Strike  (2-round wind-up)
  lunge          Queue Lunge  (1-round wind-up)

The technique fires in place of your normal main-hand attack when
its wind-up completes. Only one technique can be queued at a time.
You must be in active combat.

# subtopics

## Slash

Wind-up: 1 round. On hit: applies Bleeding (3 rounds, 4 HP/tick).
Good for sustained pressure — bleed ticks every round for free damage.

## Concussion Strike

Wind-up: 2 rounds. On hit: Stuns the target for 1 round.
A stunned enemy skips its next action entirely. Worth the wind-up
against high-defense mobs.

## Lunge

Wind-up: 1 round. On hit: shield-pierce (half damage bypasses shield),
applies Weakened (2 rounds, -10 to dodge and parry).
Best opener against heavily shielded enemies like the Vault Guardian.
""",
    },
    # ------------------------------------------------------------------
    {
        "key": "skills",
        "aliases": ["skill", "training"],
        "category": "Combat",
        "text": """
Skills improve through use and can be further trained with skill points.

Usage:
  skills             Show your current skill levels and available points.
  train <skill>      Spend 1 skill point to raise a skill by 1.

Combat skills (auto-grow by use up to 60):
  melee      Hit chance and damage potential.
  dodge      Passive chance to fully evade incoming attacks.
  parry      Passive chance to partially block (50% damage through).

Weapon-type skills (grow when landing hits with that type, up to 60):
  blades     Improves hit% with blades; note: Glass Stalkers are weak to blades.
  bludgeons  Landed hits deal bonus shield damage; Vault Guardian is weak to bludgeons.
  polearms   Bonus first-round damage before an enemy closes distance.
  ranged     Improves hit% with ranged weapons.

Soft cap: skills auto-grow to 60 through use. Spending skill points
(earned at each level-up) lets you push past 60.

Talk to Blademaster Thorne in the Nocturne Bazaar to review your skills.

# subtopics

## Attribute Effects

Primary attributes wire into skills each combat round:

  STR  → +1 weapon damage per 3 STR above 10; +1 parry per 5 STR above 10.
  DEX  → +1 melee per 5 DEX above 10; +1 dodge per 4 DEX above 10.
  MIND → +2 effective focus per MIND above 10 (focus boosts passive defense).
  PER  → +1 ranged melee per 3 PER above 10 (ranged weapons only).
  LUCK → +1 hit% per 5 LUCK above 10; +1 avoid at LUCK 20;
         +1% crit chance per LUCK above 10 on top of the 18% base.

All bonuses use max(0, stat-10) so the base value of 10 never penalises.

## Camping

  sleep / rest / camp    Begin a rest cycle to recover HP, Stamina, and Shield.
  wake / stand           Rise early for half recovery.

Resting has a 2-second scan phase before sleep begins. During the scan
you can type 'wake' to cancel without any penalty.

Recovery formula (full rest):
  HP      = 20 + camping//2 + max(0, (CON-10)//2)
  Stamina = 30 + camping//2
  Shield  = 15 + camping//2

After a full rest a cooldown applies before you can rest again:
  Cooldown = max(30s, 60s - (CON-10)*3)

CON 10 (base): 60s cooldown, +0 bonus HP.
CON 12:        54s cooldown, +1 bonus HP.
CON 14:        48s cooldown, +2 bonus HP.
CON 20:        30s cooldown (minimum), +5 bonus HP.

The camping skill improves on every completed (non-partial) rest cycle.
""",
    },
    # ------------------------------------------------------------------
    {
        "key": "equipment",
        "aliases": ["gear", "slots", "equip"],
        "category": "General",
        "text": """
Equipment occupies one of seven slots on your character.

Slots: head, torso, legs, feet, main_hand, off_hand, utility

Usage:
  eq                         Show all equipped slots.
  equip <item>               Equip an item from your inventory.
  unequip <slot|item>        Remove an item from a slot.
  inventory                  List items you are carrying.

# subtopics

## Combat Styles

Dual wield   — both hands carry weapons; off-hand attacks at -15% hit.
Sword+shield — off-hand holds a shield; boosts parry window by +15%.
Two-handed   — main-hand is two-handed; +6 bonus damage, no off-hand.
Unarmed      — empty off-hand attacks at a notable damage penalty.

## Armor

Armor pieces (head, torso, legs, feet) raise your HP max when equipped.
Colony armor: modest HP bonus, light physical reduction.
Vanta Reave armor: higher HP and physical damage reduction.

## Shields / Utility

Shield batteries are field amplifiers that couple with your natural
biofield to extend its effective capacity. They slot into utility or
off_hand and raise your shield max. Holding one in off_hand grants +15 parry.
""",
    },
    # ------------------------------------------------------------------
    {
        "key": "travel",
        "aliases": ["shuttle", "board", "dock"],
        "category": "General",
        "text": """
Travel between Helion Reach and Vanta IX via the Shardline Shuttle.

Usage:
  board              Auto-board from a shuttle dock (picks the opposite port).
  dock               Same as 'board'.
  travel <helion|vanta>  Choose destination explicitly.

You must be at a shuttle dock (helion_shuttle_dock or vanta_shuttle_dock)
to board. From inside the shuttle you can use 'travel <destination>'.

The shuttle has four rooms to explore while in transit:
  shuttle_airlock, shuttle_cargo, shuttle_lounge, shuttle_observation.

Quest note: the second contract requires boarding at Helion Dock and
arriving at Vanta IX — these are tracked automatically.
""",
    },
    # ------------------------------------------------------------------
    {
        "key": "quests",
        "aliases": ["quest", "contract", "contracts"],
        "category": "General",
        "text": """
Quests are called contracts and are managed through the quest command.

Usage:
  quest                      Browse available contracts.
  quest progress             View active contract objectives.
  quest accept <key|alias>   Accept a contract (must be at start location).
  quest turnin <key|alias>   Complete and turn in a contract.

Aliases: intro (helion_intro_colony_defense), vanta (vanta_expedition_artifact_recovery)

# subtopics

## Helion Introduction: Colony Defense

Start at: helion_gate (talk to Marshal Kaine — she auto-assigns it).
Objectives:
  1. Defeat 2 Warren Raiders in Cinder Warrens.
  2. Return and talk to Marshal Kaine.
Rewards: 150 XP, 50 credits, Recruit Field Brace.

## Vanta Expedition: Artifact Recovery

Requires completing Colony Defense first.
Start at: helion_shuttle_dock (or talk to Marshal Kaine).
Objectives:
  1. Board shuttle at Helion Dock.
  2. Arrive at Vanta IX.
  3. Defeat 3 Glass Stalkers in Glass Dunes Ruins.
  4. Recover the relic — defeat the Vault Guardian in the Relic Vault.
  5. Return to Helion and talk to Marshal Kaine.
Rewards: 400 XP, 200 credits, Veteran Field Brace.
""",
    },
    # ------------------------------------------------------------------
    {
        "key": "economy",
        "aliases": ["credits", "shop", "buy", "vendor"],
        "category": "General",
        "text": """
Credits are the currency of Helion-Vanta. Earn them from quest rewards.

Usage:
  shop               Browse the local vendor's wares.
  buy <item>         Purchase an item (added to inventory).
  status             Shows your current credit balance.

Vendors:
  Quartermaster Vex  (helion_market)  — Colony-grade gear and armor.
  Broker Sorn        (vanta_customs)  — Vanta-grade weapons and armor.

Each item can only be purchased once per character. Use
'equip <item>' after buying to put it on.
""",
    },
    # ------------------------------------------------------------------
    {
        "key": "status effects",
        "aliases": ["bleed", "stun", "weakened", "status effect"],
        "category": "Combat",
        "text": """
Status effects last for a number of combat rounds and tick each round.

Bleed    — 4 HP drained per tick for N rounds. Applied by Slash and
           the Glass Stalker's natural attacks.
Stun     — Target skips its next action entirely. Applied by Concussion.
Weakened — -10 penalty to dodge and parry skills for N rounds.
           Applied by Lunge and the Vault Guardian's on-hit.

Effects from both player techniques and mob on-hit abilities appear
in the combat log each round. Multiple effects can be active at once;
'apply_effect' keeps whichever duration is longer (no double-stacking).
""",
    },
    # ------------------------------------------------------------------
    {
        "key": "background",
        "aliases": ["lore", "setting", "world"],
        "category": "World",
        "text": """
The Helion System was colonized eighty years ago by the first wave of
expansion ships from the inner worlds. What began as a mining outpost
is now a self-sustaining colony — Helion Reach — built around a central
spaceport and defended by a standing colonial marshal corps.

Helion Station is the last major settlement before uncharted space.
Beyond it, the Shardline route leads to Vanta IX.

--- Vanta IX ---

Vanta IX is an ancient world. Its surface is partly covered by the
Glass Dunes — vast fields of fused silicate formed by processes no
geologist has fully explained. Beneath the dunes lie ruins of unknown
origin: architecture that predates every known civilization, including
anything the colonists brought with them.

The Vanta Clans are the semi-nomadic human groups who arrived on Vanta IX
before formal colonial expansion. They are not colonial subjects; they
have Clan law, Clan territory, and Clan weapons. Relations with Helion are
transactional rather than political.

--- The Ruins ---

Whatever built the ruins on Vanta IX is gone. The Clans have studied them
for generations and reached no consensus on what the builders were, how
long ago they were here, or why they left. Certain ruins are sealed by
field-emitter locks that require physical defeat of automated sentinels
to open. The colony calls these 'vault guardians.' The Clans call them
something that does not translate well.

--- Why Blades ---

Energy weapons are manufactured goods. Out on the frontier, power cells
are expensive, supply chains are unreliable, and heat buildup in confined
industrial spaces (like the Cinder Warrens) degrades charge packs fast.
A blade does not run out of charge. The melee culture on Helion is not
tradition — it is pragmatics. The Vanta Clans arrived at the same
conclusion independently.

--- Navigation ---

  map             Local compass map of adjacent rooms.
  look            Examine current room and exits.
  scan            Detect threats in the area.

See also: combat, skills, equipment, quests, travel
""",
    },
    # ------------------------------------------------------------------
    {
        "key": "guilds",
        "aliases": ["guild", "covenant", "weavers"],
        "category": "General",
        "text": """
Two factions operate in the Helion system. You may belong to only one
guild at a time. Leaving refunds all spent tokens (use |wleaveguild|n).

  Iron Covenant   — Hall at iron_covenant_hall, Helion Reach
  PSI Weavers     — Sanctum at psi_weavers_sanctum, Vanta IX

Usage:
  guilds                  Show both guilds, your rank, and skill training.
  join                    Join the guild at your current hall (costs 1 token).
  advance                 Spend 1 token to raise your rank (at guild hall).
  train <skill>           Spend XP to improve a guild skill.
  leaveguild              Resign and recover all spent tokens.

# subtopics

## Tokens and Rank Cap

Rank cap: 20 per guild. Each rank costs 1 free level token.
Tokens are earned by leveling past the main cap of 10 — one token per
level gained from 11 through 40, giving 30 tokens total.

  Maxing one guild to rank 20 costs 20 tokens.
  You cannot max both guilds (20+20=40 > 30 available).
  Typical split: one guild rank 20, the other rank 10 (30 total).

## Passive Bonuses per Rank

Each rank advance permanently applies:

  Iron Covenant  — +1 STR, +1 CON, +5 HP max
  PSI Weavers    — +1 MIND, +10 PSI max

## Iron Covenant Skills

Ranks  1-10 (passive): iron_stance (+phys_reduction), throw_weight (+weapon_damage),
                        find_weakness (+crit_chance), enhanced_criticals (+crit_damage)
Rank   5    (active):  sunder_strike — 1.5× weapon dmg + 10 flat, ignores parry.
                       Queue with |wsunder|n during combat.
Ranks 11-20 (passive): iron_will (+stamina_max), bulwark (+phys_reduction),
                        battle_mastery (+crit_chance and +crit_damage)
Rank  15    (active):  warlord_strike — 2.0× weapon dmg + 20 flat, ignores parry
                       and armor. Queue with |wwarlord|n during combat.

## PSI Weavers Skills

Ranks  1-10 (passive): focused_channel (+psi_heal_bonus)
Rank   1    (active):  resonance_shield (psi ward) — 1-round PSI barrier.
Rank   3    (active):  psi_bolt (psi bolt) — stronger PSI blast.
Rank   6    (active):  mind_shatter (psi shatter) — massive burst + stun.
Ranks 11-20 (passive): deep_resonance (+psi_max), psi_surge (+psi_heal_bonus),
                        mind_fortress (+phys_reduction)
Rank  13    (active):  void_lance (psi lance) — 30+8/MIND direct HP damage,
                       bypasses shields. Use |wpsi lance|n during combat.
""",
    },
    # ------------------------------------------------------------------
    {
        "key": "psi",
        "aliases": ["psionics", "psi ward", "resonance"],
        "category": "Combat",
        "text": """
PSI is the psionics resource, generated by MIND and used for special
abilities via the PSI Weavers guild.

Your PSI max = 10 + (MIND × 5). At MIND 10, PSI max is 60.
PSI regenerates out of combat: 2/tick base, +1 per 5 MIND above 10.
Full PSI restores on a completed rest cycle (scaled by MIND).

Usage:
  psi ward        Activate a PSI barrier that absorbs the next incoming
                  HP damage. Costs PSI. Ward is consumed on first hit.
  psi heal        Channel PSI into immediate HP recovery.
  psi strike      Channel PSI into a resonance burst attack.

# subtopics

## PSI Ward

PSI Ward absorbs incoming HP damage completely for one hit. The ward
dissipates after each combat round whether triggered or not — it must
be re-cast each round. Weavers with the psi_ward guild skill have a
larger ward pool.

## Sleep and PSI

A full rest cycle restores PSI using the formula:
  PSI gain = 20 + max(0, (MIND - 10) * 4)

Partial rest (early wake) gives half this amount.

## MIND and PSI

MIND raises PSI max, PSI regen rate, psi skill effectiveness, and
the effective focus stat used in passive defense calculations.
At MIND 10 (base): PSI max 60, regen 2/tick.
At MIND 15:        PSI max 85, regen 3/tick.
At MIND 20:        PSI max 110, regen 4/tick.
""",
    },
    # ------------------------------------------------------------------
    {
        "key": "attributes",
        "aliases": ["attrs", "str", "dex", "con", "mind", "cha", "per", "luck", "stats"],
        "category": "General",
        "text": """
Attributes are primary stats that wire into combat, skills, and resources.

  STR   Strength    — melee damage (+1 per 3 STR above 10);
                      parry window (+1 per 5 STR above 10).
  DEX   Dexterity   — hit chance (+1 melee per 5 DEX above 10);
                      evasion (+1 dodge per 4 DEX above 10).
  CON   Constitution— HP regen (+1/tick per 5 CON above 10);
                      rest bonus (+1 HP recovery per 2 CON above 10);
                      rest cooldown reduction (min 30s).
  MIND  Mind        — PSI max (+5 per MIND); PSI regen; focus (+2 per MIND above 10);
                      passive defense; shield regen.
  CHA   Charisma    — NPC reputation thresholds; dialogue options.
  PER   Perception  — ranged hit chance (+1 per 3 PER above 10, ranged only);
                      alertness detection rolls.
  LUCK  Luck        — crit chance (+1% per LUCK above 10 on top of 18% base);
                      hit chance (+1 per 5 LUCK above 10);
                      avoid chance (bonus at LUCK 20).

Usage:
  status / score         Show all attributes and current values.
  attr                   Show attribute menu with point allocation.
  attr spend <attr>      Spend an attribute point to raise a stat.

Attribute points are awarded on level-up:
  Levels 2–5: +1 to all attributes automatically.
  Level 6+:   1 attr_point per level to spend manually.

Guild ranks also award passive attribute bonuses each rank.
""",
    },
    # ------------------------------------------------------------------
    {
        "key": "backgrounds",
        "aliases": ["background", "chargen", "origin", "colonial", "initiate", "exile"],
        "category": "General",
        "text": """
Your background is chosen at character creation and applies permanent
passive bonuses that cannot be changed later.

Available backgrounds:

  Colonial Veteran
    Bonus: +3 CON at start; Camping skill starts at 10.
    Perk:  Rest cycle 5s shorter. You've survived worse than this.

  Clan Initiate
    Bonus: +3 PER at start; Blades skill starts at 15.
    Perk:  +25% damage against Glass Stalkers (glass_stalker).
           Your training was specifically for the Glass Dunes.

  Drifter
    Bonus: +3 LUCK at start; no skill bonus.
    Perk:  +5% base crit chance. You've fought your way out of
           worse odds than these.

  PSI Sensitive
    Bonus: +3 MIND at start; PSI max starts at 90 (not 60).
    Perk:  PSI regen +1/tick out of combat at all times.

Background selection happens once, during your first login session.
""",
    },
    # ------------------------------------------------------------------
    {
        "key": "reincarnation",
        "aliases": ["reincarnate", "rebirth", "soul xp"],
        "category": "General",
        "text": """
Reincarnation lets a maxed character restart at level 1, retaining a
permanent bonus from their accumulated experience.

Condition: character level 10 (main cap), both guild ranks at 20.
Command:   reincarnate  (opens confirmation prompt)

On reincarnation:
  - Level resets to 1; XP resets to 0.
  - Guild ranks reset to 0; guild skills reset.
  - A Soul XP bonus is awarded equal to a fraction of total XP earned.
  - Soul XP is permanent and persists across all reincarnations.
  - A small passive bonus is granted based on total reincarnations.

Each reincarnation cycle progresses faster than the last: Soul XP
bonuses compound and the character retains background perks.

The reincarnation system is intended for players who have exhausted
the content on a single cycle and want persistent progression.

Note: Reincarnation is irreversible. The confirmation prompt gives
you a 30-second window to cancel.
""",
    },
    # ------------------------------------------------------------------
    {
        "key": "overworld",
        "aliases": ["map", "compass", "minimap"],
        "category": "General",
        "text": """
Certain areas in Helion-Vanta use an overworld grid rather than the
standard room-to-room movement. Overworld rooms display a compass map
and use directional movement (n/s/e/w) to traverse a coordinate grid.

The Glass Dunes and sections of Helion Reach are overworld areas.

Usage (in an overworld room):
  n / s / e / w      Move one step in a compass direction.
  map                Display the local compass grid with your position.
  look               Describe the current overworld tile.

Transition rooms (marked [Overworld Entry]) link standard rooms to the
overworld grid. Moving into one changes the active command set to
overworld movement mode; moving back through an exit returns you to
standard room navigation.

Overworld tiles may contain mobs, loot, or points of interest marked on
the compass display. The 'scan' command works in overworld mode to
identify nearby threats.
""",
    },
    # ------------------------------------------------------------------
    {
        "key": "social",
        "aliases": ["roleplay", "emote", "say", "talk"],
        "category": "General",
        "text": """
Social commands let you interact with other players and NPCs.

  say <message>           Speak aloud in your current room.
  emote <action>          Describe an action (e.g. emote nods slowly.)
  talk <npc>              Talk to an NPC — triggers dialogue and quests.
  talk to <npc>           Same as talk (natural language supported).

NPCs with active quests will offer or update contracts when spoken to.
NPCs with the 'information' role provide tactical hints about the area.

# subtopics

## NPC Quest Givers

  Marshal Kaine       helion_gate        — main story contracts (Kaine).
  Scout Kess          helion_warrens_entry — Scrapforge clear contract.
  Blademaster Thorne  vanta_bazaar       — Blade Trial contract + skill report.
  Elder Lyros         vanta_ruins_entry  — Vault Recon + Ancient Record.
  Guildmaster Varro   iron_covenant_hall — Covenant combat contracts.
  Weaver Solen        psi_weavers_sanctum — PSI Weavers field contracts.
  Broker Sorn         vanta_customs      — deep ruin salvage contract.

## Guild Masters

  Guild masters (Varro, Solen) also handle guild rank advancement,
  guild skill training, and provide lore about their respective guilds.
  Use 'guild' commands at their hall/sanctum.
""",
    },
    # ------------------------------------------------------------------
    {
        "key": "alertness",
        "aliases": ["ambush", "detect", "lurk"],
        "category": "Combat",
        "text": """
Alertness is a passive skill that determines whether you detect lurking
enemies when entering a room, or are caught off-guard by an ambush.

Skill range: 0–60 (soft cap; can be pushed beyond 60 with skill points).

Detection formula:
  Detection chance = min(100%, 20% + 1% per alertness point)
  At alertness 0:  20% chance to detect.
  At alertness 40: 60% chance to detect.
  At alertness 80: 100% — always detect (guaranteed after soft cap spend).

Outcome — Detection (pass):
  "You sense movement — a <mob> lurks here."
  You are warned and alertness grows. Use 'ambush' for a first-strike
  advantage.

Outcome — Ambush (fail):
  "<mob> strikes from the shadows before you can react! [AMBUSHED]"
  The mob gets a free opening strike before combat begins. You take
  damage but are not locked out — you can immediately counter with
  'attack <target>'.

Usage:
  ambush <target>    Launch a preemptive first strike against a lurking
                     enemy. The target cannot counter-attack in round 1.
                     Alertness grows on each ambush attempt.

Mobs capable of ambush:
  Glass Stalker, Crystal Wraith, Elder Stalker.

Alertness grows automatically:
  - 25% chance to increase by 1 on each successful detection.
  - 25% chance to increase by 1 on each ambush attempt.
""",
    },
]
