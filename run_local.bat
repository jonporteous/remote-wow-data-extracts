@echo off
setlocal enabledelayedexpansion
title Datamars -- Remote WOW Local File Report
cd /d "%~dp0"

:: ---------------------------------------------------------------
:: Check Python
:: ---------------------------------------------------------------
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo  ERROR: Python is not installed or not found in PATH.
    echo  Install from https://www.python.org
    echo.
    pause
    exit /b 1
)

:: ---------------------------------------------------------------
:: Ensure required packages are installed
:: ---------------------------------------------------------------
python -c "import matplotlib" >nul 2>&1
if errorlevel 1 (
    echo  Installing matplotlib...
    pip install matplotlib --quiet
)
python -c "import pandas" >nul 2>&1
if errorlevel 1 (
    echo  Installing pandas...
    pip install pandas openpyxl --quiet
)
python -c "import openpyxl" >nul 2>&1
if errorlevel 1 (
    echo  Installing openpyxl...
    pip install openpyxl --quiet
)

:: ---------------------------------------------------------------
:: Ensure Input folder exists
:: ---------------------------------------------------------------
if not exist "Input\" (
    mkdir "Input"
    echo.
    echo  Created Input\ folder.
)

:: ---------------------------------------------------------------
:: Main loop
:: ---------------------------------------------------------------
:MAIN_MENU
cls
echo.
echo  ================================================================
echo   DATAMARS -- Remote Walkover Weighing
echo   Local File Report Generator  (no API required)
echo  ================================================================
echo.
echo  Place your device CSV exports or PPL Upload xlsx files in:
echo.
echo    %~dp0Input\
echo.
echo  Supported file types:
echo    - "[IMEI] exported weightdata data.csv"  (direct device export)
echo    - "PPL Upload*.xlsx"                      (PPL Upload spreadsheet)
echo.
echo  Processed files are automatically moved to Input\Processed\
echo  ----------------------------------------------------------------
echo.

:: Check if Input folder has any files
set FILE_COUNT=0
for %%F in ("Input\*.csv" "Input\*.xlsx") do set /a FILE_COUNT+=1

if !FILE_COUNT! == 0 (
    echo  No files found in Input\ folder.
    echo  Please copy your data files there and press any key to retry.
    echo.
    pause
    goto MAIN_MENU
)

echo  Found !FILE_COUNT! file(s) in Input\.
echo.

python analyse_wow.py --input-dir Input
set EXIT_CODE=!errorlevel!

if !EXIT_CODE! neq 0 (
    echo.
    echo  ----------------------------------------------------------------
    echo   Report could not be generated. See error above.
    echo.
    echo   Common causes:
    echo     - No supported weight data files in Input\ folder
    echo     - File format not recognised
    echo     - No weight readings in the selected files
    echo  ----------------------------------------------------------------
    echo.
    pause
    goto MAIN_MENU
)

:: ---------------------------------------------------------------
:: Open the latest HTML report
:: ---------------------------------------------------------------
set LATEST_DIR=
for /d %%D in ("Output\*") do set LATEST_DIR=%%D

if defined LATEST_DIR (
    set HTML_FILE=
    for %%F in ("!LATEST_DIR!\*.html") do set HTML_FILE=%%F
    if defined HTML_FILE (
        echo.
        echo  Opening report in browser...
        start "" "!HTML_FILE!"
    )
)

:: ---------------------------------------------------------------
:: Done
:: ---------------------------------------------------------------
echo.
echo  ================================================================
echo   Done.
echo  ================================================================
echo.
if defined LATEST_DIR echo   Saved to: !LATEST_DIR!
echo.
set GO_AGAIN=
set /p GO_AGAIN="  Run another report? (Y/N): "
if /i "!GO_AGAIN!"=="Y" goto MAIN_MENU

echo.
echo  Goodbye.
timeout /t 2 >nul
