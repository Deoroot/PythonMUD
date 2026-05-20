@echo off
setlocal
title Helion Vanta — MUD Server

set REPO=%~dp0
set PYTHON=%REPO%.venv312\Scripts\python.exe
set EVENNIA=%REPO%.venv312\Scripts\evennia
set GAME_DIR=%REPO%helionvanta

echo ============================================================
echo   HELION VANTA — MUD Server
echo   Game dir : %GAME_DIR%
echo   Python   : %PYTHON%
echo ============================================================
echo.

if not exist "%PYTHON%" (
    echo [ERROR] venv not found at %PYTHON%
    echo Run:  python -m venv .venv312  ^&^&  .venv312\Scripts\pip install -r requirements.txt
    pause & exit /b 1
)

cd /d "%GAME_DIR%"
echo Starting Evennia... (Ctrl+C to stop, or run stop_server.bat)
echo.
"%PYTHON%" "%EVENNIA%" start --log

echo.
echo Server stopped.
pause
