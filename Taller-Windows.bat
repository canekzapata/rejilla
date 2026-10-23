@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (echo Abre primero Preparar-Windows.bat & pause & exit /b 1)
".venv\Scripts\python.exe" "python\ventana.py"
if errorlevel 1 pause
