import MetaTrader5 as mt5
from datetime import datetime, timezone, timedelta
from collections import defaultdict
import numpy as np

tz = timezone(timedelta(hours=8))
mt5.initialize(login=52797683, server='ICMarketsSC-Demo', timeout=10000)

info = mt5.account_info()
today_start = datetime.now(tz).replace(hour=0, minute=0, second=0, microsecond=0)
today_ts = int(today_start.timestamp())

# 获取所有历史
all_history = mt5.history_deals_get(0, int(datetime.now(tz).timestamp())) or []
closes = [d for d in all_history if d.entry == 1]

print('=' * 60)
print('第一性原理分析：期望值 = p*b - q')
print('=' * 60)
print()

# 按品种统计
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

# 总统计
total_wins = sum(s['wins'] for s in sym_stats.values())
total_losses = sum(s['losses'] for s in sym_stats.values())
total_trades = total_wins + total_losses
overall_wr = total_wins / total_trades * 100 if total_trades > 0 else 0
all_win_amt = [p for s in sym_stats.values() for p in s['win_amt']]
all_loss_amt = [p for s in sym_stats.values() for p in s['loss_amt']]
avg_win = np.mean(all_win_amt) if all_win_amt else 0
avg_loss = abs(np.mean(all_loss_amt)) if all_loss_amt else 0
R = avg_win / avg_loss if avg_loss > 0 else 0
W = total_wins / total_trades if total_trades > 0 else 0
kelly = W - (1-W)/R if R > 0 else 0
EV = W * R - (1-W)

print('【全局统计】(%d笔平仓)' % total_trades)
print('  胜率 W = %.1f%%' % (overall_wr))
print('  平均盈利 = $%.2f' % avg_win)
print('  平均亏损 = $%.2f' % avg_loss)
print('  盈亏比 R = %.2f' % R)
print('  Kelly f* = %.1f%%' % (kelly*100))
print('  期望值 EV = %.3f (正=有优势, 负=无优势)' % EV)
print()

# 按品种详细分析
print('【按品种第一性原理分析】')
print()
print('%-10s %4s %4s %4s %5s %8s %8s %5s %6s %6s %s' % (
    '品种', '总笔', 'W', 'L', '胜率%', '均盈$', '均亏$', 'R', 'Kelly', '期望值', '决策'))
print('-' * 100)

tradable = []
blocked = []

for sym, stats in sorted(sym_stats.items(), key=lambda x: x[1]['total_pnl'], reverse=True):
    w = stats['wins']
    l = stats['losses']
    t = w + l
    wr_pct = w/t*100 if t > 0 else 0
    aw = np.mean(stats['win_amt']) if stats['win_amt'] else 0
    al = abs(np.mean(stats['loss_amt'])) if stats['loss_amt'] else 0
    r = aw/al if al > 0 else 0
    w_pct = w/t if t > 0 else 0
    k = w_pct - (1-w_pct)/r if r > 0 else -999
    ev = w_pct * r - (1-w_pct)
    pnl = stats['total_pnl']

    if t >= 5 and ev > 0:
        decision = '✅ 交易'
        tradable.append(sym)
    elif t >= 5 and ev <= 0:
        decision = '🚫 禁止'
        blocked.append(sym)
    elif t < 5:
        decision = '⚠️ 样本不足'
    else:
        decision = '❓ 未知'

    print('%-10s %4d %4d %4d %5.1f%% %8.2f %8.2f %5.2f %6.1f%% %6.3f %s' % (
        sym, t, w, l, wr_pct, aw, al, r, k*100, ev, decision))

print()

print('【第一性原理结论】')
print()
print('期望值 > 0 的品种（可以交易）:')
if tradable:
    for s in tradable:
        st = sym_stats[s]
        print('  ✅ %s (%d笔, %.0f%%胜率, 盈亏$%.2f)' % (
            s, st['wins']+st['losses'], st['wins']/(st['wins']+st['losses'])*100, st['total_pnl']))
else:
    print('  ❌ 无！所有品种期望值都为负！')

print()
print('期望值 <= 0 的品种（必须禁止）:')
for s in blocked:
    st = sym_stats[s]
    print('  🚫 %s (%d笔, %.0f%%胜率, 盈亏$%.2f)' % (
        s, st['wins']+st['losses'], st['wins']/(st['wins']+st['losses'])*100, st['total_pnl']))

print()

# 核心问题诊断
print('【核心诊断】')
if EV <= 0:
    print('  🔴 全局期望值为负！系统没有优势！')
    print('  原因: 平均盈利($%.2f) < 平均亏损($%.2f)' % (avg_win, avg_loss))
    print('  解决方案:')
    print('    1. 加大止盈/止损比例（提高 R）')
    print('    2. 提高信号门槛（提高 W）')
    print('    3. 只交易期望值为正的品种')
else:
    print('  ✅ 全局期望值为正，系统有优势')

print()

# 生成新的 Kelly 注册表
print('【建议新 Kelly 注册表】')
print('KELLY_REGISTRY = {')
for sym, stats in sorted(sym_stats.items(), key=lambda x: x[1]['total_pnl'], reverse=True):
    w = stats['wins']
    l = stats['losses']
    t = w + l
    if t < 3:
        continue
    w_pct = w/t
    aw = np.mean(stats['win_amt']) if stats['win_amt'] else 0
    al = abs(np.mean(stats['loss_amt'])) if stats['loss_amt'] else 1
    r = aw/al if al > 0 else 0
    k = w_pct - (1-w_pct)/r if r > 0 else -999
    print("    '%s':  {'W': %.2f, 'R': %.2f, 'kf': %.3f},  # %d笔, 盈亏$%.2f" % (
        sym, w_pct, r, k, t, stats['total_pnl']))
print('}')

mt5.shutdown()
