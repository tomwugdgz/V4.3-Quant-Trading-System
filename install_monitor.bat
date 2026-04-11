@echo off
echo Creating scheduled task for MT5 Auto Monitor...
schtasks /create /tn "MT5-AutoMonitor" /tr "py -3 C:\Users\DELL\.openclaw-autoclaw\workspace\trading\auto_monitor.py" /sc minute /mo 15 /ru SYSTEM /f
echo.
echo Done! Task created.
echo.
echo View task: schtasks /query /tn "MT5-AutoMonitor"
echo Run now: schtasks /run /tn "MT5-AutoMonitor"
echo Delete task: schtasks /delete /tn "MT5-AutoMonitor" /f
pause
