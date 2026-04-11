# -*- coding: utf-8 -*-
# 检查当前持仓和查询股票
import MetaTrader5 as mt5

mt5.initialize()

# 所有持仓
print("=== ALL OPEN POSITIONS ===\n")
positions = mt5.positions_get()
if positions:
    print(f"Total positions: {len(positions)}\n")
    for pos in positions:
        direction = "BUY" if pos.type == 0 else "SELL"
        sign = "+" if pos.profit >= 0 else ""
        print(f"{pos.symbol} {direction} {pos.volume:.2f} lot")
        print(f"  Entry: {pos.price_open:.5f} Current: {pos.price_current:.5f}")
        print(f"  SL: {pos.sl:.5f} TP: {pos.tp:.5f}")
        print(f"  P/L: {sign}${pos.profit:.2f} Comment: {pos.comment}\n")
else:
    print("No positions\n")

# 查询腾讯和特斯拉
print("=== STOCK QUOTE: TENCENT & TESLA ===\n")

stocks = [
    ("Tesla", "TSLA"),
    ("Tencent", "TCEHY"),
    ("Tencent HK", "0700"),
]

for name, symbol in stocks:
    tick = mt5.symbol_info_tick(symbol)
    if tick:
        print(f"{name} ({symbol}):")
        print(f"  Bid: {tick.bid:.2f} Ask: {tick.ask:.2f}")
        if tick.time:
            from datetime import datetime
            print(f"  Time: {datetime.fromtimestamp(tick.time)}")
        print()
    else:
        print(f"{name} ({symbol}): Symbol not found\n")

# 列出所有股票符号（包含 TSLA 和 Tencent）
print("=== AVAILABLE SYMBOLS CONTAINING TSLA/TENCENT ===\n")
all_symbols = mt5.symbols_get()
found = []
for sym in all_symbols:
    if 'TSLA' in sym.name.upper() or 'TENC' in sym.name.upper() or '0700' in sym.name:
        found.append(sym.name)

if found:
    for f in found:
        print(f"  {f}")
else:
    print("  No matching symbols found")

mt5.shutdown()
