@echo off
cd /d "%~dp0"
py -3.13 --version >nul 2>&1
if errorlevel 1 (python preparar.py) else (py -3.13 preparar.py)
pause
