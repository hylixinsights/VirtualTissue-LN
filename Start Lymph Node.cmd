@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>&1
if not errorlevel 1 (
  py -3 server.py --port 8010 --cells 120 --open-browser
  goto finished
)
where python >nul 2>&1
if not errorlevel 1 (
  python server.py --port 8010 --cells 120 --open-browser
  goto finished
)
set "LN_PYTHON=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if exist "%LN_PYTHON%" (
  "%LN_PYTHON%" server.py --port 8010 --cells 120 --open-browser
) else (
  echo Python was not found. Install Python 3 to open the local studio.
)
:finished
pause
