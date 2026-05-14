import MetaTrader5 as mt5
from datetime import datetime, timezone, timedelta
import numpy as np

tz = timezone(timedelta(hours=8))
mt5.initialize(login=52797683, server='ICMarketsSC-Demo', timeout=10000)

info = mt5.account_info()
positions = mt5.positions_get() or []

today_start = datetime(2026, 5, 11, 0, 0, 0, tzinfo=tz)
today_ts = int(today_start.timestamp())
to_ts = int(datetime.now(tz).timestamp())

history = mt5.history_deals_get(today_ts, to_ts) or []

print('=' * 60)
print('2026-05-11 今日战斗报告')
print('=' * 60)
print()
print('【账户状态】')
print('  余额: $%.2f' % float(info.balance))
print('  净值: $%.2f' % float(info.equity))
print('  浮盈: $%.2f' % (float(info.equity) - float(info.balance)))
print('  持仓: %d/3' % len(positions))
print()

if positions:
    print('【当前持仓】')
    for p in positions:
        pdir = 'BUY' if p.type==0 else 'SELL'
        print('  %s %s %.2f手 @%.5f SL:%.5f TP:%.5f 浮盈=$%.2f' % (
            p.symbol, pdir, p.volume, p.price_open, p.sl, p.tp, float(p.profit)))
    print()

opens = [d for d in history if d.entry == 0]
closes = [d for d in history if d.entry == 1]

print('【今日开仓】(%d笔)' % len(opens))
for d in sorted(opens, key=lambda x: x.time):
    pdir = 'BUY' if d.type == 0 else 'SELL'
    t = datetime.fromtimestamp(d.time, tz).strftime('%H:%M')
    print('  %s %s %s %.2f手 @%.5f 单号:%d' % (
        t, d.symbol, pdir, d.volume, d.price, d.position_id))
print()

print('【今日平仓】(%d笔)' % len(closes))
total_pnl = 0
for d in sorted(closes, key=lambda x: x.time):
    pdir = 'BUY' if d.type == 0 else 'SELL'
    t = datetime.fromtimestamp(d.time, tz).strftime('%H:%M')
    pnl = d.profit + d.swap + d.commission
    total_pnl += pnl
    print('  %s %s %s 盈亏=$%.2f' % (t, d.symbol, '盈利' if pnl > 0 else '亏损', pnl))
print()
print('  今日净盈亏: $%.2f' % total_pnl)
print()

wins = sum(1 for d in closes if (d.profit + d.swap + d.commission) > 0)
losses = sum(1 for d in closes if (d.profit + d.swap + d.commission) <= 0)
if closes:
    wr = wins / len(closes) * 100
    avg_win = np.mean([(d.profit+d.swap+d.commission) for d in closes if (d.profit+d.swap+d.commission)>0]) if wins else 0
    avg_loss = np.mean([(d.profit+d.swap+d.commission) for d in closes if (d.profit+d.swap+d.commission)<=0]) if losses else 0
    print('【统计】')
    print('  开仓: %d笔 | 平仓: %d笔' % (len(opens), len(closes)))
    print('  胜率: %.1f%% (%dW/%dL)' % (wr, wins, losses))
    print('  平均盈利: $%.2f' % avg_win)
    print('  平均亏损: $%.2f' % avg_loss)
else:
    print('【统计】今日无平仓')

print()
print('【按品种统计】')
sym_stats = {}
for d in closes:
    if d.symbol not in sym_stats:
        sym_stats[d.symbol] = {'wins':0, 'losses':0, 'pnl':0}
    pnl = d.profit + d.swap + d.commission
    sym_stats[d.symbol]['pnl'] += pnl
    if pnl > 0:
        sym_stats[d.symbol]['wins'] += 1
    else:
        sym_stats[d.symbol]['losses'] += 1

for sym, stats in sorted(sym_stats.items(), key=lambda x: x[1]['pnl'], reverse=True):
    print('  %s: $%.2f (%dW/%dL)' % (sym, stats['pnl'], stats['wins'], stats['losses']))

mt5.shutdown()
