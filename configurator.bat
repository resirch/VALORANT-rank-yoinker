@echo off
:: Change directory to batch script path
cd /d "%~dp0"

REM Try executable first
"vRY.exe" --config 2>nul
if %ERRORLEVEL% EQU 0 exit /b 0

REM Executable failed, try Python with venv
color 0C
echo Executable failed, trying Python with virtual environment...

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo Virtual environment not found. Trying system Python...
    python main.py --config 2>nul
    if %ERRORLEVEL% NEQ 0 (
        echo Python also failed!
        echo Try running INSTALL.bat to set up the virtual environment.
        pause >nul
    )
    exit /b
)

REM Activate virtual environment
call "venv\Scripts\activate.bat"
if %errorlevel% neq 0 (
    echo Failed to activate virtual environment. Trying system Python...
    python main.py --config 2>nul
    if %ERRORLEVEL% NEQ 0 (
        echo Python also failed!
        echo Try running INSTALL.bat to set up the virtual environment.
        pause >nul
    )
    exit /b
)

REM Run with venv Python
python main.py --config 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Python also failed!
    echo Try running INSTALL.bat to set up the virtual environment.
    pause >nul
)
