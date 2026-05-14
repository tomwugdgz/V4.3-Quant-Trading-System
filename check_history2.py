#!/usr/bin/env python
# -*- coding: utf-8 -*-
import MetaTrader5 as mt5
import pandas as pd
import sys, io
from datetime import datetime, timedelta

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

mt5.initialize(login=52797683, server='ICMarketsSC-Demo', timeout=10000)
info = mt5.account_info()

print("=== Account Status 09:39 ===")
print(f"Balance: {info.balance:.2f}")
print(f"Equity: {info.equity:.2f}")

positions = mt5.positions_get() or []
print(f"Positions: {len(positions)}")
for p in positions:
    pdir = "BUY" if p.type == 0 else "SELL"
    print(f"  #{p.ticket} {p.symbol} {pdir} {p.volume}@{p.price_open:.5f} P/L={p.profit:.2f}")

# Historical trades (past 7 days)
start = datetime.now().replace(hour=0, minute=0, second=0) - timedelta(days=7)
start_ms = int(start.timestamp())
deals = mt5.history_deals_get(start_ms, int(datetime.now().timestamp()) + 60)
if deals:
    records = []
    for d in deals:
        records.append({
            'time': datetime.fromtimestamp(d.time).strftime('%m-%d %H:%M'),
            'symbol': d.symbol,
            'type': 'BUY' if d.type == 0 else 'SELL',
            'vol': d.volume,
            'price': d.price,
            'profit': d.profit
        })
    df = pd.DataFrame(records)
    print(f"\n=== Last 7 Days: {len(df)} trades ===")
    print(df.to_string(index=False))
    by_sym = df.groupby('symbol')['profit'].agg(['count', 'sum']).sort_values('sum', ascending=False)
    print(f"\n=== P/L by Symbol ===")
    print(by_sym.to_string())
    total = df["profit"].sum()
    print(f"\nNet Profit: {total:.2f}")
else:
    print("No historical deals")

mt5.shutdown()