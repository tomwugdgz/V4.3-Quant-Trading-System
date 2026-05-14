import MetaTrader5 as mt5
import sys, time

if not mt5.initialize(login=52797683, server="ICMarketsSC-Demo", timeout=10000):
    print("MT5 init failed")
    sys.exit(1)

symbol = "NZDUSD"
positions = mt5.positions_get(symbol=symbol)

if not positions:
    print("No positions found")
    mt5.shutdown()
    sys.exit(0)

print(f"Found {len(positions)} NZDUSD positions:", flush=True)
for p in positions:
    print(f"  #{p.ticket}: {p.volume} BUY @ {p.price_open}, Profit={p.profit}", flush=True)

# Close all positions
for p in positions:
    tick = mt5.symbol_info_tick(symbol)
    close_request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": p.volume,
        "type": mt5.ORDER_TYPE_SELL,
        "position": p.ticket,
        "price": tick.bid,
        "deviation": 30,
        "magic": 240501,
        "comment": "Test Close",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    print(f"Closing #{p.ticket}...", flush=True)
    result = mt5.order_send(close_request)
    print(f"  retcode={result.retcode}, order={result.order}", flush=True)
    time.sleep(1)

# Verify
time.sleep(2)
remaining = mt5.positions_get(symbol=symbol)
if remaining:
    print(f"\n{len(remaining)} positions still open")
else:
    print("\nAll positions closed!")

mt5.shutdown()
