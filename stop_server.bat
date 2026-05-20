@echo off
setlocal
title Helion Vanta — Stop Server

set REPO=%~dp0
set PYTHON=%REPO%.venv312\Scripts\python.exe
set EVENNIA=%REPO%.venv312\Scripts\evennia
set GAME_DIR=%REPO%helionvanta

cd /d "%GAME_DIR%"
echo Stopping Evennia...
"%PYTHON%" "%EVENNIA%" stop

echo Done.
timeout /t 2 >nul
