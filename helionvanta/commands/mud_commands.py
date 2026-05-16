"""
mud_commands.py — DEPRECATED SHIM

All commands have been extracted into focused modules:

  cmd_utils.py          shared helpers and constants
  guild_commands.py     CmdGuilds, CmdJoin, CmdAdvance, CmdLeaveGuild, CmdSunder
  admin_commands.py     CmdMudBuild, CmdResetChar, CmdClaimLevels, CmdGrantShip
  inventory_commands.py CmdInventory, CmdGet, CmdEquip, CmdShop, CmdBuy, CmdSell,
                        CmdEquipment, CmdSkills, CmdTrain, CmdTechnique
  social_commands.py    CmdScan, CmdConsider, CmdAppraise, CmdStatus, CmdReputation,
                        CmdLook, CmdMoveAlias, CmdTalk
  quest_commands.py     CmdQuest, CmdTasks, CmdTravel, CmdMap
  char_commands.py      CmdRecreate, CmdReincarnate
  combat_commands.py    combat engine + CmdAttack, CmdKick, CmdSleep, CmdWake
  psi_commands.py       CmdPsi

default_cmdsets.py now imports directly from those modules.
This file is retained only as a breadcrumb and may be deleted once the
codebase has been verified stable.
"""
