@echo off
setlocal
cd /d "%~dp0"

if exist ".venv\Scripts\pythonw.exe" (
    start "" ".venv\Scripts\pythonw.exe" "Sahayak AI.pyw"
    exit /b 0
)

if exist ".venv\Scripts\python.exe" (
    start "" ".venv\Scripts\python.exe" "Sahayak AI.pyw"
    exit /b 0
)

where pyw >nul 2>nul
if %errorlevel%==0 (
    start "" pyw "Sahayak AI.pyw"
    exit /b 0
)

where py >nul 2>nul
if %errorlevel%==0 (
    start "" py -3 "Sahayak AI.pyw"
    exit /b 0
)

where pythonw >nul 2>nul
if %errorlevel%==0 (
    start "" pythonw "Sahayak AI.pyw"
    exit /b 0
)

python "main.py"
