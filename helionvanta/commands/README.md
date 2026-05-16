# commands/

Custom command modules for Helion Vanta. All commands are registered in
`default_cmdsets.py`; each module is independently importable.

## Module Index

| File | Contents |
|---|---|
| `cmd_utils.py` | Shared helpers, constants, utility functions — no Command classes |
| `guild_commands.py` | `CmdGuilds`, `CmdJoin`, `CmdAdvance`, `CmdLeaveGuild`, `CmdSunder` |
| `admin_commands.py` | `CmdMudBuild`, `CmdResetChar`, `CmdClaimLevels`, `CmdGrantShip` |
| `inventory_commands.py` | `CmdInventory`, `CmdGet`, `CmdEquip`, `CmdShop`, `CmdBuy`, `CmdSell`, `CmdEquipment`, `CmdSkills`, `CmdTrain`, `CmdTechnique` |
| `social_commands.py` | `CmdScan`, `CmdConsider`, `CmdAppraise`, `CmdStatus`, `CmdReputation`, `CmdLook`, `CmdMoveAlias`, `CmdTalk` |
| `quest_commands.py` | `CmdQuest`, `CmdTasks`, `CmdTravel`, `CmdMap` |
| `char_commands.py` | `CmdRecreate`, `CmdReincarnate` |
| `combat_commands.py` | Combat engine + `CmdAttack`, `CmdKick`, `CmdSleep`, `CmdWake` |
| `psi_commands.py` | `CmdPsi` (heal / shock / ward / bolt / shatter) |
| `overworld_commands.py` | `CmdOverworldMove`, `CmdOverworldMap`, `CmdOverworldEnter`, `CmdOverworldLook` |
| `ship_commands.py` | `CmdShips` |
| `default_cmdsets.py` | Cmdset registration — imports from all of the above |
| `mud_commands.py` | Deprecated tombstone — safe to delete |

## Adding a New Command

1. Add the class to the appropriate domain module (or create a new one).
2. Import it in `default_cmdsets.py` and add `self.add(CmdFoo())` in
   `CharacterCmdSet.at_cmdset_creation`.
3. If it needs shared helpers, import from `cmd_utils.py`.
