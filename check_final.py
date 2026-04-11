import MetaTrader5 as mt5
mt5.initialize()

positions = mt5.positions_get()
account = mt5.account_info()

print("ACCOUNT")
print("  Login: %d" % account.login)
print("  Balance: $%.2f" % account.balance)
print("  Equity: $%.2f" % account.equity)
print()

print("POSITIONS (%d):" % len(positions))
print()

total_pl = 0
for pos in positions:
    direction = "BUY" if pos.type == 0 else "SELL"
    sign = "+" if pos.profit >= 0 else ""
    print("%s %s %.2f lot" % (pos.symbol, direction, pos.volume))
    print("  Entry: %.5f Current: %.5f" % (pos.price_open, pos.price_current))
    print("  SL: %.5f TP: %.5f" % (pos.sl, pos.tp))
    print("  P/L: %s$%.2f" % (sign, pos.profit))
    print()
    total_pl += pos.profit

print("TOTAL P/L: %s$%.2f" % ("+" if total_pl >= 0 else "", total_pl))
mt5.shutdown()
