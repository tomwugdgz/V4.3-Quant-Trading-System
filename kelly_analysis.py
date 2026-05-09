import MetaTrader5 as mt5
from datetime import datetime, timezone, timedelta
from collections import defaultdict

tz = timezone(timedelta(hours=8))
mt5.initialize(login=52797683, server='ICMarketsSC-Demo', timeout=10000)

deals = mt5.history_deals_get(0, 2147483647)
pos_deals = defaultdict(list)
for d in deals:
    if d.position_id:
        pos_deals[d.position_id].append(d)

# Closed = position has entry=0 AND entry=1
closed_positions = {}
for pid, ds in pos_deals.items():
    entries = set(d.entry for d in ds)
    if 0 in entries and 1 in entries:  # has both open and close
        # Find the close deal for realized PnL
        close_deal = next((d for d in ds if d.entry == 1), None)
        open_deal = next((d for d in ds if d.entry == 0), None)
        if close_deal and open_deal:
            realized = float(close_deal.profit) if close_deal.profit else 0.0
            closed_positions[pid] = {
                'symbol': open_deal.symbol,
                'open_price': float(open_deal.price),
                'close_price': float(close_deal.price),
                'close_time': close_deal.time,
                'realized_pnl': realized
            }

print('=== All Closed Positions ===')
print('Total closed positions: {}'.format(len(closed_positions)))
print()

wins = []
losses = []
win_list = []
loss_list = []
by_symbol = defaultdict(lambda: {'wins':0,'losses':0,'pnl':0})

for pid, info in sorted(closed_positions.items(), key=lambda x: x[1]['close_time']):
    ts = datetime.fromtimestamp(info['close_time'], tz).strftime('%m-%d %H:%M')
    pnl = info['realized_pnl']
    sym = info['symbol']
    by_symbol[sym]['pnl'] += pnl
    if pnl > 0:
        wins.append(pnl)
        loss_list.append(pnl)
        by_symbol[sym]['wins'] += 1
        tag = 'WIN'
    else:
        losses.append(pnl)
        win_list.append(pnl)
        by_symbol[sym]['losses'] += 1
        tag = 'LOSS'
    print('[{}] {} {} ${:.2f}'.format(ts, sym, tag, pnl))

print()
print('=== Summary ===')
total_wins = len(wins)
total_losses = len(losses)
total_trades = total_wins + total_losses
W = total_wins / total_trades if total_trades > 0 else 0
avg_win = sum(wins) / total_wins if total_wins > 0 else 0
avg_loss = abs(sum(losses) / total_losses) if total_losses > 0 else 0
R = avg_win / avg_loss if avg_loss > 0 else 0
total_pnl = sum(wins) + sum(losses)
expectancy = W * avg_win - (1 - W) * abs(avg_loss)

print('Total: {} trades | Wins: {} | Losses: {}'.format(total_trades, total_wins, total_losses))
print('Win Rate W: {:.1f}%'.format(W * 100))
print('Avg Win: ${:.2f}'.format(avg_win))
print('Avg Loss: ${:.2f}'.format(avg_loss))
print('Reward/Risk R: {:.2f}'.format(R))
print('Total Realized PnL: ${:.2f}'.format(total_pnl))
print('Expectancy per trade: ${:.2f}'.format(expectancy))
print()

print('--- By Symbol ---')
for sym, s in sorted(by_symbol.items(), key=lambda x: x[1]['pnl']):
    net = s['pnl']
    tag = 'WIN' if net > 0 else 'LOSS'
    print('  {}: {}w/{}l net={:.2f}'.format(sym, s['wins'], s['losses'], net))

print()
print('=== Kelly Criterion ===')
if R > 0:
    kf = W - (1 - W) / R
    kf_half = kf / 2
    kf_qrt = kf / 4
    balance = 9899.46
    risk_current = 0.005  # 0.5%

    print('Formula: f* = W - (1-W)/R = {:.1f} - {:.1f}/{:.2f} = {:.1f}%'.format(
        W, (1-W), R, kf*100))
    print()
    print('Full Kelly: {:.1f}% = ${:.2f} risk/trade'.format(kf*100, balance*kf))
    print('Half Kelly (recommended): {:.1f}% = ${:.2f} risk/trade'.format(
        kf_half*100, balance*kf_half))
    print('Quarter Kelly: {:.1f}% = ${:.2f} risk/trade'.format(
        kf_qrt*100, balance*kf_qrt))
    print()
    print('Current system: {:.1f}% = ${:.2f} risk/trade'.format(
        risk_current*100, balance*risk_current))
    print()
    if kf <= 0:
        print('Conclusion: Kelly<=0, strategy has negative expectancy.')
        print('Keep current 0.5% risk - do NOT increase.')
    elif kf < 0.005:
        print('Conclusion: Kelly {:.1f}% < 0.5%. Current parameters are appropriate.'.format(kf*100))
    else:
        print('Conclusion: Kelly {:.1f}% > 0.5%. Can increase risk.'.format(kf*100))
        print('Recommendation: Quarter Kelly ${:.2f}/trade (conservative for small accounts)'.format(
            balance * kf_qrt))

info = mt5.account_info()
print()
print('Current Balance: ${:.2f}'.format(float(info.balance)))
print('Leverage: 1:{} (ICMarketsSC-Demo)'.format(info.leverage))
print()
print('--- USD/JPY Analysis ---')
print('1:5 leverage (NOT 1:200 as in article)')
print('USDJPY pip value = $6.67 per 0.01 lot at 150.00')
print('0.5% risk on $9899 = ${:.2f}'.format(9899.46 * 0.005))
print('With SL=40pip: max lots = ${:.2f} / (40 x $6.67) = {:.3f} lots'.format(
    9899.46 * 0.005, 9899.46 * 0.005 / (40 * 6.67)))

mt5.shutdown()