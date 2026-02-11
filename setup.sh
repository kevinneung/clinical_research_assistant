#!/usr/bin/env bash
# Clinical Research Assistant - First-Time Setup
# Run this script to set up everything and launch the app.
set -e

cd "$(dirname "$0")"

echo "============================================"
echo "  Clinical Research Assistant - Setup"
echo "============================================"
echo

# -------------------------------------------
# 1. Check for Python
# -------------------------------------------
PYTHON=""
if command -v python3 &>/dev/null; then
    PYTHON="python3"
elif command -v python &>/dev/null; then
    PYTHON="python"
else
    echo "[ERROR] Python was not found on your system."
    echo "Install Python 3.11+:"
    echo "  macOS:  brew install python@3.13"
    echo "  Ubuntu: sudo apt install python3 python3-venv"
    echo "  Fedora: sudo dnf install python3"
    exit 1
fi

# Verify Python version >= 3.11
PYVER=$($PYTHON --version 2>&1 | awk '{print $2}')
PYMAJOR=$(echo "$PYVER" | cut -d. -f1)
PYMINOR=$(echo "$PYVER" | cut -d. -f2)

if [ "$PYMAJOR" -lt 3 ] || { [ "$PYMAJOR" -eq 3 ] && [ "$PYMINOR" -lt 11 ]; }; then
    echo "[ERROR] Python 3.11+ is required. Found: $PYVER"
    exit 1
fi
echo "[OK] Python $PYVER found."

# -------------------------------------------
# 2. Create virtual environment
# -------------------------------------------
if [ -f "venv/bin/python" ]; then
    echo "[OK] Virtual environment already exists."
else
    echo "[..] Creating virtual environment..."
    $PYTHON -m venv venv
    echo "[OK] Virtual environment created."
fi

# -------------------------------------------
# 3. Install dependencies
# -------------------------------------------
echo "[..] Installing dependencies (this may take a minute)..."
venv/bin/pip install -e . --quiet
echo "[OK] Dependencies installed."

# -------------------------------------------
# 4. Set up .env file
# -------------------------------------------
if [ -f ".env" ]; then
    echo "[OK] .env file already exists, skipping API key setup."
else
    echo
    echo "--- API Key Setup ---"
    echo
    echo "An Anthropic API key is required for AI features."
    echo "Get one at: https://console.anthropic.com/settings/keys"
    echo
    read -p "Enter your ANTHROPIC_API_KEY (or press Enter to skip): " API_KEY
    echo

    echo "A Brave Search API key is optional (enables web search)."
    echo "Get one at: https://brave.com/search/api/"
    echo
    read -p "Enter your BRAVE_API_KEY (or press Enter to skip): " BRAVE_KEY
    echo

    echo "ANTHROPIC_API_KEY=$API_KEY" > .env
    if [ -n "$BRAVE_KEY" ]; then
        echo "BRAVE_API_KEY=$BRAVE_KEY" >> .env
    fi

    if [ -z "$API_KEY" ]; then
        echo "[WARN] No API key set. You can add it later in the .env file."
    else
        echo "[OK] .env file created."
    fi
fi

# -------------------------------------------
# 5. Check for Node.js (optional)
# -------------------------------------------
if ! command -v npx &>/dev/null; then
    echo
    echo "[NOTE] Node.js was not found. MCP tool servers (filesystem, web search)"
    echo "       require Node.js. The app will still work without it."
    echo "       Install from: https://nodejs.org"
    echo "       macOS: brew install node"
else
    echo "[OK] Node.js found."
fi

# -------------------------------------------
# 6. Done - offer to launch
# -------------------------------------------
echo
echo "============================================"
echo "  Setup complete!"
echo "============================================"
echo
echo "You can start the app anytime by running ./launch.sh"
echo
read -p "Launch the app now? (Y/n): " LAUNCH
if [ "$LAUNCH" = "n" ] || [ "$LAUNCH" = "N" ]; then
    echo
    echo "Done. Run ./launch.sh when you're ready."
    exit 0
fi

echo
echo "Starting Clinical Research Assistant..."
exec venv/bin/python -m src.main
