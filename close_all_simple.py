# Simple version without emoji/encoding issues
import MetaTrader5 as mt5
from datetime import datetime

print("Connecting to MT5...")

# Try to initialize
if not mt5.initialize():
    print("ERROR: Failed to initialize MT5")
    print("Error code:", mt5.last_error())
    print("\nTROUBLESHOOTING:")
    print("1. Make sure MT5 terminal is OPEN and running")
    print("2. Make sure you are logged into your account")
    print("3. Make sure MetaTrader5 package is installed for Python 3.7")
    exit(1)

print("Connected to MT5 OK")
print()

# Account info
account = mt5.account_info()
print("Account:", account.login)
print("Server:", account.server)
print("Balance: $%.2f" % account.balance)
print("Equity: $%.2f" % account.equity)
print()

# Get positions
positions = mt5.positions_get()
print("Open positions:", len(positions))
print()

if not positions:
    print("No positions to close")
    mt5.shutdown()
    exit(0)

# List positions
for i, pos in enumerate(positions):
    direction = "BUY" if pos.type == 0 else "SELL"
    print("%d: %s %s %.2f lot, P/L: %+.2f" % (
        i+1, pos.symbol, direction, pos.volume, pos.profit
    ))

print()
print("Closing all positions...")
print()

success = 0
failed = 0
total_pl = 0.0

for pos in positions:
    symbol = pos.symbol
    vol = pos.volume
    ticket = pos.ticket
    pl = pos.profit
    total_pl += pl
    
    print("Closing %s ticket %d..." % (symbol, ticket))
    
    tick = mt5.symbol_info_tick(symbol)
    if tick is None:
        print("FAIL: Can't get tick for", symbol)
        failed += 1
        continue
    
    close_type = mt5.ORDER_TYPE_SELL if pos.type == 0 else mt5.ORDER_TYPE_BUY
    price = tick.bid if pos.type == 0 else tick.ask
    
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": vol,
        "type": close_type,
        "position": ticket,
        "price": price,
        "deviation": 20,
        "magic": 0,
        "comment": "close all",
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    
    result = mt5.order_send(request)
    if result.retcode == mt5.TRADE_RETCODE_DONE:
        print("SUCCESS: Order", result.order)
        success += 1
    else:
        print("FAIL: Retcode", result.retcode, "Error", mt5.last_error())
        failed += 1
    
    print()

# Final summary
print("=" * 40)
print("SUMMARY")
print("=" * 40)
print("Total positions: %d" % len(positions))
print("Success: %d" % success)
print("Failed: %d" % failed)
print("Total P/L: %+.2f USD" % total_pl)

account_final = mt5.account_info()
print("Final balance: $%.2f" % account_final.balance)
print("Final equity: $%.2f" % account_final.equity)

mt5.shutdown()

print()
if failed == 0:
    print("DONE: All positions closed! Cash out complete.")
else:
    print("WARNING: Some positions failed to close. Check MT5 manually.")
