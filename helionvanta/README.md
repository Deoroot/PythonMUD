# Welcome to Evennia!

This is your game directory, set up to let you start with
your new game right away. An overview of this directory is found here:
https://github.com/evennia/evennia/wiki/Directory-Overview#the-game-directory

You can delete this readme file when you've read it and you can
re-arrange things in this game-directory to suit your own sense of
organisation (the only exception is the directory structure of the
`server/` directory, which Evennia expects). If you change the structure
you must however also edit/add to your settings file to tell Evennia
where to look for things.

Your game's main configuration file is found in
`server/conf/settings.py` (but you don't need to change it to get
started). If you just created this directory (which means you'll already
have a `virtualenv` running if you followed the default instructions),
`cd` to this directory then initialize a new database using

    evennia migrate

To start the server, stand in this directory and run

    evennia start

This will start the server, logging output to the console. Make
sure to create a superuser when asked. By default you can now connect
to your new game using a MUD client on `localhost`, port `4000`.  You can
also log into the web client by pointing a browser to
`http://localhost:4001`.

# Getting started

From here on you might want to look at one of the beginner tutorials:
http://github.com/evennia/evennia/wiki/Tutorials.

Evennia's documentation is here:
https://github.com/evennia/evennia/wiki.

Enjoy!

# Helion-Vanta Runtime Notes

This gamedir is wired to the project-level vertical slice data in `../mudgame`.

## Custom runtime commands

- `mudbuild` (Builder only): build or refresh the world from data.
- `scan`: show room tactical metadata and local hostiles.
- `travel <helion|vanta>`: shuttle travel between planets.
- `quest` or `q`: list active quest contracts.

## Startup behavior

On first `evennia migrate`, the `at_initial_setup` hook attempts to build the Helion-Vanta world automatically.
If needed later, run `mudbuild` in-game as a Builder/Admin.

## Python version note

If `evennia migrate` fails under Python 3.13 or 3.14, use the workspace helper from the project root:

`./tools/setup-evennia-env.ps1`

Then run Evennia using the virtualenv Python.
