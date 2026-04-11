import MetaTrader5 as mt5

if not mt5.initialize():
    print("Init failed")
    exit()

positions = mt5.positions_get()
print(f"Total positions: {len(positions) if positions else 0}")

if positions:
    for p in positions:
        side = "BUY" if p.type == 0 else "SELL"
        print(f"  {p.symbol} {side} {p.volume} profit=${p.profit:.2f}")
else:
    print("No positions")

mt5.shutdown()
