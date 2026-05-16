"""Inventory, equipment, shop, skills, and technique commands."""

from __future__ import annotations

from evennia import Command

from commands.cmd_utils import (
    _ensure_project_root_on_path,
    _pretty_name,
    _get_item_data,
    _get_or_init_ledger,
    _cha_adjusted_buy_price,
    _cha_adjusted_sell_price,
    _get_background_perks,
    _guild_skill_cap,
    _load_world_data,
    EQUIPMENT_SLOTS,
    _default_equipped,
    _SKILL_SOFT_CAP,
)


def _find_vendor_in_room(caller) -> object | None:
    """Return the first vendor NPC in the caller's room, or None."""
    if not caller.location:
        return None
    for obj in caller.location.contents:
        if obj.db.actor_type == "npc" and obj.db.role == "vendor":
            return obj
    return None


class CmdInventory(Command):
    """Show your inventory and currently equipped items.

    Usage:
      inventory
      inv
      i
    """

    key = "inventory"
    aliases = ["inv", "i"]
    help_category = "General"

    def func(self):
        ledger = _get_or_init_ledger(self.caller)
        inventory = ledger.get("inventory", [])
        credits = ledger.get("credits", 0)
        equipped = self.caller.db.equipped or {}

        lines = [f"|wInventory|n  (Credits: {credits})"]

        if not inventory:
            lines.append("  Your pack is empty.")
        else:
            for item_key in inventory:
                item = _get_item_data(item_key)
                if item:
                    name = item["name"]
                    slots = item.get("slots", [])
                else:
                    name = _pretty_name(item_key)
                    slots = []

                # Check if this item is equipped in any slot.
                equipped_slots = [s for s, v in equipped.items() if v == item_key]
                if equipped_slots:
                    slot_label = "/".join(equipped_slots)
                    tag_str = f" |g[equipped: {slot_label}]|n"
                else:
                    tag_str = ""
                slot_hint = f"({', '.join(slots)})" if slots else ""
                lines.append(f"  {name} {slot_hint}{tag_str}")

        self.caller.msg("\n".join(lines))


class CmdGet(Command):
    """Pick up items from the room floor.

    Usage:
      get all            - pick up everything on the floor
      get <item_name>    - pick up a specific item (partial name match)

    Examples:
      get all
      get blade
      get armour
      get helmet
      get dagger
    """

    key = "get"
    aliases = ["pickup", "take", "loot"]
    help_category = "General"

    def func(self):
        caller = self.caller
        args = self.args.strip().lower()

        if not args:
            caller.msg("Usage: get <item> or get all")
            return

        room = caller.location
        if not room:
            caller.msg("You are nowhere.")
            return

        floor_items = list(room.db.floor_items or [])
        if not floor_items:
            caller.msg("There is nothing on the floor to pick up.")
            return

        ledger = _get_or_init_ledger(caller)

        if args == "all":
            picked_names = []
            for item_key in floor_items:
                item_data = _get_item_data(item_key)
                name = item_data["name"] if item_data else _pretty_name(item_key)
                ledger["inventory"].append(item_key)
                picked_names.append(name)
            room.db.floor_items = []
            caller.db.ledger = ledger
            caller.msg("|gYou pick up:|n " + ", ".join(f"|w{n}|n" for n in picked_names))
            return

        # Partial name match - collect all items whose name or key contains the arg.
        matched_keys = []
        for item_key in floor_items:
            item_data = _get_item_data(item_key)
            display = item_data["name"].lower() if item_data else item_key.lower()
            if args in display or args in item_key.lower():
                matched_keys.append(item_key)

        if not matched_keys:
            caller.msg(f"You don't see '{self.args.strip()}' on the floor.")
            return

        # Remove matched items from the floor and add to inventory.
        remaining = list(floor_items)
        picked_names = []
        for item_key in matched_keys:
            remaining.remove(item_key)
            item_data = _get_item_data(item_key)
            picked_names.append(item_data["name"] if item_data else _pretty_name(item_key))
            ledger["inventory"].append(item_key)

        room.db.floor_items = remaining
        caller.db.ledger = ledger
        caller.msg("|gYou pick up:|n " + ", ".join(f"|w{n}|n" for n in picked_names))


class CmdEquip(Command):
    """Equip or unequip an item by name, or unequip a specific slot.

    Usage:
      equip <item_name|item_key>        - equip from inventory (goes to first valid slot)
      unequip <slot_name>               - clear that slot (e.g. unequip main_hand)
      unequip <item_name>               - find which slot it's in and remove it
      equip list                        - same as 'inventory'

    Slot names: head, torso, legs, feet, main_hand, off_hand, utility
    Aliases: weapon -> main_hand, module/shield -> utility

    Weapons add a flat damage bonus to every attack.
    Shield modules (utility slot) increase your max shield capacity.
    Multi-slot items (e.g. full armor) occupy all their slots at once.
    """

    key = "equip"
    aliases = ["unequip", "wield", "wear"]
    help_category = "General"

    # Maps shorthand aliases to canonical slot names.
    _SLOT_ALIASES = {
        "weapon": "main_hand",
        "offhand": "off_hand",
        "off hand": "off_hand",
        "module": "utility",
        "shield": "utility",
        "shield_module": "utility",
    }

    def func(self):
        raw = self.args.strip().lower() if self.args else ""

        if not raw or raw == "list":
            self.caller.execute_cmd("inventory")
            return

        if self.cmdstring.lower() == "unequip":
            self._unequip(raw)
            return

        # Allow "equip weapon" / "equip module" as unequip aliases.
        canonical = self._SLOT_ALIASES.get(raw) or raw
        if canonical in EQUIPMENT_SLOTS:
            self._unequip(raw)
            return

        self._equip(raw)

    def _get_equipped(self):
        return self.caller.db.equipped or _default_equipped()

    def _save_equipped(self, equipped: dict):
        self.caller.db.equipped = equipped

    def _equip(self, raw: str):
        caller = self.caller
        ledger = _get_or_init_ledger(caller)
        inventory = ledger.get("inventory", [])

        # Match item by exact key or partial name.
        matched_key = None
        for item_key in inventory:
            if raw == item_key or raw in item_key:
                matched_key = item_key
                break
            item = _get_item_data(item_key)
            if item and raw in item["name"].lower():
                matched_key = item_key
                break

        if not matched_key:
            caller.msg(
                f"You don't have '{raw}' in your inventory. "
                "Use 'inventory' to see what you're carrying."
            )
            return

        item = _get_item_data(matched_key)
        if not item:
            caller.msg(f"No item data found for '{matched_key}'. Contact an admin.")
            return

        slots = item.get("slots", [])
        if not slots:
            caller.msg(f"{item['name']} cannot be equipped (no slot defined).")
            return

        equipped = self._get_equipped()

        # Two-hand conflict checks.
        two_handed = item.get("two_handed", False)
        if two_handed and equipped.get("off_hand"):
            oh_item = _get_item_data(equipped["off_hand"])
            oh_name = oh_item["name"] if oh_item else equipped["off_hand"]
            caller.msg(
                f"{item['name']} is two-handed. "
                f"Unequip your {oh_name} from off_hand first."
            )
            return

        if "off_hand" in slots:
            mh_key = equipped.get("main_hand") or "training_vibroblade"
            mh_item = _get_item_data(mh_key)
            if mh_item and mh_item.get("two_handed"):
                caller.msg(
                    f"You're wielding {mh_item['name']} two-handed - "
                    "free your main hand before using an off-hand item."
                )
                return

        # Check all required slots are clear (or occupied by this same item already).
        blocking = []
        for slot in slots:
            current = equipped.get(slot)
            if current and current != matched_key:
                blocking.append((slot, current))

        for slot, blocking_key in blocking:
            # Auto-unequip whatever is in the way.
            self._remove_from_slot(slot, blocking_key, equipped, silent=True)

        # Apply item bonuses.
        shield_bonus = item.get("shield_bonus", 0)
        if shield_bonus:
            caller.db.shield_max = (caller.db.shield_max or 100) + shield_bonus
            # Don't let current shield exceed new max.
            caller.db.shield_integrity = min(
                caller.db.shield_integrity or 0, caller.db.shield_max
            )

        armor_bonus = item.get("armor_bonus", 0)
        if armor_bonus:
            caller.db.hp_max = (caller.db.hp_max or 100) + armor_bonus
            # Don't let current HP exceed new max (but do clamp down if somehow over).
            caller.db.hp = min(caller.db.hp or 0, caller.db.hp_max)

        # Set all slots.
        for slot in slots:
            equipped[slot] = matched_key
        self._save_equipped(equipped)

        slot_label = "/".join(slots)
        caller.msg(f"|gYou equip {item['name']}|n  [{slot_label}].")

    def _unequip(self, raw: str):
        caller = self.caller

        # Resolve slot alias.
        slot = self._SLOT_ALIASES.get(raw) or raw

        equipped = self._get_equipped()

        # Direct slot name?
        if slot in EQUIPMENT_SLOTS:
            item_key = equipped.get(slot)
            if not item_key:
                caller.msg(f"Nothing is equipped in the {slot} slot.")
                return
            self._remove_from_slot(slot, item_key, equipped, silent=False)
            self._save_equipped(equipped)
            return

        # Item name / partial name lookup.
        for eq_slot, eq_key in equipped.items():
            if not eq_key:
                continue
            if raw == eq_key or raw in eq_key:
                self._remove_from_slot(eq_slot, eq_key, equipped, silent=False)
                self._save_equipped(equipped)
                return
            item = _get_item_data(eq_key)
            if item and raw in item["name"].lower():
                self._remove_from_slot(eq_slot, eq_key, equipped, silent=False)
                self._save_equipped(equipped)
                return

        caller.msg(f"'{raw}' is not a valid slot name or equipped item. "
                   "Slot names: head, torso, legs, feet, main_hand, off_hand, utility.")

    def _remove_from_slot(self, slot: str, item_key: str, equipped: dict, silent: bool):
        """Clear an item from all slots it occupies and reverse its bonuses."""
        caller = self.caller
        item = _get_item_data(item_key)
        slots = item.get("slots", [slot]) if item else [slot]

        # Reverse shield bonus.
        shield_bonus = item.get("shield_bonus", 0) if item else 0
        if shield_bonus:
            caller.db.shield_max = max(100, (caller.db.shield_max or 100) - shield_bonus)
            caller.db.shield_integrity = min(
                caller.db.shield_integrity or 0, caller.db.shield_max
            )

        # Reverse armor bonus.
        armor_bonus = item.get("armor_bonus", 0) if item else 0
        if armor_bonus:
            caller.db.hp_max = max(100, (caller.db.hp_max or 100) - armor_bonus)
            caller.db.hp = min(caller.db.hp or 0, caller.db.hp_max)

        # Clear all slots this item occupied.
        for s in slots:
            if equipped.get(s) == item_key:
                equipped[s] = None

        # Default main_hand back to training vibroblade.
        if slot == "main_hand" and equipped.get("main_hand") is None:
            equipped["main_hand"] = "training_vibroblade"

        if not silent:
            name = item["name"] if item else _pretty_name(item_key)
            caller.msg(f"|yYou unequip {name}.|n")


class CmdShop(Command):
    """Browse a vendor's wares.

    Usage:
      shop
      shop <vendor_name>

    Lists items for sale and their credit prices.
    Use 'buy <item>' to purchase.
    """

    key = "shop"
    aliases = ["browse", "list"]
    help_category = "General"

    def func(self):
        vendor = _find_vendor_in_room(self.caller)

        if not vendor:
            self.caller.msg("There is no vendor here.")
            return

        shop_keys = vendor.db.shop or []
        if not shop_keys:
            self.caller.msg(f"{vendor.db.name or vendor.key} has nothing for sale right now.")
            return

        ledger = _get_or_init_ledger(self.caller)
        credits = ledger.get("credits", 0)
        attrs = self.caller.db.attrs or {}
        cha = attrs.get("cha", 10)
        discount = _get_background_perks(self.caller)["vendor_discount"]

        lines = [
            f"|w{vendor.db.name or vendor.key}|n - Available wares  (Your credits: {credits}, CHA: {cha})",
        ]
        for item_key in shop_keys:
            item = _get_item_data(item_key)
            if not item:
                continue
            name = item["name"]
            base_price = item.get("price", 0)
            price = _cha_adjusted_buy_price(base_price, cha, discount)
            # Show the relevant stat bonus based on actual item data keys.
            weapon_type = item.get("weapon_type")
            shield_bonus = item.get("shield_bonus")
            armor_bonus = item.get("armor_bonus")
            if weapon_type:
                bonus_text = f"+{item.get('damage_bonus', 0)} dmg  [{weapon_type}]"
            elif shield_bonus is not None:
                bonus_text = f"+{shield_bonus} shield max"
            elif armor_bonus is not None:
                bonus_text = f"+{armor_bonus} hp max"
            else:
                bonus_text = ""
            already = "|y[owned]|n " if item_key in ledger.get("inventory", []) else ""
            price_note = ""
            if base_price > 0 and price != base_price:
                price_note = f" |x(base {base_price})|n"
            lines.append(f"  {already}{name}  -  {price} credits{price_note}  ({bonus_text})")
            lines.append(f"    {item.get('desc', '')}")

        self.caller.msg("\n".join(lines))


class CmdBuy(Command):
    """Purchase an item from a vendor in your current room.

    Usage:
      buy <item_name_or_key>

    You must have enough credits. Each item can only be purchased once.
    """

    key = "buy"
    aliases = ["purchase"]
    help_category = "General"

    def func(self):
        if not self.args:
            self.caller.msg("Buy what? Usage: buy <item>")
            return

        vendor = _find_vendor_in_room(self.caller)
        if not vendor:
            self.caller.msg("There is no vendor here.")
            return

        shop_keys = vendor.db.shop or []
        raw = self.args.strip().lower()

        # Match by partial key or partial name.
        matched_key = None
        for item_key in shop_keys:
            if raw in item_key:
                matched_key = item_key
                break
            item = _get_item_data(item_key)
            if item and raw in item["name"].lower():
                matched_key = item_key
                break

        if not matched_key:
            self.caller.msg(
                f"{vendor.db.name or vendor.key} doesn't sell '{self.args.strip()}'. "
                "Use 'shop' to see available wares."
            )
            return

        item = _get_item_data(matched_key)
        if not item:
            self.caller.msg("Item data missing. Contact an admin.")
            return

        ledger = _get_or_init_ledger(self.caller)
        inventory = ledger.get("inventory", [])

        if matched_key in inventory:
            self.caller.msg(f"You already own {item['name']}.")
            return

        attrs = self.caller.db.attrs or {}
        cha = attrs.get("cha", 10)
        base_price = item.get("price", 0)
        discount = _get_background_perks(self.caller)["vendor_discount"]
        price = _cha_adjusted_buy_price(base_price, cha, discount)
        credits = int(ledger.get("credits", 0))
        if credits < price:
            self.caller.msg(
                f"You can't afford {item['name']}. "
                f"It costs {price} credits and you have {credits}."
            )
            return

        ledger["credits"] = credits - price
        inventory.append(matched_key)
        ledger["inventory"] = inventory
        self.caller.db.ledger = ledger

        self.caller.msg(
            f"|gYou purchase {item['name']} for {price} credits.|n  "
            f"Remaining credits: {ledger['credits']}. "
            f"Use 'equip {matched_key}' to equip it."
        )


class CmdSell(Command):
    """Sell an item from your inventory to a vendor.

    Usage:
      sell <item_name_or_key>

    Vendors pay around 50% of an item's original buy price, adjusted by CHA.
    You must have the item in your inventory - unequip it first if it is
    currently worn or wielded. Items with no listed buy price (e.g. the
    starter training_vibroblade) have no resale value.
    """

    key = "sell"
    help_category = "General"

    def func(self):
        if not self.args:
            self.caller.msg("Sell what? Usage: sell <item>")
            return

        vendor = _find_vendor_in_room(self.caller)
        if not vendor:
            self.caller.msg("There is no vendor here to sell to.")
            return

        ledger = _get_or_init_ledger(self.caller)
        inventory = ledger.get("inventory", [])
        raw = self.args.strip().lower()

        # Match by partial key or partial name.
        matched_key = None
        for item_key in inventory:
            if raw in item_key:
                matched_key = item_key
                break
            item = _get_item_data(item_key)
            if item and raw in item["name"].lower():
                matched_key = item_key
                break

        if not matched_key:
            self.caller.msg(
                f"You don't have '{self.args.strip()}' in your inventory. "
                "Use 'inventory' to see what you're carrying."
            )
            return

        item = _get_item_data(matched_key)
        if not item:
            self.caller.msg(f"Item data missing for '{matched_key}'. Contact an admin.")
            return

        # Can't sell equipped items - the player must unequip first.
        equipped = self.caller.db.equipped or {}
        if matched_key in equipped.values():
            self.caller.msg(
                f"{item['name']} is currently equipped. "
                "Unequip it first (e.g. 'unequip main_hand'), then sell."
            )
            return

        base_price = item.get("price", 0)
        if base_price <= 0:
            self.caller.msg(
                f"{item['name']} has no resale value."
            )
            return

        attrs = self.caller.db.attrs or {}
        cha = attrs.get("cha", 10)
        sell_bonus = _get_background_perks(self.caller)["sell_bonus"]
        sell_price = _cha_adjusted_sell_price(base_price, cha, sell_bonus)
        inventory.remove(matched_key)
        ledger["inventory"] = inventory
        ledger["credits"] = int(ledger.get("credits", 0)) + sell_price
        self.caller.db.ledger = ledger

        self.caller.msg(
            f"|gYou sell {item['name']} for {sell_price} credits.|n  "
            f"Remaining credits: {ledger['credits']}."
        )


class CmdEquipment(Command):
    """Show your equipped gear by slot.

    Usage:
      eq
      equipment

    Displays all equipment slots and what is currently equipped in each.
    Use 'equip <item>' to equip, 'unequip <slot>' to remove.
    """

    key = "equipment"
    aliases = ["eq"]
    help_category = "General"

    def func(self):
        caller = self.caller
        equipped = caller.db.equipped or {}

        slot_labels = {
            "head":      "Head     ",
            "torso":     "Torso    ",
            "legs":      "Legs     ",
            "feet":      "Feet     ",
            "main_hand": "Main hand",
            "off_hand":  "Off hand ",
            "utility":   "Utility  ",
        }

        # Derive combat style for the header annotation.
        weapon_item  = _get_item_data(equipped.get("main_hand") or "training_vibroblade")
        offhand_item = _get_item_data(equipped.get("off_hand")) if equipped.get("off_hand") else None
        if weapon_item and weapon_item.get("two_handed"):
            style_label = "|y[two-handed]|n"
        elif offhand_item and offhand_item.get("shield_bonus"):
            style_label = "|c[sword & shield]|n"
        elif offhand_item and offhand_item.get("weapon_type"):
            style_label = "|g[dual wield]|n"
        else:
            style_label = "|x[single + unarmed off-hand]|n"

        lines = [f"|w=== Equipment ({caller.name}) ===|n  {style_label}"]
        for slot in EQUIPMENT_SLOTS:
            item_key = equipped.get(slot)
            label = slot_labels.get(slot, slot)
            if not item_key:
                lines.append(f"  {label} : |x[empty]|n")
            else:
                item = _get_item_data(item_key)
                if item:
                    name = item["name"]
                    # Build a brief annotation without exposing raw numbers.
                    hints = []
                    if item.get("weapon_type"):
                        hints.append(item["weapon_type"])
                    if item.get("shield_bonus"):
                        hints.append("shield+")
                    if item.get("armor_bonus"):
                        hints.append("armor+")
                    hint_str = f"  |x({', '.join(hints)})|n" if hints else ""
                    lines.append(f"  {label} : |w{name}|n{hint_str}")
                else:
                    lines.append(f"  {label} : |w{_pretty_name(item_key)}|n")

        caller.msg("\n".join(lines))


class CmdSkills(Command):
    """Display your current skill levels and available skill points.

    Usage:
      skills

    Combat skills (melee, dodge, parry) grow through use up to skill 60.
    Weapon-type skills (blades, bludgeons, polearms, ranged) grow when you land hits
    with that weapon type, also up to 60. Spend skill points from level-up
    to push any skill above 60 using 'train <skill>'.
    """

    key = "skills"
    aliases = ["sk"]
    locks = "cmd:all()"
    help_category = "Combat"

    def func(self):
        caller = self.caller
        skills = caller.db.skills or {}
        sp = caller.db.skill_points or 0
        attrs = caller.db.attrs or {}
        ap = caller.db.attr_points or 0
        level = caller.db.level or 1
        soft_cap = _SKILL_SOFT_CAP

        def _row(label, key, default=10):
            val = skills.get(key, default)
            cap_tag = f"  |y(cap)|n" if val >= soft_cap else ""
            return f"  {label:<10}: {val:>3}{cap_tag}"

        def _arow(label, key):
            val = attrs.get(key, 10)
            return f"  {label:<6}: {val:>3}"

        lines = [
            f"|w=== Skills ({caller.name}) ===|n",
            f"|wCombat|n",
            _row("Melee", "melee"),
            _row("Dodge", "dodge"),
            _row("Parry", "parry"),
            f"|wWeapon type|n",
            _row("Blades", "blades", default=5),
            _row("Bludgeons", "bludgeons", default=5),
            _row("Polearms", "polearms", default=5),
            _row("Ranged", "ranged", default=5),
            f"|wSurvival|n",
            _row("Camping", "camping", default=0),
            f"",
            f"  Skill points available: |y{sp}|n",
        ]
        if sp > 0:
            lines.append(
                "  Use '|wtrain <skill>|n' to spend - valid: "
                "melee, dodge, parry, blades, bludgeons, polearms, ranged, camping."
            )
        lines.append(f"  Skills auto-grow by use up to {soft_cap}; spend points to go higher.")

        lines += [
            f"",
            f"|wAttributes|n  (base 10; levels 2-5 auto-gain +1 all; level 6+ spend attr points)",
            f"  {_arow('STR', 'str')}  {_arow('DEX', 'dex')}  {_arow('CON', 'con')}",
            f"  {_arow('MIND', 'mind')}  {_arow('CHA', 'cha')}  {_arow('PER', 'per')}",
            f"  {_arow('LUCK', 'luck')}",
            f"",
            f"  Attr points available: |y{ap}|n",
        ]
        if ap > 0:
            lines.append("  Use '|wtrain <attr>|n' to spend - valid: str, dex, con, mind, cha, per, luck.")
        elif level < 6:
            lines.append(f"  Attr points awarded at level 6+ (you are level {level}).")

        caller.msg("\n".join(lines))


class CmdTrain(Command):
    """Spend a skill point to increase a skill, or an attr point to raise an attribute.

    Usage:
      train <skill>    - spend a skill point (melee, dodge, parry, blades,
                         bludgeons, polearms, ranged, camping)
      train <attr>     - spend an attr point (str, dex, con, mind, cha, per,
                         luck) [level 6+]

    Skill points: awarded at each level-up (3 per level).
    Skills auto-grow through use up to 60; this command lets you push higher.

    Attr points: awarded at level 6+ (2 per level). Attributes start at 10 and
    cap at 30. CON raises HP max (+3), MIND raises PSI max (+5) immediately.
    Levels 2-5 auto-grant +1 to all attrs each level.
    """

    key = "train"
    locks = "cmd:all()"
    help_category = "Combat"

    _TRAINABLE_SKILLS = ("melee", "dodge", "parry", "blades", "bludgeons", "polearms", "ranged", "camping")
    _TRAINABLE_ATTRS  = ("str", "dex", "con", "mind", "cha", "per", "luck")
    _ATTR_CAP = 30

    def func(self):
        caller = self.caller
        if not self.args:
            caller.msg(
                f"Usage: train <skill|attr>\n"
                f"  Skills: {', '.join(self._TRAINABLE_SKILLS)}\n"
                f"  Attrs (level 6+): {', '.join(self._TRAINABLE_ATTRS)}"
            )
            return

        target = self.args.strip().lower()

        if target in self._TRAINABLE_ATTRS:
            self._train_attr(caller, target)
            return

        if target in self._TRAINABLE_SKILLS:
            self._train_skill(caller, target)
            return

        # Check if target is a guild skill.
        guilds = _load_world_data().get("guilds", {})
        guild_levels = caller.db.guild_levels or {}
        for gkey, gdata in guilds.items():
            if target in gdata.get("skills", {}):
                if guild_levels.get(gkey, 0) < 1:
                    gname = gdata.get("name", gkey)
                    caller.msg(f"|yYou must be a member of the {gname} to train {target}.|n")
                    return
                self._train_guild_skill(caller, gkey, target, gdata)
                return

        caller.msg(
            f"Unknown training target '{target}'.\n"
            f"  Skills: {', '.join(self._TRAINABLE_SKILLS)}\n"
            f"  Attrs: {', '.join(self._TRAINABLE_ATTRS)}\n"
            f"  Guild skills: use |wguilds|n to see your available guild skills."
        )

    def _train_skill(self, caller, skill_name: str):
        sp = caller.db.skill_points or 0
        if sp < 1:
            caller.msg("You have no skill points to spend. Earn more by levelling up.")
            return

        default = 10 if skill_name in ("melee", "dodge", "parry") else 5 if skill_name in ("blades", "bludgeons", "polearms", "ranged") else 0
        skills = caller.db.skills or {}
        current = skills.get(skill_name, default)
        if current >= 100:
            caller.msg(f"Your {skill_name} is already at its maximum (100).")
            return

        skills[skill_name] = current + 1
        caller.db.skills = skills
        caller.db.skill_points = sp - 1
        caller.msg(
            f"|gYour {skill_name} skill increases to {skills[skill_name]}.|n  "
            f"Remaining skill points: {caller.db.skill_points}."
        )

    def _train_attr(self, caller, attr_name: str):
        level = caller.db.level or 1
        if level < 6:
            caller.msg(
                f"Attribute training requires level 6 or higher "
                f"(you are level {level}). Until then, attrs improve automatically each level-up."
            )
            return

        ap = caller.db.attr_points or 0
        if ap < 1:
            caller.msg("You have no attribute points to spend. Earn more by levelling up (2/level from level 6).")
            return

        attrs = caller.db.attrs or {}
        current = attrs.get(attr_name, 10)
        if current >= self._ATTR_CAP:
            caller.msg(f"Your {attr_name.upper()} is already at maximum ({self._ATTR_CAP}).")
            return

        attrs[attr_name] = current + 1
        caller.db.attrs = attrs
        caller.db.attr_points = ap - 1

        # Apply derived effects immediately.
        extra = ""
        if attr_name == "con":
            caller.db.hp_max = (caller.db.hp_max or 100) + 3
            caller.db.stamina_max = (caller.db.stamina_max or 100) + 2
            extra = " (+3 HP max, +2 Stamina max)"
        elif attr_name == "dex":
            caller.db.stamina_max = (caller.db.stamina_max or 100) + 3
            extra = " (+3 Stamina max)"
        elif attr_name == "mind":
            caller.db.psi_max = (caller.db.psi_max or 60) + 5
            caller.db.shield_max = (caller.db.shield_max or 100) + 4
            extra = " (+5 PSI max, +4 Shield max)"
        elif attr_name == "per":
            caller.db.focus_max = (caller.db.focus_max or 50) + 2
            extra = " (+2 Focus max)"

        caller.msg(
            f"|gYour {attr_name.upper()} increases to {attrs[attr_name]}.{extra}|n  "
            f"Remaining attr points: {caller.db.attr_points}."
        )

    def _train_guild_skill(self, caller, guild_key: str, skill_key: str, guild_data: dict):
        """Spend XP to improve a guild skill by 1 percentage point."""
        sk_data = guild_data["skills"][skill_key]
        guild_levels = caller.db.guild_levels or {}
        rank = guild_levels.get(guild_key, 0)

        guild_skills = caller.db.guild_skills or {}
        g_skills = guild_skills.get(guild_key, {})
        current_pct = g_skills.get(skill_key, 0)

        # Rank gate: what is the maximum % trainable at this rank?
        cap = _guild_skill_cap(guild_key, skill_key, rank)
        if current_pct >= cap:
            if cap < 100:
                caller.msg(
                    f"|y{sk_data['name']} is capped at {cap}% for rank {rank}. "
                    f"Advance your guild rank to unlock higher training.|n"
                )
            else:
                caller.msg(f"|y{sk_data['name']} is already at its maximum (100%).|n")
            return

        # XP cost scales in 4 tiers: base * (1 + current_pct // 25).
        base_cost = sk_data.get("xp_cost_per_pct", 50)
        xp_cost = base_cost * (1 + current_pct // 25)

        xp = caller.db.xp or 0
        if xp < xp_cost:
            caller.msg(
                f"|yNot enough XP. Training {sk_data['name']} to {current_pct + 1}% "
                f"costs {xp_cost} XP (you have {xp} XP).|n"
            )
            return

        # Deduct XP and apply.
        caller.db.xp = xp - xp_cost
        new_pct = current_pct + 1
        g_skills[skill_key] = new_pct
        guild_skills[guild_key] = g_skills
        caller.db.guild_skills = guild_skills

        gname = guild_data.get("name", guild_key)
        caller.msg(
            f"|g[{gname}] {sk_data['name']} increases to {new_pct}%.|n  "
            f"Cost: {xp_cost} XP.  Remaining XP: {caller.db.xp}."
        )
        if new_pct % 25 == 0:
            # Announce milestone bonus.
            desc = sk_data.get("desc", "")
            caller.msg(f"|c  Milestone: {desc}|n")


class CmdTechnique(Command):
    """Queue a combat technique to fire on the next available round.

    Usage:
      slash          - Slash          (blades >=20, 1-round wind-up, applies Bleeding 3 rounds)
      concussion     - Concussion Strike (bludgeons >=20, 2-round wind-up, stuns 1 round)
      lunge          - Lunge          (polearms/blades >=20, 1-round wind-up, pierces shields)

    Each technique requires the matching weapon type equipped in main_hand and
    a minimum weapon-type skill of 20. Skills grow automatically through combat.

    The technique replaces your normal main-hand attack when its wind-up
    completes. Must be in active combat. Only one technique can be queued
    at a time.
    """

    key = "slash"
    aliases = ["concussion", "lunge"]
    help_category = "Combat"

    def func(self):
        _ensure_project_root_on_path()
        caller = self.caller
        session = caller.db.combat_session or {}
        if not session.get("target_id"):
            caller.msg("You must be in active combat to use techniques.")
            return

        technique_name = self.cmdstring.lower()

        from mudgame.systems.techniques import TECHNIQUE_DEFS, check_technique_requirements
        defn = TECHNIQUE_DEFS.get(technique_name)
        if not defn:
            caller.msg(f"Unknown technique: {technique_name}.")
            return

        # --- Weapon-type and skill gate -------------------------------------
        equipped = caller.db.equipped or {}
        weapon_key = equipped.get("main_hand") or "training_vibroblade"
        weapon_item = _get_item_data(weapon_key)
        active_type = weapon_item.get("weapon_type", "") if weapon_item else ""
        skills = caller.db.skills or {}

        allowed, reason = check_technique_requirements(technique_name, active_type, skills)
        if not allowed:
            caller.msg(f"|y{reason}|n")
            return
        # -------------------------------------------------------------------

        existing = caller.db.queued_technique
        if existing and isinstance(existing, dict):
            ex_name = existing.get("name", "?")
            ex_tr = existing.get("ticks_remaining", 0)
            caller.msg(
                f"|yYou already have {ex_name.title()} queued "
                f"({ex_tr} round(s) until it fires). Wait for it to resolve.|n"
            )
            return

        wind_up = defn["wind_up"]
        caller.db.queued_technique = {
            "name": technique_name,
            "ticks_remaining": wind_up,
        }

        caller.msg(
            f"|cYou begin winding up {defn['name']}.|n  "
            f"Fires in {wind_up} round(s). - {defn['desc']}"
        )
