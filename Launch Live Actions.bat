@echo off
rem Live Actions. Uses the .venv that install.ps1 creates; falls back to a Python on PATH.
cd /d "%~dp0"
if exist "%~dp0.venv\Scripts\pythonw.exe" (
  start "" "%~dp0.venv\Scripts\pythonw.exe" "%~dp0app\shell.py"
  goto :end
)
where pyw >nul 2>nul
if %errorlevel%==0 (
  start "" pyw -3 "%~dp0app\shell.py"
  goto :end
)
where pythonw >nul 2>nul
if %errorlevel%==0 (
  start "" pythonw "%~dp0app\shell.py"
  goto :end
)
echo Live Actions is not installed yet.
echo Right-click install.ps1 and choose "Run with PowerShell", or see INSTALL.md.
pause
:end
