"""Pure guild engine functions — no Evennia imports.

Guild definitions live in ``WORLD_DATA["guilds"]`` (world_data.py).  These
functions accept the guild data dict as an argument so they remain testable
without touching Evennia or the database.

Public API
----------
guild_skill_cap            — max % trainable for a skill at a given rank.
guild_passives_per_rank    — stat deltas granted per rank advance.
apply_guild_stat_passives  — compute new attrs/hp_max/psi_max after one advance.
resolve_guild_join         — validate + apply joining a guild (pure).
resolve_guild_advance      — validate + apply advancing a rank (pure).
"""

from __future__ import annotations

GUILD_MAX_RANK: int = 20


# ---------------------------------------------------------------------------
# Read-only helpers
# ---------------------------------------------------------------------------

def guild_skill_cap(
    guild_key: str,
    skill_key: str,
    rank: int,
    guilds_data: dict,
) -> int:
    """Return the maximum pct trainable for *skill_key* at *rank*.

    ``rank_gates`` is ``{min_rank: max_pct}``.  The cap is the highest
    ``max_pct`` whose ``min_rank`` the player meets or exceeds.
    """
    skill_data = (
        guilds_data.get(guild_key, {})
        .get("skills", {})
        .get(skill_key, {})
    )
    rank_gates = skill_data.get("rank_gates", {})
    cap = 0
    for min_rank, max_pct in rank_gates.items():
        if rank >= int(min_rank):
            cap = max(cap, int(max_pct))
    return cap


def guild_passives_per_rank(guild_key: str, guilds_data: dict) -> dict:
    """Return the stat delta dict granted each time a player advances one rank."""
    return guilds_data.get(guild_key, {}).get("passive_per_rank", {})


# ---------------------------------------------------------------------------
# Stat application (pure)
# ---------------------------------------------------------------------------

def apply_guild_stat_passives(
    *,
    attrs: dict,
    hp_max: int,
    psi_max: int,
    guild_key: str,
    guilds_data: dict,
) -> tuple[dict, int, int]:
    """Compute stat changes from a single rank advance.

    Args:
        attrs:      Character's attribute dict (str, dex, con, mind, cha, …).
        hp_max:     Current maximum HP.
        psi_max:    Current maximum PSI.
        guild_key:  Guild being advanced.
        guilds_data: The full guilds data dict (from WORLD_DATA["guilds"]).

    Returns:
        ``(new_attrs, new_hp_max, new_psi_max)`` — all values adjusted by
        the guild's ``passive_per_rank`` bonuses.  The original dicts are
        not mutated.
    """
    passives = guild_passives_per_rank(guild_key, guilds_data)
    new_attrs = dict(attrs)
    new_hp_max = hp_max
    new_psi_max = psi_max
    for stat, gain in passives.items():
        if stat == "hp_max":
            new_hp_max += gain
        elif stat == "psi_max":
            new_psi_max += gain
        elif stat in new_attrs:
            new_attrs[stat] = new_attrs[stat] + gain
    return new_attrs, new_hp_max, new_psi_max


# ---------------------------------------------------------------------------
# Join / advance resolution (pure)
# ---------------------------------------------------------------------------

def resolve_guild_join(
    *,
    guild_key: str,
    room_key: str,
    guild_levels: dict,
    free_levels: int,
    guild_skills: dict,
    guilds_data: dict,
) -> tuple[bool, str, dict, int, dict]:
    """Validate and apply joining a guild.

    All arguments are plain Python values — no Evennia objects.

    Returns:
        ``(ok, message, new_guild_levels, new_free_levels, new_guild_skills)``

        On failure the existing dicts are returned unchanged so the caller
        can unconditionally write them back to ``caller.db``.
    """
    guild_data = guilds_data.get(guild_key)
    if not guild_data:
        return False, f"Unknown guild '{guild_key}'.", guild_levels, free_levels, guild_skills

    gname = guild_data["name"]

    if guild_data.get("hall_room") != room_key:
        return (
            False,
            f"|yYou must be at the {gname} hall to join.|n",
            guild_levels, free_levels, guild_skills,
        )

    if guild_levels.get(guild_key, 0) > 0:
        return (
            False,
            f"|yYou are already a member of the {gname}.|n",
            guild_levels, free_levels, guild_skills,
        )

    for gk, rank in guild_levels.items():
        if rank > 0 and gk != guild_key:
            other = guilds_data.get(gk, {}).get("name", gk)
            return (
                False,
                f"|yYou are already a member of the {other}. "
                f"You may only belong to one guild.|n",
                guild_levels, free_levels, guild_skills,
            )

    if free_levels < 1:
        return (
            False,
            "|yJoining a guild costs 1 free level token. "
            "Earn tokens by leveling past level 10.|n",
            guild_levels, free_levels, guild_skills,
        )

    new_guild_levels = {**guild_levels, guild_key: 1}
    new_free_levels = free_levels - 1
    new_guild_skills = dict(guild_skills)
    if guild_key not in new_guild_skills:
        new_guild_skills[guild_key] = {
            sk: 0 for sk in guild_data.get("skills", {})
        }

    passives = guild_passives_per_rank(guild_key, guilds_data)
    p_str = ", ".join(f"+{v} {k}" for k, v in passives.items())
    msg = (
        f"|g*** You have joined the {gname} at Rank 1! ***|n\n"
        f"  Passive bonus: {p_str}\n"
        f"  Use |wguilds|n to see available skills and |wtrain <skill>|n to train them."
    )
    return True, msg, new_guild_levels, new_free_levels, new_guild_skills


def resolve_guild_advance(
    *,
    guild_key: str,
    room_key: str,
    guild_levels: dict,
    free_levels: int,
    guilds_data: dict,
) -> tuple[bool, str, dict, int]:
    """Validate and apply advancing a guild rank.

    Returns:
        ``(ok, message, new_guild_levels, new_free_levels)``

        On failure the existing dicts are returned unchanged.
    """
    guild_data = guilds_data.get(guild_key)
    if not guild_data:
        return False, f"Unknown guild '{guild_key}'.", guild_levels, free_levels

    gname = guild_data["name"]
    max_rank = guild_data.get("max_rank", GUILD_MAX_RANK)

    if guild_data.get("hall_room") != room_key:
        return (
            False,
            "|yYou must be at your guild hall to advance.|n",
            guild_levels, free_levels,
        )

    rank = guild_levels.get(guild_key, 0)
    if rank <= 0:
        return (
            False,
            f"|yYou have not joined the {gname} yet. Use |wjoin|n first.|n",
            guild_levels, free_levels,
        )

    if rank >= max_rank:
        return (
            False,
            f"|yYou are already at maximum guild rank ({max_rank}).|n",
            guild_levels, free_levels,
        )

    if free_levels < 1:
        return (
            False,
            "|yAdvancing guild rank costs 1 free level token. "
            "Earn more by leveling past 10.|n",
            guild_levels, free_levels,
        )

    new_rank = rank + 1
    new_guild_levels = {**guild_levels, guild_key: new_rank}
    new_free_levels = free_levels - 1

    passives = guild_passives_per_rank(guild_key, guilds_data)
    p_str = ", ".join(f"+{v} {k}" for k, v in passives.items())
    msg = (
        f"|g*** {gname} — Rank {new_rank}! ***|n\n"
        f"  Passive bonus: {p_str}\n"
        f"  New training caps unlocked. Use |wguilds|n to review skills."
    )
    return True, msg, new_guild_levels, new_free_levels
