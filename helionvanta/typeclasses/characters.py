"""
Characters

Characters are (by default) Objects setup to be puppeted by Accounts.
They are what you "see" in game. The Character class in this module
is setup to be the "default" character type created by the default
creation commands.

"""

import datetime
import sys
from pathlib import Path

from evennia.objects.objects import DefaultCharacter

from .objects import ObjectParent


def _ensure_project_root():
    root = str(Path(__file__).resolve().parents[2])
    if root not in sys.path:
        sys.path.insert(0, root)


_ensure_project_root()
from mudgame.contracts import EQUIPMENT_SLOTS, default_equipped as _default_equipped  # noqa: E402
from mudgame.data.constants import LEVEL_XP_TABLE as _LEVEL_XP_TABLE  # noqa: E402

# ---------------------------------------------------------------------------
# Combat-quality adjective helpers
# ---------------------------------------------------------------------------

def _skill_adj(value: int) -> str:
    """Translate a 0–100 skill value to a descriptive word."""
    if value < 10:
        return "poor"
    if value < 20:
        return "weak"
    if value < 35:
        return "fair"
    if value < 50:
        return "solid"
    if value < 65:
        return "strong"
    if value < 80:
        return "excellent"
    return "masterful"


def _focus_adj(focus: int) -> str:
    """Translate Focus stat to a reflexes/awareness quality word."""
    if focus < 20:
        return "poor"
    if focus < 35:
        return "weak"
    if focus < 50:
        return "fair"
    if focus < 70:
        return "solid"
    return "keen"


class Character(ObjectParent, DefaultCharacter):
    """
    The Character just re-implements some of the Object's methods and hooks
    to represent a Character entity in-game.

    Persistent stats stored as db attributes:
      hp, hp_max, stamina, stamina_max, focus, focus_max,
      shield_integrity, shield_max, equipped (dict), xp, level,
      skills (dict), skill_points, created_at (str)
    """

    def at_object_creation(self):
        super().at_object_creation()
        self._init_stats()

    def at_init(self):
        """Ensure stats are set on every load (handles pre-existing characters)."""
        super().at_init()
        if self.db.hp is None:
            self._init_stats()
        # Backfill fields added after initial creation.
        if self.db.level is None:
            self.db.level = 1
        if self.db.skills is None:
            self.db.skills = {"melee": 10, "dodge": 10, "parry": 10,
                              "blades": 5, "bludgeons": 5, "polearms": 5, "ranged": 5}
        else:
            # Backfill weapon-type skills for existing characters.
            skills = self.db.skills
            for wtype in ("blades", "bludgeons", "polearms", "ranged"):
                if wtype not in skills:
                    skills[wtype] = 5
            self.db.skills = skills
        if self.db.skill_points is None:
            self.db.skill_points = 0
        # Backfill creation date for characters created before this field existed.
        if self.db.created_at is None:
            self.db.created_at = "Unknown"
        # Backfill camping skill for characters created before it was added.
        skills = self.db.skills or {}
        if "camping" not in skills:
            skills["camping"] = 0
            self.db.skills = skills
        # Backfill alertness skill for characters created before it was added.
        if "alertness" not in skills:
            skills["alertness"] = 0
            self.db.skills = skills
        # Migrate old equipped_weapon / equipped_module to the new slot dict.
        if self.db.equipped is None:
            old_weapon = self.db.equipped_weapon or "training_vibroblade"
            old_module = self.db.equipped_module if self.db.equipped_module else None
            equipped = _default_equipped()
            equipped["main_hand"] = old_weapon
            equipped["utility"] = old_module
            self.db.equipped = equipped
        # Backfill attribute system for characters created before it was added.
        if self.db.attrs is None:
            self.db.attrs = {"str": 10, "dex": 10, "con": 10, "mind": 10,
                             "cha": 10, "per": 10, "luck": 10}
        else:
            attrs = self.db.attrs
            for k in ("str", "dex", "con", "mind", "cha", "per", "luck"):
                if k not in attrs:
                    attrs[k] = 10
            self.db.attrs = attrs
        if self.db.attr_points is None:
            self.db.attr_points = 0
        if self.db.psi_max is None:
            mind = (self.db.attrs or {}).get("mind", 10)
            self.db.psi_max = 10 + mind * 5
        if self.db.psi is None:
            self.db.psi = self.db.psi_max or 60
        if self.db.reputation is None:
            self.db.reputation = {"helion_colony": 0, "vanta_clans": 0}
        # Backfill guild system fields — guarded so existing data is preserved.
        if self.db.free_levels is None:
            self.db.free_levels = 0
        if self.db.guild_levels is None:
            self.db.guild_levels = {}
        if self.db.guild_skills is None:
            self.db.guild_skills = {}
        if self.db.guild_passives_applied is None:
            self.db.guild_passives_applied = {}
        if self.db.psi_ward is None:
            self.db.psi_ward = 0
        # Backfill reincarnation system fields.
        if self.db.soul_xp is None:
            self.db.soul_xp = 0
        if self.db.reincarnations is None:
            self.db.reincarnations = 0
        # Backfill chargen fields for characters created before the system existed.
        # None means the field was never set → pre-existing character → skip chargen.
        if self.db.chargen_complete is None:
            self.db.chargen_complete = True
        if self.db.background is None and self.db.chargen_complete:
            pass  # Pre-existing characters simply have no background set.
        # Backfill camping/rest fields added after initial release.
        if self.db.camping_cooldown_until is None:
            self.db.camping_cooldown_until = 0
        if self.db.sleeping_pending is None:
            self.db.sleeping_pending = False
        # Repair pool maxima corrupted by the level-up bug (None → 0 + gain·n).
        # stat_maxima_for_level() is the canonical formula — characters whose
        # stored maxima are below the expected value are healed on login /
        # server reload.
        level = self.db.level or 1
        attrs = self.db.attrs or {}
        from mudgame.systems.leveling import stat_maxima_for_level
        correct = stat_maxima_for_level(level, attrs)
        if (self.db.hp_max or 0) < correct["hp_max"]:
            self.db.hp_max = correct["hp_max"]
            self.db.hp = self.db.hp_max
        if (self.db.stamina_max or 0) < correct["stamina_max"]:
            self.db.stamina_max = correct["stamina_max"]
            self.db.stamina = self.db.stamina_max
        if (self.db.shield_max or 0) < correct["shield_max"]:
            self.db.shield_max = correct["shield_max"]
            self.db.shield_integrity = self.db.shield_max
        if (self.db.focus_max or 0) < correct["focus_max"]:
            self.db.focus_max = correct["focus_max"]
            self.db.focus = self.db.focus_max

    def _init_stats(self):
        self.db.hp = 100
        self.db.hp_max = 100
        self.db.stamina = 100
        self.db.stamina_max = 100
        self.db.focus = 50
        self.db.focus_max = 50
        self.db.shield_integrity = 100
        self.db.shield_max = 100
        self.db.equipped = _default_equipped()
        self.db.xp = 0
        self.db.level = 1
        self.db.skills = {"melee": 10, "dodge": 10, "parry": 10,
                          "blades": 5, "bludgeons": 5, "polearms": 5,
                          "ranged": 5, "camping": 0, "alertness": 0}
        self.db.skill_points = 0
        self.db.created_at = datetime.datetime.now().strftime("%b %d, %Y")
        # Attribute system and PSI pool.
        self.db.attrs = {"str": 10, "dex": 10, "con": 10, "mind": 10,
                         "cha": 10, "per": 10, "luck": 10}
        self.db.attr_points = 0
        self.db.psi = 60        # 10 + MIND(10) * 5
        self.db.psi_max = 60
        self.db.reputation = {"helion_colony": 0, "vanta_clans": 0}
        # Chargen tracking — False means this character still needs to run chargen.
        self.db.chargen_complete = False
        self.db.background = None
        # Rest/camping state.
        self.db.camping_cooldown_until = 0
        self.db.sleeping_pending = False

    def get_stats(self):
        """Return a CharacterStats dataclass reflecting current db values."""
        _ensure_project_root()
        from mudgame.contracts import CharacterStats

        equipped = self.db.equipped or _default_equipped()
        skills = self.db.skills or {"melee": 10, "dodge": 10, "parry": 10}
        attrs = self.db.attrs or {}
        return CharacterStats(
            hp=self.db.hp or 100,
            stamina=self.db.stamina or 100,
            focus=self.db.focus or 50,
            shield_integrity=self.db.shield_integrity or 100,
            equipped_weapon=equipped.get("main_hand") or "training_vibroblade",
            weapon_damage_bonus=0,  # resolved at runtime by mud_commands from item catalog
            skill_melee=skills.get("melee", 10),
            skill_dodge=skills.get("dodge", 10),
            skill_parry=skills.get("parry", 10),
            str_attr=attrs.get("str", 10),
            dex_attr=attrs.get("dex", 10),
            con_attr=attrs.get("con", 10),
            mind_attr=attrs.get("mind", 10),
            cha_attr=attrs.get("cha", 10),
            per_attr=attrs.get("per", 10),
            luck_attr=attrs.get("luck", 10),
        )

    def apply_stats(self, stats):
        """Write a CharacterStats instance back to db attributes."""
        self.db.hp = stats.hp
        self.db.stamina = stats.stamina
        self.db.focus = stats.focus
        self.db.shield_integrity = stats.shield_integrity

    def at_post_puppet(self, **kwargs):
        """Start the regen ticker as soon as a player puppets this character.

        This fires on every login, reconnect, and server reload — so regen
        is always running for any online player character without relying on
        individual commands to call _ensure_regen_ticker().

        Also triggers the chargen menu for brand-new characters that have not
        yet selected a background (chargen_complete == False).
        """
        super().at_post_puppet(**kwargs)
        try:
            from helionvanta.commands.mud_commands import _ensure_regen_ticker
            _ensure_regen_ticker(self)
        except Exception:
            pass
        # Launch character creation for new characters.
        if not self.db.chargen_complete:
            try:
                from world.chargen import start_chargen
                start_chargen(self)
            except Exception as exc:
                self.msg(f"|rCharacter creation error: {exc}|n  Contact an admin.")
                # Fail-safe: don't lock the player out permanently.
                self.db.chargen_complete = True
        # Re-attach OverworldCmdSet if reconnecting or reloading while inside
        # an OverworldRoom.  The cmdset is non-persistent (stripped on
        # disconnect / server reload) but the character's location is
        # preserved, so without this the overworld movement commands are
        # unavailable until the character physically moves into the room again.
        try:
            from helionvanta.typeclasses.overworld_room import OverworldRoom
            from commands.overworld_commands import OverworldCmdSet
            if isinstance(self.location, OverworldRoom):
                self.cmdset.add(OverworldCmdSet, persistent=False)
        except Exception:
            pass

    def at_pre_cmd(self, cmd):
        """Block most commands while sleeping/resting.

        Returns False to cancel command execution; Evennia will not run func().
        """
        if not self.db.sleeping:
            return True
        allowed = {"wake", "stand", "getup", "rise", "look", "la", "l", "help"}
        key = getattr(cmd, "key", "").lower()
        if key in allowed:
            return True
        self.msg("|yYou can't do that while resting. Type |wwake|y to get up early.|n")
        return False

    def at_after_move(self, source_location, move_type="move", **kwargs):
        """Check for ambush-capable mobs when entering a new room.

        Calls _check_room_ambush from combat_commands which rolls the
        character's alertness skill to either warn the player or allow the
        mob a free opening strike before combat begins.
        """
        try:
            from commands.combat_commands import _check_room_ambush
            _check_room_ambush(self)
        except Exception:
            pass

    @property
    def is_alive(self):
        return (self.db.hp or 0) > 0

    def status_string(self):
        hp        = self.db.hp or 0
        hp_max    = self.db.hp_max or 100
        stam      = self.db.stamina or 0
        stam_max  = self.db.stamina_max or 100
        shield    = self.db.shield_integrity or 0
        shield_max = self.db.shield_max or 100
        focus     = self.db.focus or 0
        psi       = self.db.psi or 0
        psi_max   = self.db.psi_max or 60
        xp        = self.db.xp or 0
        level     = self.db.level or 1
        skills    = self.db.skills or {}
        sp        = self.db.skill_points or 0
        created   = self.db.created_at or "Unknown"
        attrs     = self.db.attrs or {}
        ap        = self.db.attr_points or 0

        ledger  = self.db.ledger or {}
        credits = ledger.get("credits", 0)

        free_levels   = self.db.free_levels or 0
        guild_levels  = self.db.guild_levels or {}
        guild_skills  = self.db.guild_skills or {}

        # Background display (may be None for pre-chargen-system characters).
        bg_key = self.db.background
        bg_display = ""
        if bg_key:
            try:
                from mudgame.data.world_data import BACKGROUND_DATA
                bg_display = BACKGROUND_DATA.get(bg_key, {}).get("name", "")
            except Exception:
                pass

        # XP thresholds — single source of truth in mudgame/data/constants.py.
        next_xp = _LEVEL_XP_TABLE.get(level + 1)
        xp_str  = f"{xp} / {next_xp}" if next_xp else f"{xp} (level cap)"

        sp_str  = f"  |y[{sp} sp]|n" if sp > 0 else ""
        ap_str  = f"  |y[{ap} ap]|n" if ap > 0 else ""
        fl_str  = f"  |c[{free_levels} guild token(s)]|n" if free_levels > 0 else ""

        # --- Regen rates (out-of-combat baseline per tick) ---
        con  = attrs.get("con", 10)
        mind = attrs.get("mind", 10)
        dex  = attrs.get("dex",  10)
        hp_regen      = 1 + max(0, (con  - 10) // 5)
        stamina_regen = 3 + max(0, (dex  - 10) // 4)
        shield_regen  = 1 + max(0, (mind - 10) // 5)
        psi_regen     = 2 + max(0, (mind - 10) // 5)

        # --- Primary attributes ---
        a_str  = attrs.get("str",  10)
        a_dex  = attrs.get("dex",  10)
        a_con  = attrs.get("con",  10)
        a_mind = attrs.get("mind", 10)
        a_cha  = attrs.get("cha",  10)
        a_per  = attrs.get("per",  10)
        a_luck = attrs.get("luck", 10)

        # --- Combat quality (adjectives) ---
        sk_m  = skills.get("melee", 10)
        sk_d  = skills.get("dodge", 10)
        sk_p  = skills.get("parry", 10)
        sk_bl = skills.get("blades", 5)
        sk_bu = skills.get("bludgeons", 5)
        sk_po = skills.get("polearms", 5)
        sk_ra = skills.get("ranged", 5)
        sk_ca = skills.get("camping", 0)

        melee_adj  = _skill_adj(sk_m)
        dodge_adj  = _skill_adj(sk_d)
        parry_adj  = _skill_adj(sk_p)
        reflex_adj = _focus_adj(focus)

        # --- Layout helpers -------------------------------------------------
        # Inline color helper (mirrors _val_color in mud_commands.py).
        def _vc(cur, mx):
            pct = cur / mx if mx > 0 else 0
            if pct >= 0.6:
                return "|g"
            if pct >= 0.3:
                return "|y"
            return "|r"

        # Pool block: [ colored_cur / max ] — 14 visual chars fixed width.
        def _pool(cur, mx):
            return f"[ {_vc(cur, mx)}{cur:>4}|n /{mx:>4} ]"

        # Regen bracket.
        def _regen(rate):
            return f"|y[+{rate}/t]|n"

        # Attribute bracket.
        def _attr(val):
            return f"|c[{val:>2}]|n"

        # BatMUD-style cyan border (52 visual chars: "=-=+" × 13).
        border = "|c" + "=-=+" * 13 + "|n"

        # Resource rows (indent 2, label 7, pool 14, space, regen 6, attrs).
        r1 = f"  {'HP':<7} {_pool(hp,     hp_max)}    {_regen(hp_regen)}  STR{_attr(a_str)}  DEX{_attr(a_dex)}"
        r2 = f"  {'Shield':<7} {_pool(shield, shield_max)} {_regen(shield_regen)}  CON{_attr(a_con)} MIND{_attr(a_mind)}"
        r3 = f"  {'Stamina':<7} {_pool(stam,   stam_max)}  {_regen(stamina_regen)}  CHA{_attr(a_cha)}  PER{_attr(a_per)}"
        r4 = f"  {'PSI':<7} {_pool(psi,    psi_max)}    {_regen(psi_regen)}  LUCK{_attr(a_luck)}"

        return (
            f"{border}\n"
            f"  |w{self.name}|n   Level {level}   Created {created}\n"
            + (f"  Background: |c{bg_display}|n\n" if bg_display else "")
            + f"{border}\n"
            f"{r1}\n"
            f"{r2}\n"
            f"{r3}\n"
            f"{r4}\n"
            f"  XP: {xp_str}   Credits: {credits}{sp_str}{ap_str}{fl_str}\n"
            f"\n"
            f"  |wCombat Quality|n\n"
            f"  Melee:   |c{melee_adj:<12}|n  Dodge:   |c{dodge_adj}|n\n"
            f"  Parry:   |c{parry_adj:<12}|n  Reflexes: |c{reflex_adj}|n\n"
            f"\n"
            f"  |wWeapon Specialization|n\n"
            f"  Blades |c{sk_bl}|n  Bludgeons |c{sk_bu}|n  Polearms |c{sk_po}|n  Ranged |c{sk_ra}|n\n"
            f"  |wSurvival|n  Camping |c{sk_ca}|n\n"
            f"{self._guild_status_block(guild_levels, guild_skills)}"
            f"{border}\n"
            f"  Type |weq|n for gear · |wskills|n for attrs · |wsleep|n to rest"
        )

    def _guild_status_block(self, guild_levels: dict, guild_skills: dict) -> str:
        """Return a guild membership block for status_string, or empty string if no guilds."""
        if not guild_levels:
            return ""
        _ensure_project_root()
        from mudgame.data.world_data import WORLD_DATA
        guilds = WORLD_DATA.get("guilds", {})
        lines = ["\n  |wGuild Membership|n"]
        for guild_key, rank in guild_levels.items():
            if rank <= 0:
                continue
            guild_data = guilds.get(guild_key, {})
            gname = guild_data.get("name", guild_key)
            lines.append(f"  {gname}: Rank {rank}/{guild_data.get('max_rank', 10)}")
            p_skills = guild_skills.get(guild_key, {})
            for sk_key, sk_data in guild_data.get("skills", {}).items():
                pct = p_skills.get(sk_key, 0)
                if pct > 0:
                    lines.append(f"    {sk_data['name']}: {pct}%")
        return "\n".join(lines) + "\n"
