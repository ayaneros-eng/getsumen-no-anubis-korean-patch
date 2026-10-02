@echo off
setlocal
if "%~1"=="" (
  echo Drag a supported ROM onto this file.
  pause
  exit /b 1
)
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0apply_patch.ps1" -SourceRom "%~f1"
if errorlevel 1 (
  echo Patch failed. Read the message above.
  pause
  exit /b 1
)
echo Patch verified successfully.
pause
