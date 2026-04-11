import MetaTrader5 as mt5

mt5.initialize()

# EURUSD BUY
symbol = 'EURUSD'
direction = 'BUY'
atr = 0.00329
risk = 100.0

tick = mt5.symbol_info_tick(symbol)
info = mt5.symbol_info(symbol)

sl_dist = atr * 1.5
price = tick.ask
sl = price - sl_dist
tp = price + (atr * 2.5)
vol = 100 / (sl_dist * 100000)
vol = round(vol / info.volume_step) * info.volume_step
vol = max(0.01, vol)

req = {
    'action': mt5.TRADE_ACTION_DEAL,
    'symbol': symbol,
    'volume': vol,
    'type': mt5.ORDER_TYPE_BUY,
    'price': price,
    'sl': round(sl, 5),
    'tp': round(tp, 5),
    'deviation': 10,
    'magic': 2026031702,
    'comment': 'aggressive',
    'type_time': mt5.ORDER_TIME_GTC,
    'type_filling': mt5.ORDER_FILLING_IOC,
}
res = mt5.order_send(req)
print('EURUSD BUY: retcode=%d volume=%.2f price=%.5f' % (res.retcode, vol, res.price))

# USDCHF SELL
symbol = 'USDCHF'
direction = 'SELL'
atr = 0.00264
risk = 100.0

tick = mt5.symbol_info_tick(symbol)
info = mt5.symbol_info(symbol)

sl_dist = atr * 1.5
price = tick.bid
sl = price + sl_dist
tp = price - (atr * 2.5)
vol = 100 / (sl_dist * 100000) * price
vol = round(vol / info.volume_step) * info.volume_step
vol = max(0.01, vol)

req = {
    'action': mt5.TRADE_ACTION_DEAL,
    'symbol': symbol,
    'volume': vol,
    'type': mt5.ORDER_TYPE_SELL,
    'price': price,
    'sl': round(sl, 5),
    'tp': round(tp, 5),
    'deviation': 10,
    'magic': 2026031702,
    'comment': 'aggressive',
    'type_time': mt5.ORDER_TIME_GTC,
    'type_filling': mt5.ORDER_FILLING_IOC,
}
res = mt5.order_send(req)
print('USDCHF SELL: retcode=%d volume=%.2f price=%.5f' % (res.retcode, vol, res.price))

# USDCAD BUY
symbol = 'USDCAD'
direction = 'BUY'
atr = 0.00262
risk = 100.0

tick = mt5.symbol_info_tick(symbol)
info = mt5.symbol_info(symbol)

sl_dist = atr * 1.5
price = tick.ask
sl = price - sl_dist
tp = price + (atr * 2.5)
vol = 100 / (sl_dist * 100000)
vol = round(vol / info.volume_step) * info.volume_step
vol = max(0.01, vol)

req = {
    'action': mt5.TRADE_ACTION_DEAL,
    'symbol': symbol,
    'volume': vol,
    'type': mt5.ORDER_TYPE_BUY,
    'price': price,
    'sl': round(sl, 5),
    'tp': round(tp, 5),
    'deviation': 10,
    'magic': 2026031702,
    'comment': 'aggressive',
    'type_time': mt5.ORDER_TIME_GTC,
    'type_filling': mt5.ORDER_FILLING_IOC,
}
res = mt5.order_send(req)
print('USDCAD BUY: retcode=%d volume=%.2f price=%.5f' % (res.retcode, vol, res.price))

print()
print('=== All Positions ===')
positions = mt5.positions_get()
for p in positions:
    d = 'BUY' if p.type == 0 else 'SELL'
    pf = '+' if p.profit >= 0 else ''
    print('%s %s %.2f %s$%.2f (%s)' % (p.symbol, d, p.volume, pf, p.profit, p.comment))

mt5.shutdown()
