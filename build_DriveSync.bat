@echo off
REM ============================================================
REM build_drive_copy_icon.bat - Build drive_copy.exe using `python`
REM ============================================================

setlocal enabledelayedexpansion
pushd %~dp0

REM ---- Config ----
set APP_NAME=DriveSync
set SCRIPT_NAME=DriveSync.py
set ICON_FILE=DriveSync.ico

REM ---- Ensure virtual environment exists ----
if not exist .venv (
    echo [*] Creating virtual environment with python...
    python -m venv .venv
    if errorlevel 1 (
        echo [!] Could not create virtual environment. Ensure Python is installed and on PATH.
        exit /b 1
    )
)

REM ---- Activate venv ----
call .venv\Scripts\activate

REM ---- Upgrade pip & install build deps ----
echo [*] Installing build dependencies...
python -m pip install --upgrade pip
python -m pip install pyinstaller tqdm

REM ---- Clean previous builds ----
echo [*] Cleaning build artifacts...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist %APP_NAME%.spec del /q %APP_NAME%.spec

REM ---- Build (console app with icon) ----
echo [*] Building %APP_NAME%.exe with icon "%ICON_FILE%"...
if exist "%ICON_FILE%" (
    python -m PyInstaller --onefile --name "%APP_NAME%" --icon "%ICON_FILE%" "%SCRIPT_NAME%"
) else (
    echo [!] Icon file "%ICON_FILE%" not found. Building without icon.
    python -m PyInstaller --onefile --name "%APP_NAME%" "%SCRIPT_NAME%"
)

if errorlevel 1 (
    echo [!] Build failed.
    exit /b 1
)

echo.
echo [OK] Build complete.
echo     Output: dist\%APP_NAME%.exe
echo.

pause
