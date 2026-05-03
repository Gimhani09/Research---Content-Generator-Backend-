@echo off
echo ================================
echo  Content Generator Server
echo ================================
echo.
echo Starting server with venv Python 3.10...
echo.

set VENV_PYTHON=%~dp0.venv\Scripts\python.exe

if not exist "%VENV_PYTHON%" (
    echo ERROR: venv not found at %VENV_PYTHON%
    echo Please run: python -m venv .venv  then  .venv\Scripts\pip install -r requirements.txt
    pause
    exit /b 1
)

"%VENV_PYTHON%" main.py
pause
