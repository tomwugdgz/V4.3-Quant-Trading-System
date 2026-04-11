# -*- coding: utf-8 -*-
import MetaTrader5 as mt5

mt5.initialize()

account = mt5.account_info()
print('Account balance: $%.2f' % account.balance)
print('Risk per trade: $100 USD')
print()

# New trades to open: EURUSD, USDCHF, USDCAD
trades = [
    ('EURUSD', 'BUY', 0.00329),
    ('USDCHF', 'SELL', 0.00264),
    ('USDCAD', 'BUY', 0.00262),
]

results = []

for symbol, direction, atr in trades:
    tick = mt5.symbol_info_tick(symbol)
    symbol_info = mt5.symbol_info(symbol)
    
    if not tick or not symbol_info:
        print('%s: No data' % symbol)
        continue
    
    # Calculate SL/TP
    sl_distance = atr * 1.5
    tp_distance = atr * 2.5
    
    if direction == 'BUY':
        price = tick.ask
        sl = price - sl_distance
        tp = price + tp_distance
        order_type = mt5.ORDER_TYPE_BUY
    else:
        price = tick.bid
        sl = price + sl_distance
        tp = price - tp_distance
        order_type = mt5.ORDER_TYPE_SELL
    
    # Calculate volume - $100 risk per trade
    if symbol.endswith('USD'):
        volume = 100 / (sl_distance * 100000)
    else:
        volume = (100 / (sl_distance * 100000)) * price
    
    volume_step = symbol_info.volume_step
    volume_min = symbol_info.volume_min
    volume = round(volume / volume_step) * volume_step
    volume = max(0.01, volume)
    
    print('%s %s: volume=%.2f lot' % (symbol, direction, volume))
    print('  price=%.5f sl=%.5f tp=%.5f' % (price, sl, tp))
    
    # Place order
    request = {
        'action': mt5.TRADE_ACTION_DEAL,
        'symbol': symbol,
        'volume': volume,
        'type': order_type,
        'price': price,
        'sl': round(sl, 5),
        'tp': round(tp, 5),
        'deviation': 10,
        'magic': 2026031702,
        'comment': '72h-aggressive',
        'type_time': mt5.ORDER_TIME_GTC,
        'type_filling': mt5.ORDER_FILLING_IOC,
    }
    
    result = mt5.order_send(request)
    
    if result.retcode == 10009:
        results.append({
            'symbol': symbol,
            'direction': direction,
            'volume': volume,
            'price': result.price,
            'status': 'OK'
        })
        print('  ✓ OK: order=%d' % result.order)
    else:
        results.append({
            'symbol': symbol,
            'direction': direction,
            'status': 'FAILED: %s' % result.comment
        })
        print('  ✗ FAILED: %s' % result.comment)
    
    print()

print('=' * 50)
success = len([r for r in results if r.get('status') == 'OK'])
print('Completed: %d/%d executed' % (success, len(trades)))

# List all positions
print()
print('=== All Open Positions ===')
positions = mt5.positions_get()
if positions:
    for pos in positions:
        direction = 'BUY' if pos.type == 0 else 'SELL'
        profit = pos.profit
        sign = '+' if profit >= 0 else ''
        print('%s %s %.2f lot %s$%.2f (%s)' % (pos.symbol, direction, pos.volume, sign, profit, pos.comment))

mt5.shutdown()
