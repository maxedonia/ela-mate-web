@echo off
cd /d "%~dp0"

if not exist "venv\Scripts\activate" (
    echo Setting up virtual environment...
    python -m venv venv
    call venv\Scripts\activate
    echo Installing dependencies...
    pip install -r requirements.txt
) else (
    call venv\Scripts\activate
)

streamlit run app.py
pause