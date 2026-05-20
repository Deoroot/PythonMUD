@echo off
setlocal
title Helion Vanta — MUD Server

set REPO=%~dp0
set PYTHON=%REPO%.venv312\Scripts\python.exe
set EVENNIA=%REPO%.venv312\Scripts\evennia
set GAME_DIR=%REPO%helionvanta
set LOG=%REPO%helionvanta\server\logs\server.log

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

:: evennia start launches the Twisted server in the background and returns.
:: We then tail the log so this window stays useful.
echo Starting Evennia... (use stop_server.bat to stop cleanly)
echo.
"%PYTHON%" "%EVENNIA%" start

if errorlevel 1 (
    echo.
    echo [ERROR] evennia start failed. Check the logs above.
    pause & exit /b 1
)

echo.
echo Server process launched. Tailing server log (Ctrl+C to stop tail):
echo.
:: Use PowerShell's Get-Content -Wait to tail the log
powershell -Command "Get-Content -Path '%LOG%' -Wait -Tail 30" 2>nul

pause
