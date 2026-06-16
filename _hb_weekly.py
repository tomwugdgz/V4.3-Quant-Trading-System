import MetaTrader5 as mt5
import time

mt5.initialize()

t_from = int(time.mktime((2026, 6, 7, 0, 0, 0, 0, 0, 0)))
t_to = int(time.mktime((2026, 6, 14, 23, 59, 59, 0, 0, 0)))

# Get deals (closed positions)
deals = mt5.history_deals_get(t_from, t_to)
if deals is None:
    deals = []

print(f"=== CLOSED DEALS (06-07 to 06-14) ===")
total_pnl = 0
wins = 0
losses = 0
count = 0
by_symbol = {}

for d in deals:
    if d.entry == 1:  # only closing deals
        pnl = d.profit + d.swap + d.commission
        if abs(pnl) < 0.005:
            continue
        total_pnl += pnl
        count += 1
        if pnl > 0:
            wins += 1
        elif pnl < 0:
            losses += 1
        sym = d.symbol
        if sym not in by_symbol:
            by_symbol[sym] = {'count': 0, 'pnl': 0}
        by_symbol[sym]['count'] += 1
        by_symbol[sym]['pnl'] += pnl

print(f"Total closed: {count}")
print(f"Total PnL: ${total_pnl:.2f}")
print(f"Wins: {wins}, Losses: {losses}")
if wins + losses > 0:
    print(f"Win rate: {wins/(wins+losses)*100:.1f}%")
print(f"\nBy symbol:")
for sym, data in sorted(by_symbol.items(), key=lambda x: x[1]['pnl'], reverse=True):
    print(f"  {sym}: {data['count']} trades, PnL ${data['pnl']:.2f}")

mt5.shutdown()
