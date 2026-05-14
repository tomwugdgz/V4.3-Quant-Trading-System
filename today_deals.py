import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime

mt5.initialize()

today = datetime.now().replace(hour=0, minute=0, second=0)
history = mt5.history_deals_get(today, datetime.now())

if history:
    deals = [d._asdict() for d in history]
    print(f'Today closed deals: {len(deals)}')
    total_profit = 0.0
    for d in deals:
        if d['type'] == 1:  # deal close
            sym = d['symbol']
            profit = d.get('profit', 0)
            swap = d.get('swap', 0)
            commission = d.get('commission', 0)
            total_profit += profit
            print(f'  {sym}: profit={profit:.2f} swap={swap:.2f} comm={commission:.2f}')
    print(f'Net profit today: {total_profit:.2f}')
else:
    print('No closed deals today')

mt5.shutdown()
