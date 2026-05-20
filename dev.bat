@echo off
setlocal
title Helion Vanta — Dev Launcher

set REPO=%~dp0
set PYTHON=%REPO%.venv312\Scripts\python.exe
set EVENNIA=%REPO%.venv312\Scripts\evennia
set GAME_DIR=%REPO%helionvanta
set CLIENT_DIR=%REPO%helionvanta_client

echo ============================================================
echo   HELION VANTA — Dev Launcher
echo   1) Starts MUD server in a background window
echo   2) Waits 5 seconds for it to boot
echo   3) Starts the pygame client in this window
echo ============================================================
echo.

if not exist "%PYTHON%" (
    echo [ERROR] venv not found.
    echo Run:  python -m venv .venv312  ^&^&  .venv312\Scripts\pip install -r requirements.txt
    pause & exit /b 1
)

:: ── Auto-install pygame if missing ────────────────────────────────────────
"%PYTHON%" -c "import pygame" >nul 2>&1
if errorlevel 1 (
    echo [INFO] pygame not found — installing...
    "%PYTHON%" -m pip install pygame
    if errorlevel 1 (
        echo [ERROR] Failed to install pygame.
        pause & exit /b 1
    )
    echo [INFO] pygame installed OK.
    echo.
)

:: ── Start server in a separate window ────────────────────────────────────
echo [1/3] Starting MUD server in background window...
start "Helion Vanta — MUD Server" cmd /k ^
    "cd /d "%GAME_DIR%" && "%PYTHON%" "%EVENNIA%" start --log"

:: ── Wait for Evennia to boot ──────────────────────────────────────────────
echo [2/3] Waiting 6 seconds for server to boot...
timeout /t 6 /nobreak >nul

:: ── Launch client ─────────────────────────────────────────────────────────
echo [3/3] Launching pygame client...
echo.
cd /d "%CLIENT_DIR%"
"%PYTHON%" main.py %*

echo.
echo Client closed.
echo (The server window keeps running — use stop_server.bat to shut it down.)
pause
