@echo off
setlocal
title Helion Vanta — Dev Launcher

set REPO=%~dp0
set PYTHON=%REPO%.venv312\Scripts\python.exe
set CLIENT_DIR=%REPO%helionvanta_client

echo ============================================================
echo   HELION VANTA — Dev Launcher
echo   1) Starts MUD server in a background window
echo   2) Waits 12 seconds for Evennia to boot
echo   3) Starts the pygame client in this window
echo ============================================================
echo.

if not exist "%PYTHON%" (
    echo [ERROR] venv not found at %PYTHON%
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

:: ── Start server in a separate window ─────────────────────────────────────
:: Note: double-double-quotes around the path handle spaces in the repo path.
echo [1/3] Starting MUD server in background window...
start "Helion Vanta — MUD Server" cmd /k ""%REPO%start_server.bat""

:: ── Wait for Evennia to boot ───────────────────────────────────────────────
echo [2/3] Waiting 12 seconds for server to boot...
timeout /t 12 /nobreak

:: ── Quick connectivity check ──────────────────────────────────────────────
netstat -an | find "0.0.0.0:4000" >nul 2>&1
if errorlevel 1 (
    echo.
    echo [WARN] Port 4000 does not appear to be open yet.
    echo        The server may still be loading. You can try connecting
    echo        manually from the login panel once it is ready.
    echo.
) else (
    echo [OK]   Server is listening on port 4000.
    echo.
)

:: ── Launch client ──────────────────────────────────────────────────────────
echo [3/3] Launching pygame client...
echo.
cd /d "%CLIENT_DIR%"
"%PYTHON%" main.py %*

echo.
echo Client closed.
echo (Server window is still running — use stop_server.bat to shut it down.)
pause
