@echo off
setlocal
title Helion Vanta — Client

set REPO=%~dp0
set PYTHON=%REPO%.venv312\Scripts\python.exe
set CLIENT_DIR=%REPO%helionvanta_client

echo ============================================================
echo   HELION VANTA — Pygame Client
echo   Client dir : %CLIENT_DIR%
echo   Python     : %PYTHON%
echo ============================================================
echo.

if not exist "%PYTHON%" (
    echo [ERROR] venv not found at %PYTHON%
    echo Run:  python -m venv .venv312  ^&^&  .venv312\Scripts\pip install -r requirements.txt
    pause & exit /b 1
)

:: Auto-install pygame if missing
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

cd /d "%CLIENT_DIR%"
echo Launching client... %*
echo.
"%PYTHON%" main.py %*

echo.
echo Client closed.
pause
