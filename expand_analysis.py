import MetaTrader5 as mt5
from datetime import datetime, timezone, timedelta
from collections import defaultdict
import numpy as np

tz = timezone(timedelta(hours=8))
mt5.initialize(login=52797683, server='ICMarketsSC-Demo', timeout=10000)

all_history = mt5.history_deals_get(0, int(datetime.now(tz).timestamp())) or []
closes = [d for d in all_history if d.entry == 1]

sym_stats = defaultdict(lambda: {'wins':0, 'losses':0, 'total_pnl':0, 'win_amt':[], 'loss_amt':[]})

for d in closes:
    sym = d.symbol
    pnl = d.profit + d.swap + d.commission
    sym_stats[sym]['total_pnl'] += pnl
    if pnl > 0:
        sym_stats[sym]['wins'] += 1
        sym_stats[sym]['win_amt'].append(pnl)
    else:
        sym_stats[sym]['losses'] += 1
        sym_stats[sym]['loss_amt'].append(pnl)

# 分析所有扫描的品种（不仅是已交易的）
info = mt5.account_info()
SYMBOLS = [
    "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "USDCHF", "NZDUSD",
    "EURJPY", "AUDJPY", "EURGBP", "EURCAD", "GBPAUD", "GBPJPY",
    "EURAUD", "AUDCAD", "AUDCHF", "NZDJPY", "CADJPY", "CHFJPY",
    "XAUUSD", "XAGUSD"
]

# 获取已交易品种的数据
print('=' * 70)
print('扩展品种分析：从历史数据找正 EV 品种')
print('=' * 70)
print()

# 对每个已交易品种计算 EV
print('[已交易品种 EV 分析]')
print('%-10s %4s %4s %4s %5s %8s %8s %5s %6s' % (
    '品种', '总笔', 'W', 'L', '胜率%', '均盈$', '均亏$', 'R', 'Kelly'))
print('-' * 70)

tradable = []
blocked = []
micro_test = []

for sym, stats in sorted(sym_stats.items(), key=lambda x: x[1]['total_pnl'], reverse=True):
    w = stats['wins']
    l = stats['losses']
    t = w + l
    if t == 0:
        continue
    wr_pct = w/t*100
    aw = np.mean(stats['win_amt']) if stats['win_amt'] else 0
    al = abs(np.mean(stats['loss_amt'])) if stats['loss_amt'] else 0
    r = aw/al if al > 0 else 0
    w_pct = w/t
    k = w_pct - (1-w_pct)/r if r > 0 else -999
    ev = w_pct * r - (1-w_pct)
    pnl = stats['total_pnl']

    print('%-10s %4d %4d %4d %5.1f%% %8.2f %8.2f %5.2f %6.1f%%' % (
        sym, t, w, l, wr_pct, aw, al, r, k*100))

    if t >= 5 and ev > 0:
        tradable.append((sym, ev, w, l, pnl))
    elif t >= 5 and ev <= 0:
        blocked.append((sym, ev, w, l, pnl))
    elif t < 5:
        micro_test.append((sym, ev, w, l, pnl))

print()
print('[结论]')
print()
print('正 EV 品种（可交易，样本>=5）:')
for sym, ev, w, l, pnl in tradable:
    print('  ✅ %s (EV=%.3f, %dW/%dL, $%.2f)' % (sym, ev, w, l, pnl))

print()
print('负 EV 品种（禁止，样本>=5）:')
for sym, ev, w, l, pnl in blocked:
    print('  🚫 %s (EV=%.3f, %dW/%dL, $%.2f)' % (sym, ev, w, l, pnl))

print()
print('样本不足（<5笔，无法确定）:')
for sym, ev, w, l, pnl in micro_test:
    print('  ⚠️ %s (%d笔, EV=%.3f, $%.2f)' % (sym, w+l, ev, pnl))

# 检查是否有潜力品种接近正 EV
print()
print('[潜力品种分析]')
for sym, stats in sorted(sym_stats.items(), key=lambda x: x[1]['total_pnl'], reverse=True):
    w = stats['wins']
    l = stats['losses']
    t = w + l
    if t >= 3 and t < 5:
        wr_pct = w/t*100
        aw = np.mean(stats['win_amt']) if stats['win_amt'] else 0
        al = abs(np.mean(stats['loss_amt'])) if stats['loss_amt'] else 0
        r = aw/al if al > 0 else 0
        ev = (w/t) * r - (l/t) if r > 0 else -999
        print('  %s: %d笔, 胜率%.0f%%, R=%.2f, EV=%.3f, $%.2f' % (
            sym, t, wr_pct, r, ev, stats['total_pnl']))

# 生成建议注册表
print()
print('[建议新 Kelly 注册表]')
print('KELLY_REGISTRY = {')

# 正 EV 品种
for sym, ev, w, l, pnl in tradable:
    t = w + l
    w_pct = w/t
    aw = np.mean(sym_stats[sym]['win_amt'])
    al = abs(np.mean(sym_stats[sym]['loss_amt']))
    r = aw/al if al > 0 else 0
    k = w_pct - (1-w_pct)/r if r > 0 else 0
    print("    '%s':  {'W': %.2f, 'R': %.2f, 'kf': %.3f},  # %d笔, $%.2f, EV=%.3f" % (
        sym, w_pct, r, k, t, pnl, ev))

# 样本不足但正 EV 的
for sym, ev, w, l, pnl in micro_test:
    if ev > 0:
        t = w + l
        w_pct = w/t if t > 0 else 0
        aw = np.mean(sym_stats[sym]['win_amt']) if sym_stats[sym]['win_amt'] else 0
        al = abs(np.mean(sym_stats[sym]['loss_amt'])) if sym_stats[sym]['loss_amt'] else 1
        r = aw/al if al > 0 else 0
        k = w_pct - (1-w_pct)/r if r > 0 else 0
        print("    '%s':  {'W': %.2f, 'R': %.2f, 'kf': %.3f},  # %d笔(样本不足), $%.2f, EV=%.3f" % (
            sym, w_pct, r, k, t, pnl, ev))

print('}')

mt5.shutdown()
