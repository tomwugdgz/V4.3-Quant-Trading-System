import MetaTrader5 as mt5
import sys, time

print("1. Starting trade test...", flush=True)

# Explicit initialization
if not mt5.initialize(login=52797683, server="ICMarketsSC-Demo", timeout=10000):
    print(f"MT5 init failed: {mt5.last_error()}", flush=True)
    sys.exit(1)

print("2. MT5 initialized", flush=True)

symbol = "NZDUSD"
tick = mt5.symbol_info_tick(symbol)
if tick is None:
    print("No tick data", flush=True)
    mt5.shutdown()
    sys.exit(1)

print(f"3. Tick: Ask={tick.ask}, Bid={tick.bid}", flush=True)

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
    "comment": "Wangcai Test",
    "type_time": mt5.ORDER_TIME_GTC,
    "type_filling": mt5.ORDER_FILLING_IOC,
}

print(f"4. Sending BUY order: {volume} {symbol} @ {tick.ask}", flush=True)
print(f"   SL={sl_price}, TP={tp_price}", flush=True)

result = mt5.order_send(request)
print(f"5. Order result:", flush=True)
print(f"   retcode={result.retcode}", flush=True)
print(f"   order={result.order}", flush=True)
print(f"   deal={result.deal}", flush=True)
print(f"   comment={result.comment}", flush=True)

if result.retcode == mt5.TRADE_RETCODE_DONE:
    print("6. TRADE SUCCESS! Waiting 5 seconds to verify...", flush=True)
    time.sleep(5)
    
    positions = mt5.positions_get(symbol=symbol)
    if positions:
        for p in positions:
            print(f"7. Position #{p.ticket}: {p.volume} {p.type} @ {p.price_open}, SL={p.sl}, TP={p.tp}", flush=True)
        
        # Now close the position for test completion
        print("8. Closing position for test...", flush=True)
        pos = positions[0]
        close_request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": pos.volume,
            "type": mt5.ORDER_TYPE_SELL,
            "position": pos.ticket,
            "price": mt5.symbol_info_tick(symbol).bid,
            "deviation": 30,
            "magic": 240501,
            "comment": "Test Close",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        close_result = mt5.order_send(close_request)
        print(f"9. Close result: retcode={close_result.retcode}, order={close_result.order}", flush=True)
    else:
        print("7. No positions found after trade", flush=True)
else:
    print("6. Trade failed - checking positions anyway", flush=True)
    positions = mt5.positions_get(symbol=symbol)
    if positions:
        for p in positions:
            print(f"   Position #{p.ticket}: {p.volume} {p.type} @ {p.price_open}", flush=True)

mt5.shutdown()
print("10. Done", flush=True)
