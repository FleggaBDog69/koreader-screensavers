@echo off
REM Double-click launcher for Windows: opens the studio terminal UI.
REM Checks for Python first (the studio is a Python program, so it can't
REM install Python from inside itself) and offers to install it via winget.
cd /d "%~dp0"

where python >nul 2>&1
if errorlevel 1 (
  echo   Python isn't installed - the studio needs it to run.
  echo.
  where winget >nul 2>&1
  if errorlevel 1 (
    echo   Get Python from https://python.org and tick "Add to PATH".
    pause
    exit /b 1
  )
  set /p ans="  Install Python now with winget? [Y/n] "
  if /I "%ans%"=="n" (
    echo   Get Python from https://python.org and tick "Add to PATH".
    pause
    exit /b 1
  )
  winget install -e --id Python.Python.3.13
  echo.
  echo   Python installed. Close this window and re-open screensaver.bat.
  pause
  exit /b
)

python screensaver.py
pause
