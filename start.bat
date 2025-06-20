@echo off
echo Starting Zapret Manager...
echo.

REM Проверяем, установлен ли Python
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.8+ and try again
    pause
    exit /b 1
)

REM Запускаем приложение
cd /d "%~dp0"
python src/main.py

if errorlevel 1 (
    echo Error: Failed to start application
    pause
    exit /b 1
)

echo Application closed 