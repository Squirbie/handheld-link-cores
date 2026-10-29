@echo off
rem Double-click on Windows: runs update-card-windows.ps1 from this folder (unzip card-update.zip first).
setlocal
set "HB_PS1=%~dp0update-card-windows.ps1"
if not exist "%HB_PS1%" (
  echo update-card-windows.ps1 not found. Extract card-update.zip first, then run this again.
  pause
  exit /b 1
)
set PSModulePath=
powershell -NoProfile -ExecutionPolicy Bypass -Command "& ([scriptblock]::Create([IO.File]::ReadAllText($env:HB_PS1, [Text.Encoding]::UTF8)))"
echo.
pause
