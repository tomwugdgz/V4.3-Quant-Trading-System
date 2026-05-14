#!/usr/bin/env python
import MetaTrader5 as mt5
import sys

if not mt5.initialize():
    print("MT5 init failed")
    sys.exit(1)

positions = mt5.positions_get()
if positions:
    print(f"Found {len(positions)} positions to close:", flush=True)
    for pos in positions:
        tick = mt5.symbol_info_tick(pos.symbol)
        if not tick:
            print(f"  No tick for {pos.symbol}", flush=True)
            continue
        
        # Determine close order type
        close_type = mt5.ORDER_TYPE_SELL if pos.type == 0 else mt5.ORDER_TYPE_BUY
        close_price = tick.bid if pos.type == 0 else tick.ask
        
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": pos.symbol,
            "volume": pos.volume,
            "type": close_type,
            "position": pos.ticket,
            "price": close_price,
            "deviation": 50,
            "magic": 240501,
            "comment": "Close",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        print(f"  Closing #{pos.ticket} {pos.symbol} {pos.volume}...", flush=True)
        result = mt5.order_send(request)
        print(f"    retcode={result.retcode}, comment='{result.comment}'", flush=True)
        if result.retcode == mt5.TRADE_RETCODE_DONE:
            print(f"    SUCCESS!", flush=True)
        else:
            print(f"    Failed - code {result.retcode}", flush=True)
else:
    print("No positions", flush=True)

mt5.shutdown()
print("Done", flush=True)
