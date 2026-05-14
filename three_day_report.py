import MetaTrader5 as mt5
from datetime import datetime, timezone, timedelta
import json

tz = timezone(timedelta(hours=8))
mt5.initialize(login=52797683, server='ICMarketsSC-Demo', timeout=10000)

info = mt5.account_info()
positions = mt5.positions_get() or []

# 近3天数据
three_days_ago = datetime.now(tz).replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=3)
start_ts = int(three_days_ago.timestamp())
to_ts = int(datetime.now(tz).timestamp())

history = mt5.history_deals_get(start_ts, to_ts) or []
closes = [d for d in history if d.entry == 1]
opens = [d for d in history if d.entry == 0]

print('=' * 60)
print('三日战斗报告 (2026-05-11 ~ 2026-05-13)')
print('=' * 60)
print()

print('【账户状态】')
print('  余额: $%.2f' % float(info.balance))
print('  净值: $%.2f' % float(info.equity))
print('  持仓: %d/3' % len(positions))
print()

# 按天统计
for day_offset in [2, 1, 0]:
    check_date = datetime.now(tz).replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=day_offset)
    day_name = check_date.strftime('%Y-%m-%d (%A)')
    day_start = int(check_date.timestamp())
    day_end = day_start + 86400
    to = min(day_end, to_ts)

    day_closes = [d for d in history if d.entry == 1 and day_start <= d.time < to]
    day_opens = [d for d in history if d.entry == 0 and day_start <= d.time < to]

    day_pnl = sum(d.profit + d.swap + d.commission for d in day_closes)
    day_wins = sum(1 for d in day_closes if (d.profit + d.swap + d.commission) > 0)
    day_losses = len(day_closes) - day_wins

    print('【%s】' % day_name)
    print('  开仓 %d 笔 | 平仓 %d 笔 | 净盈亏 $%.2f' % (len(day_opens), len(day_closes), day_pnl))

    if day_closes:
        for d in sorted(day_closes, key=lambda x: x.time):
            t = datetime.fromtimestamp(d.time, tz).strftime('%H:%M')
            pnl = d.profit + d.swap + d.commission
            status = '盈利' if pnl > 0 else '亏损'
            print('    %s %s %s $%.2f' % (t, d.symbol, status, pnl))
    print()

# 持仓详情
if positions:
    print('【当前持仓】')
    for p in positions:
        pdir = 'BUY' if p.type == 0 else 'SELL'
        print('  %s %s %.2f手 @%.5f SL:%.5f TP:%.5f 浮盈=$%.2f' % (
            p.symbol, pdir, p.volume, p.price_open, p.sl, p.tp, float(p.profit)))
    print()

# 总统计
total_pnl = sum(d.profit + d.swap + d.commission for d in closes)
total_wins = sum(1 for d in closes if (d.profit + d.swap + d.commission) > 0)
total_losses = len(closes) - total_wins
total_trades = total_wins + total_losses
wr = (total_wins / total_trades * 100) if total_trades > 0 else 0

print('【三日合计】')
print('  开仓: %d 笔' % len(opens))
print('  平仓: %d 笔' % len(closes))
print('  净盈亏: $%.2f' % total_pnl)
print('  胜率: %.0f%% (%dW/%dL)' % (wr, total_wins, total_losses))
print()

# 按品种统计
print('【按品种】')
sym_stats = {}
for d in closes:
    sym = d.symbol
    pnl = d.profit + d.swap + d.commission
    if sym not in sym_stats:
        sym_stats[sym] = {'wins': 0, 'losses': 0, 'pnl': 0}
    sym_stats[sym]['pnl'] += pnl
    if pnl > 0:
        sym_stats[sym]['wins'] += 1
    else:
        sym_stats[sym]['losses'] += 1

for sym, stats in sorted(sym_stats.items(), key=lambda x: x[1]['pnl'], reverse=True):
    print('  %s: $%.2f (%dW/%dL)' % (sym, stats['pnl'], stats['wins'], stats['losses']))

mt5.shutdown()
