# patrol.ps1 — 30分钟巡查 + 自动开仓
$PY312 = "C:\Users\DELL\AppData\Local\Programs\Python\Python312\python.exe"
$SCAN_SCRIPT = "C:\Users\DELL\.openclaw-autoclaw\workspace\find_opportunity_v3.py"
$WS = "C:\Users\DELL\.openclaw-autoclaw\workspace"
$TS = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
$env:PYTHONIOENCODING = "utf-8"

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  $TS AUD/USD/USDCHF 30分钟巡查" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# 1. 跑扫描
Write-Host "[1/4] 扫描市场..." -ForegroundColor Yellow
$scanResult = & $PY312 $SCAN_SCRIPT 2>&1

# 2. 解析信号
Write-Host "[2/4] 解析信号..." -ForegroundColor Yellow
$lines = $scanResult -split "`n"
$opportunities = @()
$bestOp = $null

foreach ($line in $lines) {
    if ($line -match "BEST OPPORTUNITY") {
        # 开始解析 best block
        $inBest = $true
        continue
    }
    if ($inBest -and $line -match "Symbol:\s+(\S+)") {
        $bestOp = @{ Symbol = $Matches[1] }
    }
    if ($inBest -and $line -match "Signal:\s+(BUY|SELL)") {
        $bestOp.Direction = $Matches[1]
    }
    if ($inBest -and $line -match "Strength:\s+([0-9.]+)%") {
        $bestOp.Strength = [double]$Matches[1]
    }
    if ($inBest -and $line -match "SL:\s+([0-9.]+) pips") {
        $bestOp.SL = [double]$Matches[1]
    }
    if ($inBest -and $line -match "TP:\s+([0-9.]+) pips") {
        $bestOp.TP = [double]$Matches[1]
        $inBest = $false
    }
}

Write-Host "[3/4] 检查持仓..." -ForegroundColor Yellow
# 检查 MT5 持仓
$mt5Result = & $PY312 -Command @"
import MetaTrader5 as mt5, sys, json
if not mt5.initialize(login=52797683, server='ICMarketsSC-Demo', timeout=10000):
    print('MT5_FAIL'); sys.exit()
info = mt5.account_info()
positions = mt5.positions_get() or []
print(json.dumps({
    'balance': info.balance,
    'equity': info.equity,
    'positions': [{'symbol': p.symbol, 'type': p.type, 'volume': p.volume, 'price_open': p.price_open, 'sl': p.sl, 'tp': p.tp, 'profit': p.profit}
              for p in positions]
}))
mt5.shutdown()
"@ 2>&1

$mt5Data = $mt5Result | ConvertFrom-Json -ErrorAction SilentlyContinue
if ($mt5Data -and $mt5Data.balance) {
    Write-Host "  余额: `$$($mt5Data.balance), 持仓: $($mt5Data.positions.Count)/3" -ForegroundColor Green
    foreach ($p in $mt5Data.positions) {
        $dir = if ($p.type -eq 0) { "BUY" } else { "SELL" }
        Write-Host "  #$($p.symbol) $dir $($p.volume)手 @ $($p.price_open) 浮盈`$$($p.profit)"
    }
} else {
    Write-Host "  MT5 连接失败: $mt5Result" -ForegroundColor Red
}

Write-Host "[4/4] 决策..." -ForegroundColor Yellow
if ($bestOp -and $bestOp.Strength -ge 0.15) {
    $sym = $bestOp.Symbol
    $dir = $bestOp.Direction
    $sl = $bestOp.SL
    $tp = $bestOp.TP
    $strength = $bestOp.Strength

    # 检查是否已有该品种持仓
    $hasPos = $mt5Data.positions | Where-Object { $_.symbol -eq $sym }
    if ($hasPos) {
        Write-Host "  $sym 已有持仓，跳过" -ForegroundColor Yellow
    } else {
        Write-Host "  *** 强信号: $sym $dir $($strength)% (门槛0.15%)" -ForegroundColor Magenta
        # 计算手数
        $lots = 0.08  # 固定0.08手测试
        Write-Host "  自动开仓 $dir $lots $sym SL=$sl pips TP=$tp pips" -ForegroundColor Magenta
        $openResult = & $PY312 -Command @"
import MetaTrader5 as mt5, sys, time
if not mt5.initialize(login=52797683, server='ICMarketsSC-Demo', timeout=10000):
    print('MT5_INIT_FAIL'); sys.exit()
tick = mt5.symbol_info_tick('$sym')
sym_info = mt5.symbol_info('$sym')
digits = sym_info.digits
point = sym_info.point
pip_unit = 0.0001 if digits == 5 else 0.01
price = tick.ask if '$dir' == 'BUY' else tick.bid
sl_pips = $sl
tp_pips = $tp
sl_price = round(price - sl_pips * pip_unit, digits) if '$dir' == 'BUY' else round(price + sl_pips * pip_unit, digits)
tp_price = round(price + tp_pips * pip_unit, digits) if '$dir' == 'BUY' else round(price - tp_pips * pip_unit, digits)
req = {
    'action': mt5.TRADE_ACTION_DEAL,
    'symbol': '$sym',
    'volume': $lots,
    'type': mt5.ORDER_TYPE_BUY if '$dir' == 'BUY' else mt5.ORDER_TYPE_SELL,
    'price': price,
    'sl': sl_price,
    'tp': tp_price,
    'deviation': 50,
    'magic': 240501,
    'comment': 'Patrol Auto',
    'type_time': mt5.ORDER_TIME_GTC,
    'type_filling': mt5.ORDER_FILLING_IOC
}
result = mt5.order_send(req)
print(f'RETC={result.retcode} ORDER={result.order}')
mt5.shutdown()
"@ 2>&1
        Write-Host "  开仓结果: $openResult" -ForegroundColor $(if ($openResult -match "RETC=10009") { "Green" } else { "Red" })
    }
} else {
    $strengthStr = if ($bestOp.Strength) { "$($bestOp.Strength)%" } else { "N/A" }
    Write-Host "  无达标信号 ($strengthStr < 0.15%)" -ForegroundColor DarkGray
}

Write-Host ""
Write-Host "巡查完成 $TS" -ForegroundColor Cyan
