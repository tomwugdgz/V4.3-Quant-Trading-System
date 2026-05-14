import MetaTrader5 as mt5
import os, sys
os.environ["PYTHONIOENCODING"] = "utf-8"

if not mt5.initialize():
    print("MT5 init failed")
    sys.exit(1)

acc = mt5.account_info()
print(f"Balance: ${acc.balance:.2f}")
print(f"Equity: ${acc.equity:.2f}")
print(f"Margin: ${acc.margin:.2f}")
print(f"Free: ${acc.margin_free:.2f}")
print(f"Leverage: 1:{acc.leverage}")
pos_count = len(mt5.positions_get()) if mt5.positions_get() else 0
print(f"Positions: {pos_count}")
print()

positions = mt5.positions_get()
if positions:
    for p in positions:
        profit = p.profit + p.swap
        tname = "BUY" if p.type == 0 else "SELL"
        print(f"[{p.symbol}] {tname} {p.volume} lots @ {p.price_open:.5f} | SL:{p.sl:.5f} TP:{p.tp:.5f} | P/L: ${profit:.2f}")
else:
    print("No open positions")

print()

from datetime import datetime
today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

deals = mt5.history_deals_get(today_start)
if deals:
    print(f"Today's deals: {len(deals)}")
    total_profit = 0
    for d in deals:
        if d.profit:
            total_profit += d.profit
            t = datetime.fromtimestamp(d.time)
            dname = getattr(d, 'comment', '') or getattr(d, 'order', '') or ''
            print(f"  {dname} {d.symbol} | P/L: ${d.profit:.2f} | {t:%H:%M}")
    print(f"Today P/L: ${total_profit:.2f}")
else:
    print("No deals today yet")

mt5.shutdown()
