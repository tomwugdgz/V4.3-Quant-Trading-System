import MetaTrader5 as mt5
import numpy as np
import os

os.environ['PYTHONIOENCODING'] = 'utf-8'

mt5.initialize()

# Current positions
positions = mt5.positions_get()
print('Current positions:')
for p in (positions or []):
    ptype = 'BUY' if p.type == 0 else 'SELL'
    print(f'  {p.symbol}: {ptype} {p.volume} lots, profit={p.profit:.2f}')

# Account info
info = mt5.account_info()
print(f'\nBalance: ${info.balance:.2f}, Equity: ${info.equity:.2f}')

# XAUUSD signal
symbol = 'XAUUSD'
rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H4, 0, 50)
ma6 = np.mean([r['close'] for r in rates[-6:]])
ma12 = np.mean([r['close'] for r in rates[-12:]])
current = rates[-1]['close']
dev6 = (current - ma6) / ma6 * 100
dev12 = (current - ma12) / ma12 * 100
signal = (abs(dev6) + abs(dev12)) / 2
direction = 'SELL' if current < ma6 and current < ma12 else 'BUY'

print(f'\nXAUUSD: {current:.2f}, MA6={ma6:.2f} ({dev6:+.3f}%), MA12={ma12:.2f} ({dev12:+.3f}%)')
print(f'Signal: {signal:.3f}%, Direction: {direction}')

# Check threshold
if signal > 0.15:
    print('  ** SIGNAL ABOVE 0.15% THRESHOLD - READY TO TRADE **')

# Scan all majors
print('\nAll majors scan:')
pairs = ['EURUSD', 'GBPUSD', 'AUDUSD', 'NZDUSD', 'USDJPY', 'USDCAD', 'USDCHF']
for sym in pairs:
    r = mt5.copy_rates_from_pos(sym, mt5.TIMEFRAME_H4, 0, 20)
    if r is not None:
        ma = np.mean([x['close'] for x in r[-10:]])
        cur = r[-1]['close']
        dev = (cur - ma) / ma * 100
        d = 'BUY' if dev > 0 else 'SELL'
        flag = ' ** SIGNAL **' if abs(dev) > 0.15 else ''
        print(f'  {sym}: {cur:.5f}, dev={dev:+.3f}% ({d}){flag}')

mt5.shutdown()
