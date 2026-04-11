# Check all open positions
import MetaTrader5 as mt5
from datetime import datetime

mt5.initialize()

print("Current Open Positions Report")
print("Time:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
print("=" * 60)
print()

account = mt5.account_info()
print("Account:", account.login)
print("Server:", account.server)
print("Balance: $%.2f" % account.balance)
print("Equity: $%.2f" % account.equity)
print("Free Margin: $%.2f" % account.margin_free)
print()

positions = mt5.positions_get()
print("Total open positions:", len(positions) if positions else 0)
print()

total_volume = 0.0
total_profit = 0.0

if positions:
    for i, pos in enumerate(positions, 1):
        direction = "BUY" if pos.type == 0 else "SELL"
        profit_sign = "+" if pos.profit >= 0 else ""
        print("%d. %s %s %.2f lot" % (i, pos.symbol, direction, pos.volume))
        print("   Entry: %.5f | Current: %.5f" % (pos.price_open, pos.price_current))
        print("   SL: %.5f | TP: %.5f" % (pos.sl, pos.tp))
        print("   P/L: %s%.2f (Swap: %.2f)" % (profit_sign, pos.profit, pos.swap))
        print("   Open Time: %s" % datetime.fromtimestamp(pos.time))
        print()
        total_volume += pos.volume
        total_profit += pos.profit

print("=" * 60)
print("SUMMARY:")
print("=" * 60)
print("Total lots: %.2f" % total_volume)
profit_sign = "+" if total_profit >= 0 else ""
print("Total floating P/L: %s%.2f USD" % (profit_sign, total_profit))
print()

mt5.shutdown()
