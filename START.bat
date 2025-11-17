@echo off
:: Change directory to batch script path
cd /d "%~dp0"

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo Virtual environment not found. Please run INSTALL.bat first.
    pause
    exit /b 1
)

REM Activate virtual environment
call "venv\Scripts\activate.bat"
if %errorlevel% neq 0 (
    echo Failed to activate virtual environment.
    pause
    exit /b 1
)

REM Run the main script
python "main.py"
pause
