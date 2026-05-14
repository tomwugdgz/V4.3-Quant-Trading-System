import MetaTrader5 as mt5
import sys, time

if not mt5.initialize(login=52797683, server="ICMarketsSC-Demo", timeout=15000):
    print("MT5 init failed")
    sys.exit(1)

symbol = "NZDUSD"

# Check supported filling modes
sym_info = mt5.symbol_info(symbol)
print(f"Symbol: {symbol}", flush=True)
print(f"Fill modes: {sym_info.filling_mode}", flush=True)
# 1=FOK, 2=IOC, 3=RETURN

positions = mt5.positions_get(symbol=symbol)
if not positions:
    print("No positions")
    mt5.shutdown()
    sys.exit(0)

print(f"Found {len(positions)} positions", flush=True)

for p in positions:
    tick = mt5.symbol_info_tick(symbol)
    print(f"\nClosing #{p.ticket}...", flush=True)
    
    # Use IOC filling mode
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
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    
    result = mt5.order_send(close_request)
    print(f"  retcode={result.retcode}, comment={result.comment}", flush=True)
    time.sleep(3)

time.sleep(5)
remaining = mt5.positions_get(symbol=symbol)
print(f"\nRemaining: {len(remaining) if remaining else 0} positions")

mt5.shutdown()
