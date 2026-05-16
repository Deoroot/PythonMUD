"""
Command sets

All commands in the game must be grouped in a cmdset.  A given command
can be part of any number of cmdsets and cmdsets can be added/removed
and merged onto entities at runtime.

To create new commands to populate the cmdset, see
`commands/command.py`.

This module wraps the default command sets of Evennia; overloads them
to add/remove commands from the default lineup. You can create your
own cmdsets by inheriting from them or directly from `evennia.CmdSet`.

"""

from evennia import default_cmds

from commands.admin_commands import CmdMudBuild, CmdResetChar, CmdClaimLevels, CmdGrantShip
from commands.char_commands import CmdRecreate, CmdReincarnate
from commands.quest_commands import CmdQuest, CmdTasks, CmdTravel, CmdMap
from commands.social_commands import (
    CmdScan, CmdConsider, CmdAppraise, CmdStatus, CmdReputation,
    CmdLook, CmdMoveAlias, CmdTalk,
)
from commands.combat_commands import CmdAttack, CmdKick, CmdSleep, CmdWake
from commands.psi_commands import CmdPsi
from commands.inventory_commands import (
    CmdInventory, CmdGet, CmdEquip, CmdEquipment,
    CmdShop, CmdBuy, CmdSell, CmdSkills, CmdTrain, CmdTechnique,
)
from commands.guild_commands import CmdGuilds, CmdJoin, CmdAdvance, CmdLeaveGuild, CmdSunder, CmdWarlordStrike
from commands.overworld_commands import OverworldCmdSet  # noqa: F401 — imported so Evennia can resolve it
from commands.ship_commands import CmdShips


class CharacterCmdSet(default_cmds.CharacterCmdSet):
    """
    The `CharacterCmdSet` contains general in-game commands like `look`,
    `get`, etc available on in-game Character objects. It is merged with
    the `AccountCmdSet` when an Account puppets a Character.
    """

    key = "DefaultCharacter"

    def at_cmdset_creation(self):
        """
        Populates the cmdset
        """
        super().at_cmdset_creation()
        #
        # any commands you add below will overload the default ones.
        #
        self.add(CmdScan())
        self.add(CmdTravel())
        self.add(CmdQuest())
        self.add(CmdTasks())
        self.add(CmdMudBuild())
        self.add(CmdResetChar())
        self.add(CmdRecreate())
        self.add(CmdReincarnate())
        self.add(CmdClaimLevels())
        self.add(CmdAttack())
        self.add(CmdKick())
        self.add(CmdStatus())
        self.add(CmdReputation())
        self.add(CmdSleep())
        self.add(CmdWake())
        self.add(CmdLook())
        self.add(CmdMoveAlias())
        self.add(CmdTalk())
        self.add(CmdInventory())
        self.add(CmdGet())
        self.add(CmdEquip())
        self.add(CmdEquipment())
        self.add(CmdShop())
        self.add(CmdBuy())
        self.add(CmdSell())
        self.add(CmdSkills())
        self.add(CmdTrain())
        self.add(CmdTechnique())
        self.add(CmdPsi())
        self.add(CmdConsider())
        self.add(CmdAppraise())
        self.add(CmdMap())
        self.add(CmdGuilds())
        self.add(CmdJoin())
        self.add(CmdAdvance())
        self.add(CmdLeaveGuild())
        self.add(CmdSunder())
        self.add(CmdWarlordStrike())
        self.add(CmdShips())
        self.add(CmdGrantShip())


class AccountCmdSet(default_cmds.AccountCmdSet):
    """
    This is the cmdset available to the Account at all times. It is
    combined with the `CharacterCmdSet` when the Account puppets a
    Character. It holds game-account-specific commands, channel
    commands, etc.
    """

    key = "DefaultAccount"

    def at_cmdset_creation(self):
        """
        Populates the cmdset
        """
        super().at_cmdset_creation()
        #
        # any commands you add below will overload the default ones.
        #


class UnloggedinCmdSet(default_cmds.UnloggedinCmdSet):
    """
    Command set available to the Session before being logged in.  This
    holds commands like creating a new account, logging in, etc.
    """

    key = "DefaultUnloggedin"

    def at_cmdset_creation(self):
        """
        Populates the cmdset
        """
        super().at_cmdset_creation()
        #
        # any commands you add below will overload the default ones.
        #


class SessionCmdSet(default_cmds.SessionCmdSet):
    """
    This cmdset is made available on Session level once logged in. It
    is empty by default.
    """

    key = "DefaultSession"

    def at_cmdset_creation(self):
        """
        This is the only method defined in a cmdset, called during
        its creation. It should populate the set with command instances.

        As and example we just add the empty base `Command` object.
        It prints some info.
        """
        super().at_cmdset_creation()
        #
        # any commands you add below will overload the default ones.
        #
