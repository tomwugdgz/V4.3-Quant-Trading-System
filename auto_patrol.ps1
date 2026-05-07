# auto_patrol.ps1 — 持续自动巡查，每30分钟运行一次patrol.py
# 设置为Windows计划任务，开机自启
param(
    [int]$IntervalMinutes = 30,
    [int]$MaxRuns = -1    # -1 = 无限循环
)

$PY312 = "C:\Users\DELL\AppData\Local\Programs\Python\Python312\python.exe"
$PATROL = "C:\Users\DELL\.openclaw-autoclaw\workspace\trading\patrol.py"
$LOG_DIR = "D:\LLM-Wiki\trading\logs"
$env:PYTHONIOENCODING = "utf-8"
$env:Path = "C:\Users\DELL\AppData\Local\Programs\Python\Python312;C:\Users\DELL\AppData\Local\Programs\Python\Python312\Scripts;$env:Path"

# 日志函数
function Write-Log {
    param([string]$msg, [string]$level = "INFO")
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "$ts [$level] $msg" | Tee-Object -FilePath "$LOG_DIR\auto_patrol.log" -Append
}

# 确保日志目录存在
if (-not (Test-Path $LOG_DIR)) { New-Item -ItemType Directory -Path $LOG_DIR -Force | Out-Null }

$runCount = 0
$running = $true

# Ctrl+C 处理
$sigHandler = [Console]::TreatControlCAsInput
[Console]::TreatControlCAsInput = $true

Write-Log "=========================================="
Write-Log "Auto Patrol 启动 (间隔 ${IntervalMinutes}min)"
Write-Log "=========================================="

while ($running -and ($MaxRuns -lt 0 -or $runCount -lt $MaxRuns)) {
    $runCount++
    $cycleStart = Get-Date

    # 检查是否收到 Ctrl+C
    if ([Console]::KeyAvailable) {
        $key = [Console]::ReadKey($true)
        if ($key.Key -eq [ConsoleKey]::C -and $key.Modifiers -eq [ConsoleModifiers]::Control) {
            Write-Log "收到 Ctrl+C，停止巡查"
            break
        }
    }

    Write-Log "=== 第 ${runCount} 次巡查 ==="

    # 1. 检查 MT5 连接
    $checkResult = & $PY312 -Command @"
import MetaTrader5 as mt5, sys, json
if not mt5.initialize(login=52797683, server='ICMarketsSC-Demo', timeout=10000):
    print('MT5_OFFLINE')
    sys.exit()
info = mt5.account_info()
positions = mt5.positions_get() or []
print(json.dumps({
    'status': 'online',
    'balance': float(info.balance),
    'equity': float(info.equity),
    'pos_count': len(positions)
}, ensure_ascii=False))
mt5.shutdown()
"@ 2>&1

    if ($checkResult -match "MT5_OFFLINE") {
        Write-Log "MT5 离线，等待下次巡查" "WARN"
        Start-Sleep -Seconds ($IntervalMinutes * 60)
        continue
    }

    # 2. 运行 patrol.py
    $patrolStart = Get-Date
    Write-Log "启动 patrol.py..."
    $patrolResult = & $PY312 $PATROL 2>&1
    $patrolEnd = Get-Date
    $patrolDuration = ($patrolEnd - $patrolStart).TotalSeconds

    # 3. 解析 patrol 输出，提取关键信息
    $lines = $patrolResult -split "`n" | Where-Object { $_.Trim() -ne "" }
    $hasSignal = $false
    $tradeExecuted = $false
    $positionCount = 0
    $balance = 0
    $equity = 0

    foreach ($line in $lines) {
        if ($line -match "余额=\$?([\d\.]+)") { $balance = [double]$Matches[1] }
        if ($line -match "净值=\$?([\d\.]+)") { $equity = [double]$Matches[1] }
        if ($line -match "持仓:?\s*(\d+)") { $positionCount = [int]$Matches[1] }
        if ($line -match "强信号") { $hasSignal = $true }
        if ($line -match "成功开仓") { $tradeExecuted = $true; Write-Log "开仓通知: $($line.Trim())" "TRADE" }
        if ($line -match "失败") { Write-Log "错误: $($line.Trim())" "ERROR" }
    }

    # 4. 记录到日志
    $duration = "$([Math]::Round($patrolDuration, 1))s"
    if ($tradeExecuted) {
        Write-Log "持仓:$positionCount/5 余额:\$${balance} 净值:\$${equity} [交易执行] (${duration})" "TRADE"
    } elseif ($hasSignal) {
        Write-Log "持仓:$positionCount/5 余额:\$${balance} 净值:\$${equity} [有信号待查] (${duration})" "WARN"
    } else {
        Write-Log "持仓:$positionCount/5 余额:\$${balance} 净值:\$${equity} [无信号] (${duration})" "INFO"
    }

    # 5. 如果有交易执行，额外记录 trade log
    if ($tradeExecuted) {
        $tradeLog = "$LOG_DIR\trade_log_$(Get-Date -Format 'yyyy-MM-dd').json"
        $tradeEntry = @{
            timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
            event = "patrol_trade"
            balance = $balance
            equity = $equity
            positions = $positionCount
            duration_seconds = [Math]::Round($patrolDuration, 1)
            raw_output = ($patrolResult -join "`n") -replace '`n', ' | '
        } | ConvertTo-Json -Compress

        if (Test-Path $tradeLog) {
            Add-Content -Path $tradeLog -Value $tradeEntry
        } else {
            "@{ `"date`"=`"$(Get-Date -Format 'yyyy-MM-dd')`"; `"trades`"=[] }" | Set-Content $tradeLog
            Add-Content -Path $tradeLog -Value $tradeEntry
        }
    }

    # 6. 等待下次巡查（精确计时）
    $elapsed = ((Get-Date) - $cycleStart).TotalSeconds
    $waitSeconds = [Math]::Max(0, ($IntervalMinutes * 60) - $elapsed)
    Write-Log "下次巡查: $(Get-Date).AddSeconds($waitSeconds).ToString('HH:mm:ss') (等待 ${waitSeconds}s)"

    if ($waitSeconds -gt 0) {
        Start-Sleep -Seconds $waitSeconds
    }
}

Write-Log "Auto Patrol 已停止 (共运行 ${runCount} 次)"
