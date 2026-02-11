@echo off
:: Clinical Research Assistant Launcher
:: Double-click this file to start the application.
:: Uses pythonw.exe so no console window stays open.

cd /d "%~dp0"
start "" "venv\Scripts\pythonw.exe" -m src.main
