#!/usr/bin/env python
# -*- coding: utf-8 -*-
import MetaTrader5 as mt5
import json

mt5.initialize()

with open('72h_trades.json', 'r') as f:
    plan = json.load(f)

total_profit = 0
total_volume = 0

for t in plan['trades']:
    sym = t['symbol']
    tick = mt5.symbol_info_tick(sym)
    if tick is None:
        continue
    symbol_info = mt5.symbol_info(sym)
    
    if t['order_type'] == 'buy':
        current = tick.ask
        price_diff = current - t['price']
    else:
        current = tick.bid
        price_diff = t['price'] - current
    
    point = symbol_info.point
    tick_value = symbol_info.trade_tick_value
    ticks_diff = price_diff / point
    profit = ticks_diff * tick_value * t['volume']
    total_profit += profit
    total_volume += t['volume']

print(f"===== 72小时计划 ($2000本金) =====")
print(f"总投入风险: $2000 USD")
print(f"当前总浮盈: ${total_profit:.2f} USD")
print(f"收益率: {(total_profit / 2000 * 100):.2f}%")
print(f"总手数: {total_volume:.2f} 手")

mt5.shutdown()
