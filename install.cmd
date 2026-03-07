@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

set "USERNAME_ARG=%~1"
set "REPO_ARG=%~2"
set "MODEL_ARG=%~3"
if "%REPO_ARG%"=="" set "REPO_ARG=micro-aff-site"
if "%MODEL_ARG%"=="" set "MODEL_ARG=llama3.2"
set "SITE_DOMAIN="
if not "%USERNAME_ARG%"=="" set "SITE_DOMAIN=%USERNAME_ARG%.github.io/%REPO_ARG%"

echo ================================================
echo micro-aff-site install
echo ================================================
echo.

where python >nul 2>nul
if errorlevel 1 (
  echo [ERROR] python was not found.
  echo Install Python 3.10+ and run this again.
  exit /b 1
)

where git >nul 2>nul
if errorlevel 1 (
  echo [ERROR] git was not found.
  echo Install Git for Windows and run this again.
  exit /b 1
)

where ollama >nul 2>nul
if errorlevel 1 (
  echo [ERROR] ollama was not found.
  echo Install it from https://ollama.com/download/windows
  exit /b 1
)

echo [1/5] Installing Python requirements...
python -m pip install --upgrade pip
if errorlevel 1 exit /b 1
python -m pip install -r requirements.txt
if errorlevel 1 exit /b 1

echo.
echo [2/5] Checking Ollama model...
ollama list | findstr /i /c:"%MODEL_ARG%" >nul
if errorlevel 1 (
  echo Model %MODEL_ARG% was not found. Running pull...
  ollama pull %MODEL_ARG%
  if errorlevel 1 (
    echo [ERROR] ollama pull %MODEL_ARG% failed.
    exit /b 1
  )
) else (
  echo Model %MODEL_ARG% is already available.
)

echo.
echo [3/5] Setting SITE_DOMAIN...
if "%SITE_DOMAIN%"=="" (
  echo GitHub username was not supplied, so automatic SITE_DOMAIN update is skipped.
  echo Example: install.cmd YOUR_GITHUB_USERNAME micro-aff-site llama3.2
) else (
  powershell -NoProfile -ExecutionPolicy Bypass -Command "$p='scripts/build_site.py'; $c=Get-Content -Raw $p; $c=[regex]::Replace($c,'SITE_DOMAIN = \"[^\"]+\"','SITE_DOMAIN = \"%SITE_DOMAIN%\"',1); Set-Content -Path $p -Value $c -Encoding UTF8"
  if errorlevel 1 (
    echo [ERROR] Failed to update SITE_DOMAIN in scripts/build_site.py
    exit /b 1
  )
  echo SITE_DOMAIN = %SITE_DOMAIN%
)

echo.
echo [4/5] Running initial build...
python scripts\build_site.py
if errorlevel 1 exit /b 1

echo.
echo [5/5] Done.
if "%SITE_DOMAIN%"=="" (
  echo Next steps:
  echo   1. Replace YOUR_AFFILIATE_LINK_HERE in data\affiliate_map.json
  echo   2. Run install.cmd again with your GitHub username, or edit SITE_DOMAIN in scripts\build_site.py
  echo   3. Push to GitHub and set Pages source to GitHub Actions
) else (
  echo Next steps:
  echo   1. Replace YOUR_AFFILIATE_LINK_HERE in data\affiliate_map.json
  echo   2. Push to GitHub and set Pages source to GitHub Actions
  echo   3. Run launch.cmd --dry-run
)

echo.
exit /b 0
