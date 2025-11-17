@echo off
setlocal EnableDelayedExpansion

REM Change directory to batch script path
cd /d "%~dp0"

REM Define supported Python versions X.Y.Z for easy future updates
set SUPPORTED_MIN_VERSION=3.10
set SUPPORTED_MAX_VERSION=3.11.9

REM Try to find a supported Python version using py launcher (prefer 3.11, then 3.10)
set PYTHON_CMD=
set PYTHON_VERSION_FOUND=
set USE_PY_LAUNCHER=0

for /f "tokens=*" %%I in ('py -3.11 --version 2^>nul') do (
    set PYTHON_CMD=py -3.11
    set PYTHON_VERSION_FOUND=3.11
    set USE_PY_LAUNCHER=1
)
if not defined PYTHON_CMD (
    for /f "tokens=*" %%I in ('py -3.10 --version 2^>nul') do (
        set PYTHON_CMD=py -3.10
        set PYTHON_VERSION_FOUND=3.10
        set USE_PY_LAUNCHER=1
    )
)

REM If py launcher didn't work, try direct python commands
if not defined PYTHON_CMD (
    for /f "tokens=2 delims= " %%I in ('python --version 2^>nul') do (
        set PYTHON_VERSION=%%I
        for /f "tokens=1-2 delims=." %%a in ("!PYTHON_VERSION!") do (
            if "%%a"=="3" (
                if "%%b"=="10" (
                    set PYTHON_CMD=python
                    set PYTHON_VERSION_FOUND=3.10
                    set USE_PY_LAUNCHER=0
                )
                if "%%b"=="11" (
                    set PYTHON_CMD=python
                    set PYTHON_VERSION_FOUND=3.11
                    set USE_PY_LAUNCHER=0
                )
            )
        )
    )
)

REM If still not found, try to install via winget
if not defined PYTHON_CMD (
    echo.
    echo Python %SUPPORTED_MIN_VERSION% or %SUPPORTED_MAX_VERSION% is not installed.
    echo.
    
    REM Check if winget is available
    where winget >nul 2>&1
    if %errorlevel% equ 0 (
        echo Attempting to install Python 3.11 via winget...
        echo This will install Python 3.11 system-wide, but we'll use it only in the virtual environment.
        echo.
        winget install Python.Python.3.11 --silent --accept-package-agreements --accept-source-agreements
        if %errorlevel% equ 0 (
            echo.
            echo Python 3.11 installed successfully. Refreshing Python launcher...
            REM Refresh py launcher
            py -0
            REM Try again
            for /f "tokens=*" %%I in ('py -3.11 --version 2^>nul') do (
                set PYTHON_CMD=py -3.11
                set PYTHON_VERSION_FOUND=3.11
                set USE_PY_LAUNCHER=1
            )
        ) else (
            echo.
            echo Winget installation failed. Trying Python 3.10...
            winget install Python.Python.3.10 --silent --accept-package-agreements --accept-source-agreements
            if %errorlevel% equ 0 (
                echo.
                echo Python 3.10 installed successfully. Refreshing Python launcher...
                py -0
                for /f "tokens=*" %%I in ('py -3.10 --version 2^>nul') do (
                    set PYTHON_CMD=py -3.10
                    set PYTHON_VERSION_FOUND=3.10
                    set USE_PY_LAUNCHER=1
                )
            )
        )
    )
)

REM Check if we found a supported Python version
if not defined PYTHON_CMD (
    call :error "Python %SUPPORTED_MIN_VERSION% or %SUPPORTED_MAX_VERSION% is not installed and could not be auto-installed.^
Please install Python %SUPPORTED_MIN_VERSION% or %SUPPORTED_MAX_VERSION% manually from https://www.python.org/downloads/"
    exit /b
)

REM Get the actual version for display
if !USE_PY_LAUNCHER! equ 1 (
    for /f "tokens=2 delims= " %%I in ('"!PYTHON_CMD!" --version 2^>nul') do set PYTHON_VERSION=%%I
) else (
    for /f "tokens=2 delims= " %%I in ('%PYTHON_CMD% --version 2^>nul') do set PYTHON_VERSION=%%I
)

echo.
echo Found Python version: !PYTHON_VERSION!
echo.
set VENV_NAME=venv
if not exist venv goto create_venv
echo Virtual environment already exists. Recreating with correct Python version...
echo Renaming old virtual environment...
if exist venv_old rmdir /s /q venv_old 2>nul
ren venv venv_old 2>nul
if exist venv\Scripts\activate.bat (
    echo Warning: Could not rename old venv (may be in use). Creating new venv with temporary name...
    set VENV_NAME=venv_new
)
:create_venv
echo Creating virtual environment with Python version !PYTHON_VERSION!
if !USE_PY_LAUNCHER! equ 1 (
    !PYTHON_CMD! -m venv !VENV_NAME!
) else (
    %PYTHON_CMD% -m venv !VENV_NAME!
)
if !errorlevel! neq 0 (
    call :error "Failed to create virtual environment. Please check the output above for more details."
    exit /b
)

REM If we created venv_new, rename it to venv and clean up old one
if exist venv_new\Scripts\activate.bat (
    echo Replacing old virtual environment...
    if exist venv_old rmdir /s /q venv_old 2>nul
    if exist venv\Scripts\activate.bat ren venv venv_old 2>nul
    ren venv_new venv 2>nul
    if exist venv_old (
        echo Cleaning up old virtual environment in background...
        start /b "" cmd /c "timeout /t 3 /nobreak >nul && rmdir /s /q venv_old"
    )
)

REM Activate virtual environment and install requirements
echo.
echo Activating virtual environment and installing requirements...
call "venv\Scripts\activate.bat"
if !errorlevel! neq 0 (
    call :error "Failed to activate virtual environment."
    exit /b
)

REM Verify we're using the correct Python version in venv
for /f "tokens=2 delims= " %%I in ('python --version 2^>nul') do set VENV_PYTHON_VERSION=%%I
echo.
echo Virtual environment is using Python !VENV_PYTHON_VERSION!
echo.

REM Upgrade pip in venv
python -m pip install --upgrade pip --quiet
if !errorlevel! neq 0 (
    call :error "Failed to upgrade pip. Please check the output above for more details."
    exit /b
)

REM Install requirements
echo Installing requirements...
pip install -r requirements.txt
if !errorlevel! neq 0 (
    call :error "There was an error installing the requirements. Please check the output above for more details."
    exit /b
)

REM Success
echo.
echo.
echo.
echo.
echo.
echo.
echo Requirements were successfully installed in virtual environment.
echo Virtual environment uses Python !VENV_PYTHON_VERSION! (isolated from system Python).
echo Use START.bat to start the application.
echo.
echo.
echo.
echo Press any key to exit...
pause >nul
exit /b

REM Display error message
:error
echo.
echo.
echo.
echo.
echo.
echo.
echo %~1
echo.
echo.
echo.
echo Press any key to exit...
pause >nul
goto :eof
