@echo off
REM V4.3 交易系统 - 快速启动脚本
REM 创建：2026-04-10

echo ================================================================================
echo V4.3 交易系统 - 快速启动
echo ================================================================================
echo.

REM 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请先安装 Python 3.8+
    pause
    exit /b 1
)

echo [检查] Python 已安装
echo.

REM 检查依赖
echo [检查] 依赖包...
python -c "import pandas" >nul 2>&1
if errorlevel 1 (
    echo [安装] pandas...
    pip install pandas
)

python -c "import numpy" >nul 2>&1
if errorlevel 1 (
    echo [安装] numpy...
    pip install numpy
)

python -c "import MetaTrader5" >nul 2>&1
if errorlevel 1 (
    echo [安装] MetaTrader5...
    pip install MetaTrader5
)

echo [完成] 依赖检查
echo.

REM 运行测试
echo ================================================================================
echo 选择运行模式:
echo.
echo 1. 测试 Market Regime
echo 2. 测试 Factor Score
echo 3. 测试 Risk Agent
echo 4. 运行完整扫描（不执行）
echo 5. 运行完整扫描 + 自动执行
echo 6. 生成每日复盘报告
echo.
set /p choice="请输入选择 (1-6): "

if "%choice%"=="1" (
    echo.
    echo [运行] Market Regime 测试...
    cd v4_3
    python market_regime.py
) else if "%choice%"=="2" (
    echo.
    echo [运行] Factor Score 测试...
    cd v4_3
    python factor_score.py
) else if "%choice%"=="3" (
    echo.
    echo [运行] Risk Agent 测试...
    cd v4_3
    python risk_agent.py
) else if "%choice%"=="4" (
    echo.
    echo [运行] 市场扫描...
    cd v4_3
    python main_v43.py
) else if "%choice%"=="5" (
    echo.
    echo [运行] 自动交易...
    echo [警告] 即将执行真实交易！
    set /p confirm="确认执行？(y/n): "
    if "%confirm%"=="y" (
        cd v4_3
        python main_v43.py --auto-execute
    ) else (
        echo [取消] 已停止执行
    )
) else if "%choice%"=="6" (
    echo.
    echo [运行] 每日复盘...
    cd v4_3
    python review_agent.py
) else (
    echo.
    echo [错误] 无效选择
)

echo.
echo ================================================================================
echo 完成
echo ================================================================================
pause
