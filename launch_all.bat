@echo off
setlocal enabledelayedexpansion
echo Detecting Python and Processing...

REM =====================================================
REM  FIND PYTHON
REM =====================================================
set PYTHON_EXE="venv\Scripts\python.exe"

echo ====================================================
echo =     LAUNCHING FULL INTERACTION PIPELINE         =
echo ====================================================

echo.
echo --- Starting SRA ---
start "SRA" "sra5\sra5_on.bat"

echo --- Starting PPILOT5 ---
start "PPILOT5" "ppilot5_3.3\ppilot5.exe"

echo --- Starting Processing Palette ---
start "" /D "%CD%\Palette\windows-amd64" "Palette.exe"

echo --- Starting Python: multi_strockes ---
start "GESTURE" %PYTHON_EXE% forme_multistroke.py

timeout /t 2 /nobreak >nul
echo --- Starting Visionneur ---
start "VISIONNEUR" "visionneur_1_2\visonneur.bat"

echo --- Starting Python: Moteur ---
start "MOTEUR" %PYTHON_EXE% Moteur.py

echo.
echo All systems launched!
echo ====================================================
pause
