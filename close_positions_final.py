import MetaTrader5 as mt5
import sys, time, socket

socket.setdefaulttimeout(30)

if not mt5.initialize(login=52797683, server="ICMarketsSC-Demo", timeout=30000):
    print("MT5 init failed")
    sys.exit(1)

symbol = "NZDUSD"
positions = mt5.positions_get(symbol=symbol)

if not positions:
    print("No positions")
    mt5.shutdown()
    sys.exit(0)

print(f"Found {len(positions)} positions to close", flush=True)

# Try closing each position with longer waits
for p in positions:
    tick = mt5.symbol_info_tick(symbol)
    print(f"\nClosing #{p.ticket} {p.volume} @ {tick.bid}...", flush=True)
    
    close_request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": p.volume,
        "type": mt5.ORDER_TYPE_SELL,
        "position": p.ticket,
        "price": tick.bid,
        "deviation": 100,
        "magic": 240501,
        "comment": "Close",
        "type_time": mt5.ORDER_TIME_DAY,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    
    result = mt5.order_send(close_request)
    print(f"  retcode={result.retcode}, comment='{result.comment}'", flush=True)
    
    if result.retcode == mt5.TRADE_RETCODE_DONE:
        print(f"  SUCCESS! Order #{result.order}", flush=True)
    elif result.retcode == 10012:
        print(f"  TIMEOUT - waiting 5s and retrying...", flush=True)
        time.sleep(5)
        result2 = mt5.order_send(close_request)
        print(f"  Retry: retcode={result2.retcode}, comment='{result2.comment}'", flush=True)
    
    time.sleep(2)

time.sleep(5)
remaining = mt5.positions_get(symbol=symbol)
print(f"\nFinal: {len(remaining) if remaining else 0} NZDUSD positions remaining", flush=True)

# Check final balance
info = mt5.account_info()
print(f"Balance: ${info.balance:.2f}", flush=True)

mt5.shutdown()
