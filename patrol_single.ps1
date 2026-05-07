# patrol_single.ps1 — 单次巡查（供计划任务调用）
# 每次运行执行一次 patrol.py，记录结果到日志
param(
    [string]$LogDir = "D:\LLM-Wiki\trading\logs"
)

$PY312 = "C:\Users\DELL\AppData\Local\Programs\Python\Python312\python.exe"
$PATROL = "C:\Users\DELL\.openclaw-autoclaw\workspace\trading\patrol.py"
$TRADE_LOG = "$LogDir\trade_log_$(Get-Date -Format 'yyyy-MM-dd').json"
$PATROL_LOG = "$LogDir\patrol_log_$(Get-Date -Format 'yyyy-MM-dd').log"
$env:PYTHONIOENCODING = "utf-8"
$env:Path = "C:\Users\DELL\AppData\Local\Programs\Python\Python312;C:\Users\DELL\AppData\Local\Programs\Python\Python312\Scripts;$env:Path"

$ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
"$ts [PATROL] 开始巡查" | Out-File -FilePath $PATROL_LOG -Append -Encoding UTF8

# 1. 执行 patrol.py
$patrolResult = & $PY312 $PATROL 2>&1
$lines = $patrolResult -split "`n" | Where-Object { $_.Trim() -ne "" }

# 2. 解析结果
$balance = $null; $equity = $null; $posCount = 0
$tradeExecuted = $null; $signalInfo = $null

foreach ($line in $lines) {
    "$ts $line" | Out-File -FilePath $PATROL_LOG -Append -Encoding UTF8
    if ($line -match "余额=\$?([\d\.]+)") { $balance = [double]$Matches[1] }
    if ($line -match "净值=\$?([\d\.]+)") { $equity = [double]$Matches[1] }
    if ($line -match "持仓:?\s*(\d+)") { $posCount = [int]$Matches[1] }
    if ($line -match "强信号") { $signalInfo = $line.Trim() }
    if ($line -match "成功开仓") { $tradeExecuted = $true }
}

# 3. 写入 trade log
$tradeEntry = @{
    timestamp = $ts
    event = if ($tradeExecuted) { "trade_executed" } elseif ($signalInfo) { "signal_skipped" } else { "no_signal" }
    balance = $balance
    equity = $equity
    positions = $posCount
    signal = $signalInfo
} | ConvertTo-Json -Compress

# 追加到当日 JSON 日志
if (Test-Path $TRADE_LOG) {
    # 读取现有内容，追加
    try {
        $existing = Get-Content $TRADE_LOG -Raw -Encoding UTF8 | ConvertFrom-Json
        $existing.trades += $tradeEntry
        $existing | ConvertTo-Json -Compress | Set-Content $TRADE_LOG -Encoding UTF8
    } catch {
        "@{date='$(Get-Date -Format 'yyyy-MM-dd')'; trades=@($tradeEntry)}" | Set-Content $TRADE_LOG -Encoding UTF8
    }
} else {
    "@{date='$(Get-Date -Format 'yyyy-MM-dd')'; trades=@($tradeEntry)}" | Set-Content $TRADE_LOG -Encoding UTF8
}

"$ts [PATROL] 完成 (持仓:$posCount/5 余额:$balance)" | Out-File -FilePath $PATROL_LOG -Append -Encoding UTF8
