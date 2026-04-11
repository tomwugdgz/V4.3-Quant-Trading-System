@echo off
REM V4.3 自动交易监控启动脚本
REM 创建：2026-04-10

echo ================================================================================
echo V4.3 自动交易监控启动
echo ================================================================================
echo.

cd /d "%~dp0"

echo [启动] 自动交易监控（每 60 分钟扫描）
echo [模式] 自动执行交易（无需确认）
echo [日志] %CD%\paper_trading_logs\
echo.
echo 按 Ctrl+C 停止监控
echo.

start "监控仪表板" cmd /k "cd /d %~dp0 && python monitor_dashboard.py"
timeout /t 3 /nobreak >nul

python paper_trading_monitor.py --interval 60 --auto-trade

pause
