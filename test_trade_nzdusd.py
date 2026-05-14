import MetaTrader5 as mt5
import sys, time

if not mt5.initialize():
    print("MT5 init failed")
    sys.exit(1)

symbol = "NZDUSD"
tick = mt5.symbol_info_tick(symbol)
print(f"NZDUSD Tick: Bid={tick.bid}, Ask={tick.ask}")

# Ultra small test: 0.01 lot
volume = 0.01
sl_pips = 17.2
tp_pips = 34.4
point = mt5.symbol_info(symbol).point
digits = mt5.symbol_info(symbol).digits

sl_price = round(tick.ask - sl_pips * point * 10, digits)
tp_price = round(tick.ask + tp_pips * point * 10, digits)

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

print(f"Order: BUY {volume} {symbol} @ {tick.ask}")
print(f"SL={sl_price}, TP={tp_price}")

result = mt5.order_send(request)
print(f"Retcode: {result.retcode}")
print(f"Order: {result.order}")
print(f"Deal: {result.deal}")
print(f"Comment: {result.comment}")

# Verify position
time.sleep(2)
positions = mt5.positions_get(symbol=symbol)
if positions:
    for p in positions:
        print(f"Position #{p.ticket}: {p.volume} {p.type} @ {p.price_open}, SL={p.sl}, TP={p.tp}")
else:
    print("No positions found")

mt5.shutdown()
