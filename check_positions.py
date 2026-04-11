# -*- coding: utf-8 -*-
import MetaTrader5 as mt5
from datetime import datetime

mt5.initialize()

account = mt5.account_info()
print('=== ACCOUNT STATUS ===')
print(f'Account: {account.login}')
print(f'Balance: ${account.balance:.2f} USD')
print(f'Equity: ${account.equity:.2f} USD')
print(f'Margin: ${account.margin:.2f} USD')
print(f'Free Margin: ${account.margin_free:.2f} USD')
print(f'Margin Level: {account.margin_level:.1f}%')
print()

positions = mt5.positions_get()
print(f'=== POSITIONS: {len(positions)} ===')
print()

if positions:
    for pos in positions:
        direction = 'BUY' if pos.type == 0 else 'SELL'
        profit_sign = '+' if pos.profit >= 0 else ''
        status = 'PROFIT' if pos.profit >= 0 else 'LOSS'
        
        print(f'[{status}] {pos.symbol} {direction} {pos.volume:.2f} lot')
        print(f'  Entry: {pos.price_open:.5f}')
        print(f'  Current: {pos.price_current:.5f}')
        print(f'  SL: {pos.sl:.5f}')
        print(f'  TP: {pos.tp:.5f}')
        print(f'  P/L: {profit_sign}${pos.profit:.2f} (Swap: ${pos.swap:.2f})')
        print(f'  Open Time: {datetime.fromtimestamp(pos.time)}')
        print(f'  Comment: {pos.comment}')
        print()
else:
    print('WARNING: NO OPEN POSITIONS!')

mt5.shutdown()
