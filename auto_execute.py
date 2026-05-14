import MetaTrader5 as mt5
import numpy as np
import os
import sys

os.environ['PYTHONIOENCODING'] = 'utf-8'

mt5.initialize()

RISK_PER_TRADE = 0.005  # 0.5%
MAX_POSITIONS = 3
SIGNAL_THRESHOLD = 0.15  # %

def get_contract_specs(symbol):
    info = mt5.symbol_info(symbol)
    if info is None:
        return None
    return {
        'contract_size': info.trade_contract_size,
        'point': info.point,
        'digits': info.digits,
        'volume_min': info.volume_min,
        'volume_step': info.volume_step,
        'volume_max': info.volume_max,
    }

def calc_lot_size(symbol, sl_price, direction):
    specs = get_contract_specs(symbol)
    if specs is None:
        return 0.01
    
    # Get tick value
    tick = mt5.symbol_info_tick(symbol)
    if tick is None:
        return 0.01
    
    # Calculate pip size
    pip_size = specs['point'] * 10
    if specs['digits'] in [3, 5]:
        pip_size = specs['point'] * 10
    elif specs['digits'] in [2, 4]:
        pip_size = specs['point'] * 100
    
    # For JPY pairs and XAUUSD, adjust
    if 'JPY' in symbol:
        pip_size = specs['point'] * 100
    if symbol == 'XAUUSD':
        pip_size = 0.01 * 100  # $0.01 point, pip = $1
    
    # Get tick value per lot
    sl_points = abs(sl_price - tick.bid if direction == 'BUY' else tick.ask - sl_price) / specs['point']
    
    # pip_value = tick_value * (pip_size / tick_size)
    # For most pairs: pip_value per lot = $10
    # We need to get this from MT5
    tick_value = 1.0  # default, will adjust
    
    account = mt5.account_info()
    risk_amount = account.balance * RISK_PER_TRADE
    
    # Simple approach: use point value calculation
    point_value = specs['contract_size'] * specs['point']  # per 1 lot
    
    if direction == 'BUY':
        sl_pips = abs(tick.bid - sl_price) / specs['point']
    else:
        sl_pips = abs(tick.ask - sl_price) / specs['point']
    
    sl_cost = sl_pips * point_value  # cost per lot for this SL distance
    lot_size = risk_amount / sl_cost if sl_cost > 0 else 0.01
    
    # Normalize
    lot_size = max(specs['volume_min'], min(specs['volume_max'], lot_size))
    lot_size = round(lot_size / specs['volume_step']) * specs['volume_step']
    lot_size = round(lot_size, 2)
    
    return max(specs['volume_min'], lot_size)

def open_trade(symbol, direction, sl_price, tp_price, lot_size):
    if direction == 'BUY':
        price = mt5.symbol_info_tick(symbol).ask
        order_type = mt5.ORDER_TYPE_BUY
    else:
        price = mt5.symbol_info_tick(symbol).bid
        order_type = mt5.ORDER_TYPE_SELL
    
    request = {
        'action': mt5.TRADE_ACTION_DEAL,
        'symbol': symbol,
        'volume': lot_size,
        'type': order_type,
        'price': price,
        'sl': sl_price,
        'tp': tp_price,
        'deviation': 50,
        'magic': 234000,
        'comment': 'AutoTrade v4.3',
        'type_time': mt5.ORDER_TIME_GTC,
        'type_filling': mt5.ORDER_FILLING_FOK,
    }
    
    result = mt5.order_send(request)
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        # Try with IOC filling
        request['type_filling'] = mt5.ORDER_FILLING_IOC
        result = mt5.order_send(request)
    
    return result

# Check current positions
positions = mt5.positions_get()
current_count = len(positions) if positions else 0
print(f'Current positions: {current_count}/{MAX_POSITIONS}')
for p in (positions or []):
    ptype = 'BUY' if p.type == 0 else 'SELL'
    print(f'  {p.symbol}: {ptype} {p.volume} lots, profit={p.profit:.2f}')

if current_count >= MAX_POSITIONS:
    print('Max positions reached, skipping new trades.')
    mt5.shutdown()
    sys.exit()

# Scan for signals
print('\nScanning for signals...')
symbols_to_scan = ['XAUUSD', 'EURUSD', 'GBPUSD', 'AUDUSD', 'NZDUSD', 'USDJPY', 'USDCAD', 'USDCHF']
signals = []

for sym in symbols_to_scan:
    rates = mt5.copy_rates_from_pos(sym, mt5.TIMEFRAME_H4, 0, 50)
    if rates is None or len(rates) < 12:
        continue
    
    ma6 = np.mean([r['close'] for r in rates[-6:]])
    ma12 = np.mean([r['close'] for r in rates[-12:]])
    current = rates[-1]['close']
    
    dev6 = (current - ma6) / ma6 * 100
    dev12 = (current - ma12) / ma12 * 100
    signal_strength = (abs(dev6) + abs(dev12)) / 2
    
    if current < ma6 and current < ma12:
        direction = 'SELL'
    else:
        direction = 'BUY'
    
    if signal_strength > SIGNAL_THRESHOLD:
        signals.append({
            'symbol': sym,
            'direction': direction,
            'strength': signal_strength,
            'price': current,
        })
        print(f'  {sym}: {direction} {signal_strength:.3f}% (price {current:.5f})')

# Sort by strength
signals.sort(key=lambda x: x['strength'], reverse=True)

# Execute top signals (respecting max positions)
available_slots = MAX_POSITIONS - current_count
executed = 0

for sig in signals[:available_slots]:
    sym = sig['symbol']
    direction = sig['direction']
    strength = sig['strength']
    price = sig['price']
    
    specs = get_contract_specs(sym)
    tick = mt5.symbol_info_tick(sym)
    
    if specs is None or tick is None:
        print(f'  Skipping {sym}: no specs/tick data')
        continue
    
    # Calculate SL/TP using ATR
    atr_rates = mt5.copy_rates_from_pos(sym, mt5.TIMEFRAME_H4, 0, 20)
    atr_values = []
    for i in range(1, min(15, len(atr_rates))):
        high = atr_rates[i]['high']
        low = atr_rates[i]['low']
        prev_close = atr_rates[i-1]['close']
        tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
        atr_values.append(tr)
    atr = np.mean(atr_values) if atr_values else specs['point'] * 100
    
    if direction == 'BUY':
        sl_price = round(tick.ask - 2 * atr, specs['digits'])
        tp_price = round(tick.ask + 3 * atr, specs['digits'])
    else:
        sl_price = round(tick.bid + 2 * atr, specs['digits'])
        tp_price = round(tick.bid - 3 * atr, specs['digits'])
    
    lot_size = calc_lot_size(sym, sl_price, direction)
    
    print(f'\nExecuting {sym} {direction}:')
    print(f'  Signal: {strength:.3f}%')
    print(f'  Entry: {tick.ask if direction=="BUY" else tick.bid:.5f}')
    print(f'  SL: {sl_price:.5f}, TP: {tp_price:.5f}')
    print(f'  Lot: {lot_size}')
    
    result = open_trade(sym, direction, sl_price, tp_price, lot_size)
    
    if result and result.retcode == mt5.TRADE_RETCODE_DONE:
        print(f'  ** EXECUTED! Order #{result.order} **')
        executed += 1
    else:
        rc = result.retcode if result else 'N/A'
        print(f'  FAILED: retcode={rc}, comment={result.comment if result else "N/A"}')

print(f'\nTotal executed: {executed}')
mt5.shutdown()
