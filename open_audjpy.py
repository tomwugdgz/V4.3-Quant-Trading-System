import MetaTrader5 as mt5, sys, io, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

if not mt5.initialize(login=52797683, server='ICMarketsSC-Demo', timeout=10000):
    print("MT5 init failed")
    sys.exit()

symbol = "AUDJPY"
tick = mt5.symbol_info_tick(symbol)
sym = mt5.symbol_info(symbol)
print(f"{symbol}: Bid={tick.bid:.3f} Ask={tick.ask:.3f}")

volume = 0.08
sl_pips = 15.0
tp_pips = 30.0
point = sym.point
digits = sym.digits
pip_unit = 0.01 if digits == 3 else 0.001
sl_price = round(tick.ask - sl_pips * pip_unit, digits)
tp_price = round(tick.ask + tp_pips * pip_unit, digits)

risk = volume * sl_pips * 10
print(f"Order: BUY {volume} {symbol} @ {tick.ask:.3f}")
print(f"SL={sl_price:.3f} ({sl_pips}pips) TP={tp_price:.3f} ({tp_pips}pips)")
print(f"Risk: ~${risk:.2f}")

request = {
    "action": mt5.TRADE_ACTION_DEAL,
    "symbol": symbol,
    "volume": volume,
    "type": mt5.ORDER_TYPE_BUY,
    "price": tick.ask,
    "sl": sl_price,
    "tp": tp_price,
    "deviation": 50,
    "magic": 240501,
    "comment": "Wangcai V4.5",
    "type_time": mt5.ORDER_TIME_GTC,
    "type_filling": mt5.ORDER_FILLING_IOC,
}

result = mt5.order_send(request)
print(f"Retcode: {result.retcode}")

if result.retcode == mt5.TRADE_RETCODE_DONE:
    print(f"SUCCESS! Order #{result.order}, Deal #{result.deal}")
    time.sleep(3)
    info = mt5.account_info()
    positions = mt5.positions_get(symbol=symbol)
    print(f"Balance: ${info.balance:.2f}")
    if positions:
        for p in positions:
            print(f"Position #{p.ticket}: {p.volume} {symbol} BUY @ {p.price_open:.3f}, SL={p.sl:.3f} TP={p.tp:.3f}")
else:
    print(f"Failed: {result.comment}")

mt5.shutdown()
