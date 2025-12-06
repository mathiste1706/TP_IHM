@echo off
setlocal enabledelayedexpansion

echo =====================================================
echo DETECTING PYTHON 3.12
echo =====================================================

REM Check if Python 3.12 is installed
py -3.12 --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python 3.12 not found! Please install Python 3.12.
    pause
    exit /b 1
)

REM Create venv if missing
if not exist "venv\Scripts\python.exe" (
    echo Creating virtual environment with Python 3.12...
    py -3.12 -m venv venv
)

echo Using Python in venv:
venv\Scripts\python.exe --version

venv\Scripts\python.exe -m pip install --upgrade pip setuptools wheel


if exist requirements.txt (
    venv\Scripts\python.exe -m pip install -r requirements.txt
)

echo =====================================================
echo LAUNCHING ALL PROGRAMS
echo =====================================================

REM Set venv python executable variable
set PYTHON_EXE=venv\Scripts\python.exe


echo Starting SRA...
start "SRA" "sra5\sra5_on.bat"

REM --- Start PPILOT5 ---
echo Starting PPILOT5...
start "PPILOT5" "ppilot5_3.3\ppilot5.exe"


echo Starting Processing Palette...
start "" /D "%CD%\Palette\windows-amd64" "Palette.exe"


echo Starting GESTURE (multi_strokes)...
start "GESTURE" %PYTHON_EXE% forme_multistroke.py

timeout /t 2 /nobreak >nul

REM --- Start Visionneur ---
echo Starting VISIONNEUR...
start "VISIONNEUR" "visionneur_1_2\visonneur.bat"

REM --- Start Python: Moteur ---
echo Starting MOTEUR...
start "MOTEUR" %PYTHON_EXE% Moteur.py

echo =====================================================
echo All systems launched!
echo =====================================================
pause
