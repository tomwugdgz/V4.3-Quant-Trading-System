import MetaTrader5 as mt5
from datetime import datetime, timezone, timedelta
import json

tz = timezone(timedelta(hours=8))
mt5.initialize(login=52797683, server='ICMarketsSC-Demo', timeout=10000)

info = mt5.account_info()
positions = mt5.positions_get() or []

print('=' * 60)
print('近两日交易报告 (2026-05-11 ~ 2026-05-12)')
print('=' * 60)
print()

for day_offset in [1, 0]:
    check_date = datetime.now(tz).replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=day_offset)
    day_start = int(check_date.timestamp())
    day_end = day_start + 86400
    to_ts = min(day_end, int(datetime.now(tz).timestamp()))

    history = mt5.history_deals_get(day_start, to_ts) or []
    opens = [d for d in history if d.entry == 0]
    closes = [d for d in history if d.entry == 1]

    day_name = check_date.strftime('%Y-%m-%d (%A)')
    print('【%s】' % day_name)

    if not opens and not closes:
        print('  无交易')
        print()
        continue

    # Opens
    print('  开仓 %d 笔:' % len(opens))
    for d in sorted(opens, key=lambda x: x.time):
        pdir = 'BUY' if d.type == 0 else 'SELL'
        t = datetime.fromtimestamp(d.time, tz).strftime('%H:%M')
        print('    %s %s %s %.2f手 @%.5f #%d' % (t, d.symbol, pdir, d.volume, d.price, d.position_id))

    # Closes
    print('  平仓 %d 笔:' % len(closes))
    day_pnl = 0
    wins = 0
    losses = 0
    for d in sorted(closes, key=lambda x: x.time):
        pdir = 'BUY' if d.type == 0 else 'SELL'
        t = datetime.fromtimestamp(d.time, tz).strftime('%H:%M')
        pnl = d.profit + d.swap + d.commission
        day_pnl += pnl
        if pnl > 0:
            wins += 1
            status = '盈利'
        else:
            losses += 1
            status = '亏损'
        print('    %s %s %s %s=$%.2f' % (t, d.symbol, pdir, status, pnl))

    total_trades = wins + losses
    wr = (wins / total_trades * 100) if total_trades > 0 else 0
    print('  当日净盈亏: $%.2f (%dW/%dL, 胜率%.0f%%)' % (day_pnl, wins, losses, wr))
    print()

# Overall summary
print('【两日合计】')
two_days_start = int((datetime.now(tz).replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)).timestamp())
two_days_end = int(datetime.now(tz).timestamp())
history_all = mt5.history_deals_get(two_days_start, two_days_end) or []
closes_all = [d for d in history_all if d.entry == 1]
total_pnl = sum(d.profit + d.swap + d.commission for d in closes_all)
wins_all = sum(1 for d in closes_all if (d.profit + d.swap + d.commission) > 0)
losses_all = sum(1 for d in closes_all if (d.profit + d.swap + d.commission) <= 0)
total_trades_all = wins_all + losses_all
wr_all = (wins_all / total_trades_all * 100) if total_trades_all > 0 else 0

print('  开仓: %d 笔' % len([d for d in history_all if d.entry == 0]))
print('  平仓: %d 笔' % len(closes_all))
print('  净盈亏: $%.2f' % total_pnl)
print('  胜率: %.0f%% (%dW/%dL)' % (wr_all, wins_all, losses_all))
print()

# Current positions
print('【当前持仓】')
for p in positions:
    pdir = 'BUY' if p.type==0 else 'SELL'
    print('  %s %s %.2f手 @%.5f SL:%.5f TP:%.5f 浮盈=$%.2f' % (
        p.symbol, pdir, p.volume, p.price_open, p.sl, p.tp, float(p.profit)))
print()

print('【账户状态】')
print('  余额: $%.2f' % float(info.balance))
print('  净值: $%.2f' % float(info.equity))

mt5.shutdown()
