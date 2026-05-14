#!/usr/bin/env python3
"""Close duplicate AUDUSD position."""
import MetaTrader5 as mt5
import sys, io

if hasattr(sys.stdout, 'buffer'):
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    except:
        pass

mt5.initialize()
positions = mt5.positions_get()
if not positions:
    print("No positions")
    mt5.shutdown()
    sys.exit(0)

for p in positions:
    direction = "BUY" if p.type == 0 else "SELL"
    print('%s %s %s %.2f lots P/L: $%.2f' % (p.ticket, p.symbol, direction, p.volume, p.profit))

aud_positions = [p for p in positions if p.symbol == 'AUDUSD']
if len(aud_positions) > 1:
    dup = min(aud_positions, key=lambda p: abs(p.profit))
    print('Closing duplicate AUDUSD ticket %s' % dup.ticket)
    order_type = mt5.ORDER_TYPE_SELL if dup.type == 0 else mt5.ORDER_TYPE_BUY
    tick = mt5.symbol_info_tick(dup.symbol)
    price = tick.bid if dup.type == 0 else tick.ask
    req = {
        'action': mt5.TRADE_ACTION_DEAL,
        'position': dup.ticket,
        'symbol': dup.symbol,
        'volume': dup.volume,
        'type': order_type,
        'price': price,
        'deviation': 20,
        'magic': 234000,
        'comment': 'close_duplicate_v4',
        'type_time': mt5.ORDER_TIME_GTC,
        'type_filling': mt5.ORDER_FILLING_IOC
    }
    result = mt5.order_send(req)
    if result.retcode == mt5.TRADE_RETCODE_DONE:
        print('Success: closed %s' % dup.ticket)
    else:
        print('Failed: retcode=%s, comment=%s' % (result.retcode, result.comment))
else:
    print("No duplicate AUDUSD found")

mt5.shutdown()
