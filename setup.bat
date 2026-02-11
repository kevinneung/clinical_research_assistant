@echo off
:: Clinical Research Assistant - First-Time Setup
:: Double-click this file to set up everything and launch the app.
setlocal enabledelayedexpansion

cd /d "%~dp0"

echo ============================================
echo   Clinical Research Assistant - Setup
echo ============================================
echo.

:: -------------------------------------------
:: 1. Check for Python
:: -------------------------------------------
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python was not found on your system.
    echo Please install Python 3.11+ from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

:: Verify Python version >= 3.11
for /f "tokens=2 delims= " %%v in ('python --version 2^>^&1') do set PYVER=%%v
for /f "tokens=1,2 delims=." %%a in ("!PYVER!") do (
    if %%a lss 3 (
        echo [ERROR] Python 3.11+ is required. Found: !PYVER!
        pause
        exit /b 1
    )
    if %%a equ 3 if %%b lss 11 (
        echo [ERROR] Python 3.11+ is required. Found: !PYVER!
        pause
        exit /b 1
    )
)
echo [OK] Python !PYVER! found.

:: -------------------------------------------
:: 2. Create virtual environment
:: -------------------------------------------
if exist "venv\Scripts\python.exe" (
    echo [OK] Virtual environment already exists.
) else (
    echo [..] Creating virtual environment...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created.
)

:: -------------------------------------------
:: 3. Install dependencies
:: -------------------------------------------
echo [..] Installing dependencies (this may take a minute)...
venv\Scripts\pip install -e . --quiet
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b 1
)
echo [OK] Dependencies installed.

:: -------------------------------------------
:: 4. Set up .env file
:: -------------------------------------------
if exist ".env" (
    echo [OK] .env file already exists, skipping API key setup.
) else (
    echo.
    echo --- API Key Setup ---
    echo.
    echo An Anthropic API key is required for AI features.
    echo Get one at: https://console.anthropic.com/settings/keys
    echo.
    set /p "API_KEY=Enter your ANTHROPIC_API_KEY (or press Enter to skip): "
    echo.

    echo A Brave Search API key is optional (enables web search).
    echo Get one at: https://brave.com/search/api/
    echo.
    set /p "BRAVE_KEY=Enter your BRAVE_API_KEY (or press Enter to skip): "
    echo.

    (
        echo ANTHROPIC_API_KEY=!API_KEY!
        if not "!BRAVE_KEY!"=="" echo BRAVE_API_KEY=!BRAVE_KEY!
    ) > .env

    if "!API_KEY!"=="" (
        echo [WARN] No API key set. You can add it later in the .env file.
    ) else (
        echo [OK] .env file created.
    )
)

:: -------------------------------------------
:: 5. Check for Node.js (optional)
:: -------------------------------------------
where npx >nul 2>nul
if %errorlevel% neq 0 (
    echo.
    echo [NOTE] Node.js was not found. MCP tool servers (filesystem, web search)
    echo        require Node.js. The app will still work without it.
    echo        Install from: https://nodejs.org
) else (
    echo [OK] Node.js found.
)

:: -------------------------------------------
:: 6. Done - offer to launch
:: -------------------------------------------
echo.
echo ============================================
echo   Setup complete!
echo ============================================
echo.
echo You can start the app anytime by double-clicking launch.bat
echo.
set /p "LAUNCH=Launch the app now? (Y/n): "
if /i "!LAUNCH!"=="n" (
    echo.
    echo Done. Run launch.bat when you're ready.
    pause
    exit /b 0
)

echo.
echo Starting Clinical Research Assistant...
start "" "venv\Scripts\pythonw.exe" -m src.main
