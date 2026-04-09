@echo off
setlocal

:: Define the path to the virtual environment
set "VENV_DIR=%~dp0venv"

:: Check if the virtual environment exists
if not exist "%VENV_DIR%" (
    echo [dupeGuru] Creating virtual environment in %VENV_DIR%...
    python -m venv "%VENV_DIR%"
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment. 
        echo Ensure Python is installed and added to PATH.
        pause
        exit /b 1
    )
)

:: Activate the virtual environment
echo [dupeGuru] Activating virtual environment...
call "%VENV_DIR%\Scripts\activate"

:: Bootstrap the build tooling used by setup.py.
echo [dupeGuru] Updating pip, setuptools, and wheel...
python -m pip install --upgrade pip setuptools wheel
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install or upgrade pip/setuptools/wheel.
    pause
    exit /b 1
)

echo [dupeGuru] Checking and installing requirements...
python -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install requirements.
    pause
    exit /b 1
)

:: Run dupeGuru Flask Web App with Custom Watcher
echo [dupeGuru] Starting web application with watcher.py...
python watcher.py

if %errorlevel% neq 0 (
    echo [ERROR] dupeGuru watcher exited with code %errorlevel%.
    pause
)

endlocal
