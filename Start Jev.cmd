@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>&1
if not errorlevel 1 (
  py -3 scripts/start_jev.py %*
  goto finished
)
where python >nul 2>&1
if not errorlevel 1 (
  python scripts/start_jev.py %*
  goto finished
)
set "LN_PYTHON=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if exist "%LN_PYTHON%" (
  "%LN_PYTHON%" scripts/start_jev.py %*
) else (
  echo Python was not found. Install Python 3 to open the LN with Jev.
)
:finished
pause
