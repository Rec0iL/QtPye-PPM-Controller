@echo off

REM Activate the virtual environment
call venv\Scripts\activate.bat

REM Run the Python application
python main.py

REM Deactivate the virtual environment and pause
call venv\Scripts\deactivate.bat
pause
