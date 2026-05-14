import MetaTrader5 as mt5
import json
import sys

if not mt5.initialize(login=52797683, server='ICMarketsSC-Demo', timeout=10000):
    print('MT5_OFFLINE')
    sys.exit()

info = mt5.account_info()
pos = mt5.positions_get() or []

# Get today's closed trades from history
from datetime import datetime, timedelta
today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
from_sec = int(today_start.timestamp())
to_sec = int(datetime.now().timestamp())

deals = mt5.history_deals_get(from_sec, to_sec)

closed_trades = []
if deals:
    for d in deals:
        if d.comment not in ('Patrol Smart', 'Patrol Auto') or d.profit == 0:
            continue
        closed_trades.append({
            'ticket': d.ticket,
            'symbol': d.symbol,
            'dir': 'BUY' if d.type == 0 else 'SELL',
            'volume': float(d.volume),
            'open_price': float(d.price_open),
            'close_price': float(d.price_close),
            'pnl': float(d.profit),
            'time': datetime.fromtimestamp(d.time).strftime('%H:%M')
        })

result = {
    'balance': float(info.balance),
    'equity': float(info.equity),
    'positions': [{'symbol': p.symbol, 'dir': 'BUY' if p.type==0 else 'SELL', 'volume': float(p.volume), 'price': float(p.price_open), 'pnl': float(p.profit), 'ticket': p.ticket} for p in pos],
    'closed_today': closed_trades
}

print(json.dumps(result, ensure_ascii=False, indent=2))
mt5.shutdown()