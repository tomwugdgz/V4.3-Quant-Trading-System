import MetaTrader5 as mt5
import sys
from datetime import datetime, timezone, timedelta

mt5.initialize()
acc = mt5.account_info()
print('Balance:', acc.balance)
print('Equity:', acc.equity)
positions = mt5.positions_get()
print('Positions:', len(positions) if positions else 0)
if positions:
    for p in positions:
        direction = "BUY" if p.type == 0 else "SELL"
        print(f'  {p.symbol} {direction} {p.volume}@{p.price_open} P/L={p.profit:.2f}')

# Check daily loss
TZ = timezone(timedelta(hours=8))
today_start = datetime.now(TZ).replace(hour=0, minute=0, second=0, microsecond=0)
today_start_mt = today_start.timestamp()
history = mt5.history_orders_get(today_start_mt, datetime.now(TZ).timestamp())
realized_loss = 0
if history:
    for o in history:
        realized_loss += o.profit
print(f'Realized P/L today: ${realized_loss:.2f}')

mt5.shutdown()
