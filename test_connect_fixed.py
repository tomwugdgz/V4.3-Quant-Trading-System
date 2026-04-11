import MetaTrader5 as mt5

print("=== MT5 Connection Test ===")
print()

result = mt5.initialize()
print("Initialize: ", result)

if not result:
    error = mt5.last_error()
    print("Error: ", error)
    exit()

account = mt5.account_info()
print()
print("Connection SUCCESS!")
print("Account: ", account.login)
print("Balance: $", account.balance)
print("Equity: $", account.equity)
print("Free Margin: $", account.margin_free)
print()

symbols = ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD', 'USDCHF', 'USDCAD']
print("Symbol check:")
for sym in symbols:
    tick = mt5.symbol_info_tick(sym)
    if tick:
        print("  %s: bid=%.5f ask=%.5f" % (sym, tick.bid, tick.ask))
    else:
        print("  %s: (no data)" % sym)

positions = mt5.positions_get()
print()
print("Current positions: %d" % len(positions))
if positions:
    for pos in positions:
        direction = "BUY" if pos.type == 0 else "SELL"
        print("  %s %s %.2f lot P/L $%.2f" % (pos.symbol, direction, pos.volume, pos.profit))

print()
print("=== Test Complete ===")
mt5.shutdown()
