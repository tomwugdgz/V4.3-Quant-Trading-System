import MetaTrader5 as mt5
import os, sys
os.environ["PYTHONIOENCODING"] = "utf-8"

if not mt5.initialize():
    print("MT5 init failed")
    sys.exit(1)

acc = mt5.account_info()
print(f"Balance: ${acc.balance:.2f}")
print(f"Equity: ${acc.equity:.2f}")
print()

# Yesterday close balance
from datetime import datetime, timedelta
yesterday = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)
today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

# Get all deals from yesterday to now
deals = mt5.history_deals_get(yesterday)
if deals:
    today_deals = [d for d in deals if d.time >= int(today_start.timestamp())]
    if today_deals:
        print(f"Today's closed deals: {len(today_deals)}")
        total = 0
        for d in today_deals:
            if d.profit:
                total += d.profit
                t = datetime.fromtimestamp(d.time)
                sym = d.symbol or ''
                print(f"  {sym} | P/L: ${d.profit:.2f} | {t:%H:%M:%S}")
        print(f"Today P/L: ${total:.2f}")
    else:
        print("No deals today")
else:
    print("No deals today")

# Also check recent closed positions via orders
# Get today's closed orders
orders = mt5.history_orders_get(today_start)
if orders:
    closed = [o for o in orders if o.state == 5]  # DEAL
    if closed:
        print(f"\nToday closed orders: {len(closed)}")
        for o in closed:
            print(f"  {o.symbol} {o.type} | {datetime.fromtimestamp(o.time_setup):%H:%M:%S}")

mt5.shutdown()
