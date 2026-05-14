#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""周度复盘脚本"""
import MetaTrader5 as mt5
from datetime import datetime

mt5.initialize()
mt5.login(52797683)

from_dt = datetime(2026, 4, 25)
to_dt = datetime.now()

deals = mt5.history_deals_get(from_dt, to_dt)

# 按品种统计
stats = {}
total_profit = 0.0
for d in deals:
    sym = d.symbol
    if sym not in stats:
        stats[sym] = {'count': 0, 'profit': 0.0}
    stats[sym]['count'] += 1
    stats[sym]['profit'] += d.profit
    total_profit += d.profit

print('=== 品种统计 ===')
for sym in sorted(stats.keys(), key=lambda x: stats[x]['profit'], reverse=True):
    s = stats[sym]
    print(f"{sym}: {s['count']} 笔，总盈亏: ${s['profit']:.2f}")
print(f'\n总盈亏: ${total_profit:.2f}')

print('\n=== 最近 15 笔交易 ===')
sorted_deals = sorted(deals, key=lambda x: x.time, reverse=True)
for d in sorted_deals[:15]:
    direction = "BUY" if d.type == 0 else "SELL"
    t = datetime.fromtimestamp(d.time)
    print(f"{t}: {d.symbol} {direction} {d.volume} profit=${d.profit:.2f} comment={d.comment}")

# 检查每笔交易前是否调用了 Python/MT5 数据
print('\n=== 交易时间分布 ===')
# 按小时统计
hour_stats = {}
for d in deals:
    t = datetime.fromtimestamp(d.time)
    hour = t.hour
    if hour not in hour_stats:
        hour_stats[hour] = 0
    hour_stats[hour] += 1

print('按小时分布:')
for h in sorted(hour_stats.keys()):
    print(f"  {h:02d}:00 - {hour_stats[h]} 笔")
