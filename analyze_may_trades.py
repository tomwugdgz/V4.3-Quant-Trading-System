import MetaTrader5 as mt5
from datetime import datetime
from collections import defaultdict

mt5.initialize(login=52797683, server='ICMarketsSC-Demo', timeout=10000)

from_sec = int(datetime(2026,5,1).timestamp())
to_sec = int(datetime(2026,5,8).timestamp())

deals = mt5.history_deals_get(from_sec, to_sec)
trades = []
if deals:
    for d in deals:
        if d.volume > 0 and abs(d.profit) > 0.1:
            trades.append({
                'time': datetime.fromtimestamp(d.time).strftime('%m-%d %H:%M'),
                'symbol': d.symbol,
                'dir': 'BUY' if d.type == 0 else 'SELL',
                'vol': float(d.volume),
                'pnl': float(d.profit),
                'comment': d.comment
            })

trades.sort(key=lambda x: x['time'])
total = 0
for t in trades:
    tag = t['comment'].strip('[]') if t['comment'] else ''
    print(f"{t['time']} {t['symbol']:8} {t['dir']} {t['vol']} ${t['pnl']:+.2f}  [{tag}]")
    total += t['pnl']

print(f"\n===== 5月1日-7日 =====")
print(f"总笔数: {len(trades)}")
print(f"盈利笔数: {len([t for t in trades if t['pnl']>0])}")
print(f"亏损笔数: {len([t for t in trades if t['pnl']<0])}")
print(f"净盈亏: ${total:.2f}")

by_sym = defaultdict(lambda: {'win':0,'lose':0,'pnl':0})
for t in trades:
    by_sym[t['symbol']]['pnl'] += t['pnl']
    if t['pnl'] > 0:
        by_sym[t['symbol']]['win'] += 1
    else:
        by_sym[t['symbol']]['lose'] += 1
print(f"\n===== 品种盈亏 =====")
for sym, s in sorted(by_sym.items(), key=lambda x: -x[1]['pnl']):
    print(f"  {sym:8}: {s['win']}W/{s['lose']}L  ${s['pnl']:+.2f}")

print(f"\n===== 05-06 AUDJPY 连续3单分析 =====")
for t in trades:
    if '05-06' in t['time'] and 'AUDJPY' in t['symbol']:
        print(f"  {t['time']} {t['dir']} {t['vol']} ${t['pnl']:.2f}  [{t['comment']}]")

print(f"\n===== 05-07 尾盘异动 =====")
for t in trades:
    if '05-07' in t['time']:
        print(f"  {t['time']} {t['symbol']:8} {t['dir']} {t['vol']} ${t['pnl']:+.2f}")

mt5.shutdown()
