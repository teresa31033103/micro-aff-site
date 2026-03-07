@echo off
setlocal EnableExtensions
cd /d "%~dp0"

if "%~1"=="" (
  echo Examples:
  echo   launch.cmd --dry-run
  echo   launch.cmd --push
  echo   launch.cmd --all --push
  echo.
)

where python >nul 2>nul
if errorlevel 1 (
  echo [ERROR] python was not found.
  exit /b 1
)

python scripts\run_pipeline.py %*
set "EXITCODE=%ERRORLEVEL%"

echo.
if "%EXITCODE%"=="0" (
  echo Done.
) else (
  echo [ERROR] Pipeline failed. Check the log above.
)
exit /b %EXITCODE%
