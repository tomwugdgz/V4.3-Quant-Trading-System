import MetaTrader5 as mt5
from datetime import datetime, timezone, timedelta
import numpy as np
import json
import os

tz = timezone(timedelta(hours=8))
mt5.initialize(login=52797683, server='ICMarketsSC-Demo', timeout=10000)

info = mt5.account_info()
positions = mt5.positions_get() or []

# 今日数据
today_start = datetime.now(tz).replace(hour=0, minute=0, second=0, microsecond=0)
today_ts = int(today_start.timestamp())
to_ts = int(datetime.now(tz).timestamp())

history = mt5.history_deals_get(today_ts, to_ts) or []
opens = [d for d in history if d.entry == 0]
closes = [d for d in history if d.entry == 1]

# 每日盈亏
daily_pnl = sum(d.profit + d.swap + d.commission for d in closes)
wins = sum(1 for d in closes if (d.profit + d.swap + d.commission) > 0)
losses = sum(1 for d in closes if (d.profit + d.swap + d.commission) <= 0)
total_trades = wins + losses
wr = (wins / total_trades * 100) if total_trades > 0 else 0

# 账户起始余额（假设 $10000）
START_BALANCE = 10000
total_return = (float(info.balance) - START_BALANCE) / START_BALANCE * 100

# 生成报告
report = {
    'date': datetime.now(tz).strftime('%Y-%m-%d'),
    'balance': float(info.balance),
    'equity': float(info.equity),
    'daily_pnl': daily_pnl,
    'wins': wins,
    'losses': losses,
    'total_return_pct': round(total_return, 2),
    'positions': [],
    'trades_today': []
}

# 当前持仓
for p in positions:
    pdir = 'BUY' if p.type == 0 else 'SELL'
    report['positions'].append({
        'symbol': p.symbol,
        'direction': pdir,
        'volume': p.volume,
        'entry': float(p.price_open),
        'sl': float(p.sl),
        'tp': float(p.tp),
        'floating_pnl': float(p.profit)
    })

# 今日交易
for d in sorted(opens, key=lambda x: x.time):
    pdir = 'BUY' if d.type == 0 else 'SELL'
    t = datetime.fromtimestamp(d.time, tz).strftime('%H:%M')
    report['trades_today'].append({
        'time': t,
        'symbol': d.symbol,
        'action': 'open',
        'direction': pdir,
        'volume': d.volume,
        'price': float(d.price)
    })

for d in sorted(closes, key=lambda x: x.time):
    pdir = 'BUY' if d.type == 0 else 'SELL'
    t = datetime.fromtimestamp(d.time, tz).strftime('%H:%M')
    pnl = d.profit + d.swap + d.commission
    report['trades_today'].append({
        'time': t,
        'symbol': d.symbol,
        'action': 'close',
        'direction': pdir,
        'pnl': round(pnl, 2)
    })

# 保存报告
report_path = os.path.join(os.path.dirname(__file__), 'daily_review.json')
with open(report_path, 'w', encoding='utf-8') as f:
    json.dump(report, f, ensure_ascii=False, indent=2)

# 输出摘要
print('=' * 60)
print('每日复盘 %s' % datetime.now(tz).strftime('%Y-%m-%d'))
print('=' * 60)
print()
print('【账户】余额 $%.2f | 净值 $%.2f | 总回报 %.2f%%' % (
    float(info.balance), float(info.equity), total_return))
print('【今日】开仓 %d 笔 | 平仓 %d 笔 | 净盈亏 $%.2f | 胜率 %.0f%%' % (
    len(opens), len(closes), daily_pnl, wr))
print()

if positions:
    print('【持仓】')
    for p in positions:
        pdir = 'BUY' if p.type == 0 else 'SELL'
        print('  %s %s %.2f手 @%.5f SL:%.5f TP:%.5f 浮盈=$%.2f' % (
            p.symbol, pdir, p.volume, p.price_open, p.sl, p.tp, float(p.profit)))
    print()

if closes:
    print('【今日平仓】')
    for d in sorted(closes, key=lambda x: x.time):
        pdir = 'BUY' if d.type == 0 else 'SELL'
        t = datetime.fromtimestamp(d.time, tz).strftime('%H:%M')
        pnl = d.profit + d.swap + d.commission
        print('  %s %s %s $%.2f' % (t, d.symbol, pdir, pnl))
    print()

# 建议
print('【建议】')
if daily_pnl < -50:
    print('  ⚠️ 今日亏损超限，系统已停止交易')
elif daily_pnl < 0:
    print('  ⚡ 今日亏损中，注意风控')
else:
    print('  ✅ 今日盈利，继续保持')

if wr < 40 and total_trades > 2:
    print('  ⚠️ 胜率低于 40%，考虑调整策略')

if total_return < -5:
    print('  🔴 总回报低于 -5%，建议全面复盘')

mt5.shutdown()
