# -*- coding: utf-8 -*-
"""
Connection screen

This is the text to show the user when they first connect to the game (before
they log in).

To change the login screen in this module, do one of the following:

- Define a function `connection_screen()`, taking no arguments. This will be
  called first and must return the full string to act as the connection screen.
  This can be used to produce more dynamic screens.
- Alternatively, define a string variable in the outermost scope of this module
  with the connection string that should be displayed. If more than one such
  variable is given, Evennia will pick one of them at random.

The commands available to the user when the connection screen is shown
are defined in evennia.default_cmds.UnloggedinCmdSet. The parsing and display
of the screen is done by the unlogged-in "look" command.

"""

CONNECTION_SCREEN = """
|c=================================================================|n

      |w H  E  L  I  O  N     ·     V  A  N  T  A |n

      |y"Beyond the Reach, the frontier waits."|n

|c=================================================================|n

  The Helion System. Eighty years of colony ships have carved
  something worth fighting for out of the void. Helion Station
  stands as the last outpost before uncharted space — supply depot,
  rough-edged sanctuary, and the only place to fence salvage without
  too many questions asked.

  Beyond it: |cVanta IX|n. Alien ruins. Architecture no engineer can
  date. A vault that has swallowed every expedition sent to open it.
  The Reaches draw contractors, discharged soldiers, and those with
  nothing left to lose.

  Energy weapons are a colony luxury. This far out, you learn the
  blade — or you don't come back.

|c=================================================================|n

  Connect to an existing account : |wconnect <name> <password>|n
  Create a new account            : |wcreate <name> <password>|n

  Type |whelp|n for commands · |wlook|n to re-display this screen.

|c=================================================================|n"""
