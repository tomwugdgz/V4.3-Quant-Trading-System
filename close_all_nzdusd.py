import MetaTrader5 as mt5
import sys, time

if not mt5.initialize(login=52797683, server="ICMarketsSC-Demo", timeout=15000):
    print("MT5 init failed")
    sys.exit(1)

symbol = "NZDUSD"
positions = mt5.positions_get(symbol=symbol)

if not positions:
    print("No NZDUSD positions")
    mt5.shutdown()
    sys.exit(0)

print(f"Closing {len(positions)} NZDUSD positions...", flush=True)

for p in positions:
    tick = mt5.symbol_info_tick(symbol)
    print(f"Closing #{p.ticket}: {p.volume} @ {tick.bid}", flush=True)
    
    close_request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": p.volume,
        "type": mt5.ORDER_TYPE_SELL,
        "position": p.ticket,
        "price": tick.bid,
        "deviation": 50,
        "magic": 240501,
        "comment": "Close Test",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_FOK,
    }
    
    result = mt5.order_send(close_request)
    print(f"  retcode={result.retcode}, comment={result.comment}", flush=True)
    time.sleep(2)

time.sleep(3)
remaining = mt5.positions_get(symbol=symbol)
if remaining:
    print(f"\n{len(remaining)} positions still open:")
    for p in remaining:
        print(f"  #{p.ticket}: Profit={p.profit:.2f}", flush=True)
else:
    print("\nAll NZDUSD positions closed!")

mt5.shutdown()
