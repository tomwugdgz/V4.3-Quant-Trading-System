#!/usr/bin/env python
# -*- coding: utf-8 -*-
import MetaTrader5 as mt5
import json

mt5.initialize()

with open('72h_closed.json', 'r') as f:
    closed = json.load(f)

closed_tickets = [p['ticket'] for p in closed['closed_positions']]
positions = mt5.positions_get()

print("=== Remaining Positions ===\n")

old_positions = []
total_equity = 0

for pos in positions:
    if pos.ticket in closed_tickets:
        continue
    
    if pos.type == 0:
        price_diff = pos.price_current - pos.price_open
    else:
        price_diff = pos.price_open - pos.price_current
    
    symbol_info = mt5.symbol_info(pos.symbol)
    point = symbol_info.point
    tick_value = symbol_info.trade_tick_value
    ticks_diff = price_diff / point
    profit = ticks_diff * tick_value * pos.volume
    notional = pos.volume * pos.price_open * 100000
    
    if notional > 0:
        profit_pct = (profit / notional) * 100
    else:
        profit_pct = 0
    
    old_positions.append({
        'symbol': pos.symbol,
        'type': 'BUY' if pos.type == 0 else 'SELL',
        'volume': pos.volume,
        'open_price': pos.price_open,
        'current_price': pos.price_current,
        'profit': pos.profit,
        'profit_pct': profit_pct
    })
    
    total_equity += pos.profit

print(f"Count: {len(old_positions)}\n")

for i, p in enumerate(old_positions, 1):
    direction = "BUY" if p['type'] == 'BUY' else "SELL"
    icon = "[+]" if p['profit'] > 0 else "[-]"
    print(f"{i}. {p['symbol']} {direction} {p['volume']} lots")
    print(f"   Open: {p['open_price']:.5f} | Current: {p['current_price']:.5f}")
    print(f"   P/L: ${p['profit']:.2f} ({p['profit_pct']:.2f}%) {icon}\n")

account = mt5.account_info()
print("=== Summary ===")
print(f"Total P/L: ${total_equity:.2f}")
print(f"Balance: ${account.balance:.2f}")
print(f"Equity: ${account.equity:.2f}")

loss_20 = [p for p in old_positions if p['profit_pct'] < -20]
if loss_20:
    print(f"\n[WARN] Positions >20% loss: {len(loss_20)}")
    for p in loss_20:
        print(f"   {p['symbol']}: {p['profit_pct']:.2f}%")
else:
    print(f"\n[OK] No positions below -20%")

mt5.shutdown()
