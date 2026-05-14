import MetaTrader5 as mt5
import sys, time, traceback

output = []

def log(msg):
    output.append(msg)
    print(msg)
    sys.stdout.flush()

try:
    log("Starting trade test...")
    
    if not mt5.initialize():
        log(f"MT5 init failed: {mt5.last_error()}")
        sys.exit(1)
    
    log("MT5 initialized")
    
    symbol = "NZDUSD"
    tick = mt5.symbol_info_tick(symbol)
    if tick is None:
        log(f"Failed to get tick for {symbol}")
        mt5.shutdown()
        sys.exit(1)
    
    log(f"NZDUSD Bid={tick.bid}, Ask={tick.ask}")
    
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
        "comment": "Wangcai Test Trade",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    
    log(f"Order: BUY {volume} {symbol} @ {tick.ask}")
    log(f"SL={sl_price}, TP={tp_price}")
    
    result = mt5.order_send(request)
    log(f"Retcode: {result.retcode}")
    log(f"Order: {result.order}")
    log(f"Deal: {result.deal}")
    log(f"Comment: {result.comment}")
    
    time.sleep(3)
    positions = mt5.positions_get(symbol=symbol)
    if positions:
        for p in positions:
            log(f"Position #{p.ticket}: {p.volume} {p.type} @ {p.price_open}")
    else:
        log("No positions found after trade")
    
except Exception as e:
    log(f"Exception: {e}")
    log(traceback.format_exc())
finally:
    mt5.shutdown()
    log("Done")
    
    # Write to file as backup
    with open("test_trade_log.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(output))
