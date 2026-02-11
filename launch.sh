#!/usr/bin/env bash
# Clinical Research Assistant Launcher
# Run this script to start the application.
cd "$(dirname "$0")"
exec venv/bin/python -m src.main
