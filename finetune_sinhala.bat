@echo off
REM Fine-tune mT5 for Sinhala/Code-Mixed Content Generation

echo.
echo ============================================================
echo    SINHALA CONTENT GENERATOR - FINE-TUNING
echo ============================================================
echo.

REM Activate virtual environment if it exists
if exist .venv\Scripts\activate.bat (
    echo Activating virtual environment...
    call .venv\Scripts\activate.bat
)

REM Run fine-tuning
python finetune_sinhala.py

echo.
echo ============================================================
echo Press any key to exit...
pause > nul
