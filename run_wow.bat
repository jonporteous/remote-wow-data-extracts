@echo off
setlocal enabledelayedexpansion
title Datamars -- Remote WOW Data Report
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
python -c "import requests" >nul 2>&1
if errorlevel 1 (
    echo  Installing requests...
    pip install requests --quiet
)
python -c "import matplotlib" >nul 2>&1
if errorlevel 1 (
    echo  Installing matplotlib...
    pip install matplotlib --quiet
)
python -c "import pandas" >nul 2>&1
if errorlevel 1 (
    echo  Installing pandas (required for farm list^)...
    pip install pandas openpyxl --quiet
)
python -c "import openpyxl" >nul 2>&1
if errorlevel 1 (
    echo  Installing openpyxl (required for farm list^)...
    pip install openpyxl --quiet
)

:: ---------------------------------------------------------------
:: Main loop
:: ---------------------------------------------------------------
:MAIN_MENU
cls
echo.
echo  ================================================================
echo   DATAMARS -- Remote Walkover Weighing
echo   Weight ^& Growth Report Generator
echo  ================================================================
echo.
echo  NOTE: Your IP address must be whitelisted on the PPL server
echo  for the farm you are requesting. Disconnect any VPN first.
echo.
echo  ----------------------------------------------------------------
echo   Select date range:
echo  ----------------------------------------------------------------
echo.
echo    1.  Last  7 days
echo    2.  Last 14 days
echo    3.  Last 21 days
echo    4.  Custom date range
echo.
set DATE_CHOICE=
set /p DATE_CHOICE="  Enter choice (1-4): "

if "!DATE_CHOICE!"=="1" (
    set PYTHON_ARGS=--days 7
    set DATE_LABEL=Last 7 days
    goto RUN
)
if "!DATE_CHOICE!"=="2" (
    set PYTHON_ARGS=--days 14
    set DATE_LABEL=Last 14 days
    goto RUN
)
if "!DATE_CHOICE!"=="3" (
    set PYTHON_ARGS=--days 21
    set DATE_LABEL=Last 21 days
    goto RUN
)
if "!DATE_CHOICE!"=="4" (
    goto CUSTOM_DATE
)
echo.
echo  Invalid choice — please enter 1, 2, 3 or 4.
timeout /t 2 >nul
goto MAIN_MENU

:CUSTOM_DATE
echo.
set START_DATE=
set END_DATE=
set /p START_DATE="  Start date (YYYY-MM-DD): "
set /p END_DATE="    End date (YYYY-MM-DD): "
if "!START_DATE!"=="" goto DATE_ERROR
if "!END_DATE!"==""   goto DATE_ERROR
set PYTHON_ARGS=--start !START_DATE! --end !END_DATE!
set DATE_LABEL=!START_DATE! to !END_DATE!
goto RUN

:DATE_ERROR
echo.
echo  ERROR: Both start and end dates are required.
timeout /t 2 >nul
goto MAIN_MENU

:: ---------------------------------------------------------------
:: Run — Python handles farm list, paddock selection, fetch & report
:: ---------------------------------------------------------------
:RUN
echo.
echo  ================================================================
echo   Date range: !DATE_LABEL!
echo  ================================================================

python analyse_wow.py !PYTHON_ARGS!
set EXIT_CODE=!errorlevel!

if !EXIT_CODE! neq 0 (
    echo.
    echo  ----------------------------------------------------------------
    echo   Report could not be generated. See error above.
    echo.
    echo   Common causes:
    echo     - IP address not whitelisted for this farm on PPL server
    echo     - Incorrect farm selection
    echo     - VPN active ^(changes your IP address^)
    echo     - No data exists for the selected date range
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
