#!/usr/bin/env python3
"""MT5 data read test"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import MetaTrader5 as mt5
from datetime import datetime, timedelta

if not mt5.initialize():
    print('MT5 initialization failed')
    sys.exit(1)

# 1. Account info
acc = mt5.account_info()
print('=== Account Info ===')
print(f'Login: {acc.login}')
print(f'Server: {acc.server}')
print(f'Balance: ${acc.balance:.2f}')
print(f'Equity: ${acc.equity:.2f}')
print(f'Free Margin: ${acc.margin_free:.2f}')
print(f'Margin: ${acc.margin:.2f}')
print(f'Margin Level: {acc.margin_level:.2f}%')
print(f'Leverage: 1:{acc.leverage}')
print(f'Floating P/L: ${acc.profit:.2f}')

# 2. Open positions
positions = mt5.positions_get()
print(f'\n=== Open Positions ({len(positions) if positions else 0}) ===')
if positions:
    for p in positions:
        d = 'BUY' if p.type == 0 else 'SELL'
        print(f'  {p.symbol} {d} {p.volume} @ {p.price_open} | Current: {p.price_current} | P/L: ${p.profit:.2f}')
else:
    print('  No open positions')

# 3. Recent deals (last 7 days)
deals = mt5.history_deals_get(datetime.now() - timedelta(days=7), datetime.now()) or []
closed = [d for d in deals if d.profit != 0]
print(f'\n=== Last 7 Days Deals ({len(deals)} total, {len(closed)} closed) ===')
for d in deals[-10:]:
    d_type = 'BUY' if d.type == 0 else 'SELL'
    print(f'  {d.symbol} {d_type} vol:{d.volume} @ {d.price} | P/L: ${d.profit:.2f} | Comm: ${d.commission:.2f} | {d.time}')

# 4. Real-time quotes
symbols = ['EURUSD', 'GBPUSD', 'AUDUSD', 'NZDUSD', 'USDCHF', 'USDCAD', 'USDJPY']
print(f'\n=== Live Quotes ===')
for sym in symbols:
    tick = mt5.symbol_info_tick(sym)
    if tick:
        spread = (tick.ask - tick.bid) * 10000
        print(f'  {sym}: Bid={tick.bid:.5f} Ask={tick.ask:.5f} Spread={spread:.1f} pts')
    else:
        print(f'  {sym}: NO DATA')

# 5. Summary stats
total_profit = sum(d.profit for d in deals)
total_comm = sum(d.commission for d in deals)
wins = [d for d in deals if d.profit > 0]
losses = [d for d in deals if d.profit < 0]
print(f'\n=== 7-Day Summary ===')
print(f'Total deals: {len(deals)}')
print(f'Closed P/L deals: {len(closed)}')
print(f'Wins: {len(wins)}, Losses: {len(losses)}')
print(f'Total profit: ${total_profit:.2f}')
print(f'Total commission: ${total_comm:.2f}')
print(f'Net P/L: ${total_profit + total_comm:.2f}')
if closed:
    wr = len(wins) / len(closed) * 100
    print(f'Win rate: {wr:.1f}%')

mt5.shutdown()
print('\n=== MT5 data read: ALL OK ===')
