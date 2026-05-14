import MetaTrader5 as mt5
import sys

if not mt5.initialize(login=52797683, server="ICMarketsSC-Demo", timeout=15000):
    print("MT5 init failed")
    sys.exit(1)

# Check EURUSD (most liquid pair)
for sym in ["EURUSD", "GBPUSD", "NZDUSD"]:
    tick = mt5.symbol_info_tick(sym)
    if tick:
        print(f"{sym}: Bid={tick.bid}, Ask={tick.ask}, Spread={tick.ask-tick.bid:.5f}", flush=True)
    else:
        print(f"{sym}: No tick data", flush=True)

mt5.shutdown()
