"""
旺财交易系统 — 进化引擎 v0.1
复制 | 变异 | 竞争 | 生存

策略：变异参数 → 回测评估 → 保留最优 → 淘汰失败
"""

import MetaTrader5 as mt5, pandas as pd, numpy as np
from datetime import datetime
from itertools import product

mt5.initialize(login=52797683, server='ICMarketsSC-Demo', timeout=10000)

# ============================================================
# 第一阶段：复制 — 建立基准（v2.2 当前参数）
# ============================================================

def calc_atr(df):
    hi, lo, cl = df['high'], df['low'], df['close']
    tr1 = hi - lo
    tr2 = abs(hi - cl.shift(1))
    tr3 = abs(lo - cl.shift(1))
    tr = np.maximum(np.maximum(tr1, tr2), tr3)
    return tr.rolling(14).mean()

def calc_signal(df_d1, df_h4, df_h1):
    """返回 direction, strength"""
    try:
        ema20 = df_d1['close'].ewm(span=20).mean().iloc[-1]
        ema50 = df_d1['close'].ewm(span=50).mean().iloc[-1]
        price = df_d1['close'].iloc[-1]
        d1_bull = ema20 > ema50 and price > ema20
        d1_bear = ema20 < ema50 and price < ema20
        if not d1_bull and not d1_bear:
            return None, 0

        direction = "BUY" if d1_bull else "SELL"

        delta4 = df_h4['close'].diff()
        gain4 = delta4.clip(lower=0).rolling(14).mean()
        loss4 = (-delta4.clip(upper=0)).rolling(14).mean()
        rs4 = gain4 / loss4.replace(0, np.nan)
        h4_rsi = (100 - 100 / (1 + rs4)).iloc[-1]

        hi, lo, cl = df_h1['high'], df_h1['low'], df_h1['close']
        tr1 = hi - lo
        tr2 = abs(hi - cl.shift(1))
        tr3 = abs(lo - cl.shift(1))
        tr = np.maximum(np.maximum(tr1, tr2), tr3)
        atr = tr.rolling(14).mean()
        plus_dm = hi.diff().clip(lower=0)
        minus_dm = (-lo.diff()).clip(upper=0)
        plus_di = 100 * plus_dm.rolling(14).mean() / atr.replace(0, np.nan)
        minus_di = 100 * minus_dm.rolling(14).mean() / atr.replace(0, np.nan)
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di).replace(0, np.nan)
        adx = dx.rolling(14).mean().iloc[-1]

        if not np.isfinite(adx) or adx < 25:
            return None, 0

        score = 0
        if d1_bull: score += 3
        elif d1_bear: score -= 3
        if (h4_rsi < 35 and d1_bull) or (h4_rsi > 65 and d1_bear): score += 2
        elif 35 <= h4_rsi <= 65: score += 1
        if adx > 25: score += 2

        strength = max(0, (abs(score) - 2) / 8 * 1.5) * 100
        return direction, round(strength, 1)
    except:
        return None, 0

def backtest_symbol(sym, jpy_sl_mult, jpy_min_sl, nonjpy_sl_mult, nonjpy_min_sl,
                    test_days=7, threshold=15):
    """
    回测单个品种N天
    返回: (总盈亏pips, 交易次数, 胜率, 盈亏比)
    """
    is_jpy = sym in ['USDJPY','AUDJPY','EURJPY','GBPJPY','NZDJPY','CADJPY','CHFJPY']
    pip_size = 0.01 if is_jpy else 0.0001

    # 获取足够历史数据
    bars_per_day = 24  # H1
    n_bars = bars_per_day * (test_days + 30)  # 多拿30天预热

    rates = mt5.copy_rates_from_pos(sym, mt5.TIMEFRAME_H1, 0, n_bars)
    if rates is None or len(rates) < 200:
        return None

    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    df.set_index('time', inplace=True)

    # ATR
    df['atr'] = calc_atr(df)

    # 多时间框架信号需要D1/H4
    d1_rates = mt5.copy_rates_from_pos(sym, mt5.TIMEFRAME_D1, 0, test_days + 30)
    h4_rates = mt5.copy_rates_from_pos(sym, mt5.TIMEFRAME_H4, 0, (test_days + 30) * 6)
    if d1_rates is None or h4_rates is None:
        return None

    df_d1 = pd.DataFrame(d1_rates)
    df_h4 = pd.DataFrame(h4_rates)

    # 从测试日开始（前30天预热）
    test_start = len(df) - bars_per_day * test_days

    trades = []
    in_pos = False
    entry_price = 0
    entry_dir = None

    for i in range(30, len(df)):  # 从第30根开始（ATR预热）
        if i < test_start:
            continue

        row = df.iloc[i]
        if pd.isna(row['atr']):
            continue

        # 获取同时刻的D1/H4
        t = row.name
        d1_idx = df_d1[df_d1['time'] <= t.timestamp()].index
        h4_idx = df_h4[df_h4['time'] <= t.timestamp()].index

        if len(d1_idx) == 0 or len(h4_idx) == 0:
            continue

        d1_slice = df_d1.loc[:t.timestamp()].tail(50)
        h4_slice = df_h4.loc[:t.timestamp()].tail(50)

        direction, strength = calc_signal(d1_slice, h4_slice, df.iloc[max(0,i-50):i].tail(50))

        if direction is None or strength < threshold:
            continue

        if not in_pos:
            # 计算止损
            atr_pips = row['atr'] / pip_size
            if is_jpy:
                sl_pips = max(atr_pips * jpy_sl_mult, jpy_min_sl)
            else:
                sl_pips = max(atr_pips * nonjpy_sl_mult, nonjpy_min_sl)
            tp_pips = sl_pips * 2.0

            in_pos = True
            entry_price = row['close']
            entry_dir = direction
            sl_price = entry_price + sl_pips * pip_size if direction == "SELL" else entry_price - sl_pips * pip_size
            tp_price = entry_price - tp_pips * pip_size if direction == "SELL" else entry_price + tp_pips * pip_size

        else:
            high, low = row['high'], row['low']

            if entry_dir == "SELL":
                if high >= sl_price:
                    pnl = -(sl_price - entry_price) / pip_size
                    trades.append({'result': 'SL', 'pnl': pnl, 'dir': entry_dir})
                    in_pos = False
                elif low <= tp_price:
                    pnl = (entry_price - tp_price) / pip_size
                    trades.append({'result': 'TP', 'pnl': pnl, 'dir': entry_dir})
                    in_pos = False
            else:  # BUY
                if low <= sl_price:
                    pnl = -(entry_price - sl_price) / pip_size
                    trades.append({'result': 'SL', 'pnl': pnl, 'dir': entry_dir})
                    in_pos = False
                elif high >= tp_price:
                    pnl = (tp_price - entry_price) / pip_size
                    trades.append({'result': 'TP', 'pnl': pnl, 'dir': entry_dir})
                    in_pos = False

    if not trades:
        return (0, 0, 0, 0)

    total_pnl = sum(t['pnl'] for t in trades)
    wins = [t for t in trades if t['pnl'] > 0]
    losses = [t for t in trades if t['pnl'] <= 0]
    win_rate = len(wins) / len(trades) * 100 if trades else 0
    avg_win = sum(t['pnl'] for t in wins) / len(wins) if wins else 0
    avg_loss = sum(t['pnl'] for t in losses) / len(losses) if losses else 0
    rr = abs(avg_win / avg_loss) if avg_loss != 0 else 0

    return (round(total_pnl, 2), len(trades), round(win_rate, 1), round(rr, 2))

# ============================================================
# 第二阶段：变异 — 生成候选参数组合
# ============================================================

print("=" * 60)
print("旺财进化引擎 v0.1 — JPY品种优化")
print("=" * 60)

# 变异空间
JPY_ATR_MULT_RANGE = [1.5, 2.0, 2.5]  # JPY ATR倍数
JPY_MIN_SL_RANGE = [20, 25, 30]       # JPY 最低SL(pip)
THRESHOLD_RANGE = [12, 15, 18]         # 信号门槛%

variants = list(product(JPY_ATR_MULT_RANGE, JPY_MIN_SL_RANGE, THRESHOLD_RANGE))
print(f"\n生成 {len(variants)} 个候选变体")

# 测试品种
JPY_TEST = ['AUDJPY', 'USDJPY', 'EURJPY', 'GBPJPY']

# 历史基准数据（5月1日-7日）
# 从MT5获取历史数据来验证
print("\n开始回测（最近7天）...")

results = []
for idx, (atr_mult, min_sl, thresh) in enumerate(variants):
    variant_name = f"v{idx+1}_ATR{atr_mult}_minSL{min_sl}_th{thresh}"
    variant_result = {'name': variant_name, 'atr_mult': atr_mult,
                      'min_sl': min_sl, 'thresh': thresh, 'symbols': {}}

    total_pnl = 0
    total_trades = 0
    total_wins = 0

    for sym in JPY_TEST:
        res = backtest_symbol(sym, atr_mult, min_sl, 1.5, 15,
                             test_days=7, threshold=thresh)
        if res is None:
            variant_result['symbols'][sym] = {'pnl': 0, 'trades': 0}
            continue

        pnl, n, wr, rr = res
        variant_result['symbols'][sym] = {'pnl': pnl, 'trades': n, 'winrate': wr, 'rr': rr}
        total_pnl += pnl
        total_trades += n

    variant_result['total_pnl'] = total_pnl
    variant_result['total_trades'] = total_trades
    results.append(variant_result)

    print(f"  [{idx+1:2d}/{len(variants)}] {variant_name}: 总Pnl={total_pnl:+.1f}pip ({total_trades}笔)")

# ============================================================
# 第三阶段：竞争 & 生存 — 排名淘汰
# ============================================================

results.sort(key=lambda x: -x['total_pnl'])

print("\n" + "=" * 60)
print("进化结果排名（按总盈亏）")
print("=" * 60)
print(f"{'排名':<4} {'变体名称':<30} {'总Pnl(pip)':<12} {'交易次数':<8}")
print("-" * 60)

for rank, r in enumerate(results, 1):
    tag = "★★★" if rank <= 3 else "★★" if rank <= 6 else ""
    print(f"#{rank:<3} {r['name']:<30} {r['total_pnl']:>+8.1f}pip  {r['total_trades']:<8} {tag}")

# 最优变体
best = results[0]
worst = results[-1]

print(f"\n最优: {best['name']} → {best['total_pnl']:+.1f}pip")
print(f"最差: {worst['name']} → {worst['total_pnl']:+.1f}pip")

# 盈利变体
profitable = [r for r in results if r['total_pnl'] > 0]
print(f"\n盈利变体: {len(profitable)}/{len(results)}")

if profitable:
    print("\n===== 推荐参数（盈利变体）=====")
    for r in profitable[:5]:
        print(f"  {r['name']}: {r['total_pnl']:+.1f}pip | ATR×{r['atr_mult']} minSL={r['min_sl']} thresh={r['thresh']}")

    # 保存最优参数
    best_profitable = profitable[0]
    print(f"\n>>> 选用最优盈利参数: {best_profitable['name']}")
    print(f"    JPY ATR×{best_profitable['atr_mult']}, 最低SL={best_profitable['min_sl']}pip, 门槛={best_profitable['thresh']}%")
else:
    print("\n⚠️ 所有变体均亏损，保留v2.2基准参数")

mt5.shutdown()

# 保存结果到Wiki
import json
output = {
    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M'),
    'total_variants': len(variants),
    'profitable_count': len(profitable),
    'results': results[:10],  # 只保存前10
    'best': best if profitable else None,
    'param_space': {
        'JPY_ATR_MULT': JPY_ATR_MULT_RANGE,
        'JPY_MIN_SL': JPY_MIN_SL_RANGE,
        'THRESHOLD': THRESHOLD_RANGE
    }
}

print("\n结果已准备就绪，可写入Wiki")