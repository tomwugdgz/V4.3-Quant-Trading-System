import MetaTrader5 as mt5
mt5.initialize()

print("=== ALL OPEN POSITIONS ===")
print()
positions = mt5.positions_get()
if positions:
    print("Total positions: %d" % len(positions))
    print()
    for pos in positions:
        direction = "BUY" if pos.type == 0 else "SELL"
        sign = "+" if pos.profit >= 0 else ""
        print("%s %s %.2f lot" % (pos.symbol, direction, pos.volume))
        print("  Entry: %.5f Current: %.5f" % (pos.price_open, pos.price_current))
        print("  SL: %.5f TP: %.5f" % (pos.sl, pos.tp))
        print("  P/L: %s$%.2f Comment: %s" % (sign, pos.profit, pos.comment))
        print()
else:
    print("No positions")
    print()

print("=== SEARCH FOR TESLA AND TENCENT ===")
print()

all_symbols = mt5.symbols_get()
found = []
for sym in all_symbols:
    name = sym.name.upper()
    if 'TSLA' in name or 'TENC' in name or '0700' in name:
        found.append(sym.name)

if found:
    print("Found symbols:")
    for f in found:
        tick = mt5.symbol_info_tick(f)
        if tick:
            print("  %s: bid=%.2f ask=%.2f" % (f, tick.bid, tick.ask))
        else:
            print("  %s: (no tick data)" % f)
else:
    print("No matching symbols found")

print()
print("Check complete")
mt5.shutdown()
