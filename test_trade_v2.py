import MetaTrader5 as mt5
import sys, time

print("1. Importing mt5...", flush=True)
import MetaTrader5 as mt5
print("2. Import OK", flush=True)

if not mt5.initialize():
    print("MT5 init failed")
    sys.exit(1)

print("3. MT5 initialized", flush=True)

symbol = "NZDUSD"
tick = mt5.symbol_info_tick(symbol)
if tick is None:
    print("No tick data")
    mt5.shutdown()
    sys.exit(1)

print(f"4. Tick: Ask={tick.ask}", flush=True)

volume = 0.01
point = mt5.symbol_info(symbol).point
digits = mt5.symbol_info(symbol).digits

sl_price = round(tick.ask - 17.2 * point * 10, digits)
tp_price = round(tick.ask + 34.4 * point * 10, digits)

request = {
    "action": mt5.TRADE_ACTION_DEAL,
    "symbol": symbol,
    "volume": volume,
    "type": mt5.ORDER_TYPE_BUY,
    "price": tick.ask,
    "sl": sl_price,
    "tp": tp_price,
    "deviation": 30,
    "magic": 240501,
    "comment": "Test",
    "type_time": mt5.ORDER_TIME_GTC,
    "type_filling": mt5.ORDER_FILLING_IOC,
}

print(f"5. Sending order: BUY {volume} {symbol} @ {tick.ask}, SL={sl_price}, TP={tp_price}", flush=True)

try:
    result = mt5.order_send(request)
    print(f"6. Result retcode={result.retcode}", flush=True)
    print(f"   Order={result.order}, Deal={result.deal}", flush=True)
except Exception as e:
    print(f"6. Exception: {e}", flush=True)

mt5.shutdown()
print("7. Done", flush=True)
