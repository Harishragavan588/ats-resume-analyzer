@echo off
title ATS Resume Analyzer
cd /d C:\ATS_Analyzer
call venv\Scripts\activate.bat
echo.
echo  ====================================
echo   ATS Resume Analyzer is starting...
echo  ====================================
echo  Open browser at: http://127.0.0.1:5000
echo.
start "" http://127.0.0.1:5000
python app.py
pause
