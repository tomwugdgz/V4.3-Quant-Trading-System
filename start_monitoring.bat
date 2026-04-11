@echo off
chcp 65001 >nul
echo Starting 72h Trading Monitor...
echo Start time: %date% %time%

:loop
echo.
echo ========================================
echo Running monitor at %date% %time%
echo ========================================

"C:\Users\Dell\AppData\Local\Programs\Python\Python37\python.exe" "C:\Users\DELL\.openclaw-autoclaw\workspace\trading\simple_monitor.py" > "C:\Users\DELL\.openclaw-autoclaw\workspace\trading\72h_reports\monitor_output.txt" 2>&1

type "C:\Users\DELL\.openclaw-autoclaw\workspace\trading\72h_reports\monitor_output.txt"

echo.
echo Next check in 60 minutes...
echo.

REM Wait 60 minutes (3600 seconds)
timeout /t 3600 /nobreak >nul

goto loop
