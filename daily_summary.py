import MetaTrader5 as mt5
from datetime import datetime, timezone, timedelta

tz = timezone(timedelta(hours=8))
mt5.initialize(login=52797683, server='ICMarketsSC-Demo', timeout=10000)

info = mt5.account_info()
balance = float(info.balance)
equity = float(info.equity)

today_start = datetime.now(tz).replace(hour=0, minute=0, second=0, microsecond=0)
from_sec = int(today_start.timestamp())
deals = mt5.history_deals_get(from_sec, int(datetime.now(tz).timestamp()))

positions = mt5.positions_get()

print('=== 2026-05-08 全天亏损根因分析 ===')
print()
print('--- 今日所有成交（时间顺序）---')
for d in sorted(deals, key=lambda x: x.time):
    action = '开仓' if d.entry in (0,1) else '平仓'
    pdir = 'BUY' if d.type==0 else 'SELL'
    profit_val = float(d.profit) if d.profit is not None else 0.0
    comm_val = float(d.commission) if d.commission is not None else 0.0
    price_val = float(d.price) if d.price is not None else 0.0
    print('[{}] {} {} {}手 @{} {} -> PnL:${:.2f} Comm:${:.2f}'.format(
        datetime.fromtimestamp(d.time, tz).strftime('%H:%M'),
        d.symbol, pdir, d.volume, price_val, action, profit_val, comm_val))

print()
print('--- 按品种汇总 ---')
from collections import defaultdict
by_symbol = defaultdict(lambda: {'opens':0,'closed_pnl':0.0,'fees':0.0,'winning':0,'losing':0,'open_entries':[]})
for d in deals:
    key = d.symbol
    comm_val = float(d.commission) if d.commission is not None else 0.0
    price_val = float(d.price) if d.price is not None else 0.0
    profit_val = float(d.profit) if d.profit is not None else 0.0
    by_symbol[key]['fees'] += abs(comm_val)
    if d.entry in (2,3):
        by_symbol[key]['closed_pnl'] += profit_val
        if profit_val > 0:
            by_symbol[key]['winning'] += 1
        else:
            by_symbol[key]['losing'] += 1
    else:
        by_symbol[key]['opens'] += 1
        by_symbol[key]['open_entries'].append((d.type, d.volume, price_val, datetime.fromtimestamp(d.time, tz).strftime('%H:%M')))

for sym, s in sorted(by_symbol.items(), key=lambda x: x[1]['closed_pnl']):
    print('{}: 开仓{}笔 已平盈亏${:.2f} 费用${:.2f} 赢{}笔亏{}笔'.format(
        sym, s['opens'], s['closed_pnl'], s['fees'], s['winning'], s['losing']))
    for e in s['open_entries']:
        pdir = 'BUY' if e[0]==0 else 'SELL'
        print('    -> {} {}手 @{} {}'.format(pdir, e[1], e[2], e[3]))

print()
print('--- 当前持仓（检查SL/TP是否正常）---')
for p in positions:
    tick = mt5.symbol_info_tick(p.symbol)
    pdir = 'BUY' if p.type==0 else 'SELL'
    cur = float(tick.bid if p.type==0 else tick.ask)
    entry = float(p.price_open)
    pips = (cur - entry) / 0.0001 if 'JPY' not in p.symbol else (cur - entry) / 0.01
    sl_val = float(p.sl) if p.sl is not None else 0.0
    tp_val = float(p.tp) if p.tp is not None else 0.0
    print('  {} {} {}手 @{} 现价{} 浮盈${:.2f}（{:.1f}pip）'.format(
        p.symbol, pdir, p.volume, entry, cur, float(p.profit), pips))
    print('    SL={} TP={}'.format(sl_val, tp_val))
    # 检查SL/TP是否异常
    if pdir == 'BUY' and sl_val > 0 and sl_val > entry:
        print('    *** 警告: BUY仓SL {} > 入场价 {}，异常！'.format(sl_val, entry))
    if pdir == 'SELL' and sl_val > 0 and sl_val < entry:
        print('    *** 警告: SELL仓SL {} < 入场价 {}，异常！'.format(sl_val, entry))

print()
total_closed = sum(float(d.profit) for d in deals if d.entry in (2,3) and d.profit is not None)
total_fee = sum(abs(float(d.commission)) for d in deals if d.commission is not None)
total_unreal = sum(float(p.profit) for p in positions if p.profit is not None)
print('已实现: ${:.2f}  费用: ${:.2f}  浮动: ${:.2f}  合计: ${:.2f}'.format(
    total_closed, total_fee, total_unreal, total_closed+total_fee+total_unreal))
print('余额: ${:.2f}  净值: ${:.2f}'.format(balance, equity))
mt5.shutdown()