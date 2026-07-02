@echo off
echo ===================================================
echo   Historic Heights YouTube Analytics Scheduler Setup
echo ===================================================
echo.
echo Registering daily task to run fetch_daily.py every day at 9:00 PM...
echo.

set TASK_NAME="HistoricHeightsDailyAnalytics"
set SCRIPT_PATH="%~dp0fetch_daily.py"

schtasks /create /tn %TASK_NAME% /tr "python %SCRIPT_PATH%" /sc daily /st 21:00 /f

if %ERRORLEVEL% EQU 0 (
    echo.
    echo [SUCCESS] Task %TASK_NAME% has been scheduled successfully to run at 9:00 PM daily.
) else (
    echo.
    echo [ERROR] Failed to schedule task. Please run this script as Administrator.
)

pause
