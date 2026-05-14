import MetaTrader5 as mt5, pandas as pd, numpy as np
from datetime import datetime

mt5.initialize(login=52797683, server='ICMarketsSC-Demo', timeout=10000)

sym = 'AUDJPY'
# 获取长期数据
rates = mt5.copy_rates_from_pos(sym, mt5.TIMEFRAME_H1, 0, 2000)
df = pd.DataFrame(rates)
df['time'] = pd.to_datetime(df['time'], unit='s')

# 指标
df['atr14'] = np.maximum(df['high'] - df['low'],
    np.maximum(abs(df['high'] - df['close'].shift(1)),
               abs(df['low'] - df['close'].shift(1)))).rolling(14).mean()
df['ema20'] = df['close'].ewm(span=20).mean().mean()
delta = df['close'].diff(14)
rs = delta.where(delta > 0, 0).rolling(14).mean() / (-delta.where(delta < 0, 0)).rolling(14).mean().replace(0, 0.001)
df['rsi14'] = (100 - (100 / (1 + rs))).mean()
df['ema_fast'] = df['close'].ewm(span=5).mean()
df['ema_slow'] = df['close'].ewm(span=20).mean()

# 获取当前值
tick = mt5.symbol_info_tick(sym)
rates_r = mt5.copy_rates_from_pos(sym, mt5.TIMEFRAME_H1, 0, 100)
df_r = pd.DataFrame(rates_r)

hi, lo, cl = df_r['high'], df_r['low'], df_r['close']
tr1 = hi - lo; tr2 = abs(hi - cl.shift(1)); tr3 = abs(lo - cl.shift(1))
tr = np.maximum(np.maximum(tr1, tr2), tr3)
atr_now = tr.rolling(14).mean().iloc[-1]

ema_fast_now = df_r['close'].ewm(span=5).mean().iloc[-1]
ema_slow_now = df_r['close'].ewm(span=20).mean().iloc[-1]
delta = df_r['close'].diff(14)
gain = delta.where(delta > 0, 0).rolling(14).mean()
loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
rs_now = gain / loss.replace(0, 0.001)
rsi_now = (100 - (100 / (1 + rs_now))).iloc[-1]

# D1 trend判断
rates_d1 = mt5.copy_rates_from_pos(sym, mt5.TIMEFRAME_D1, 0, 30)
df_d1 = pd.DataFrame(rates_d1)
ema_d1_20 = df_d1['close'].ewm(span=20).mean().iloc[-1]
current_price_d1 = df_d1['close'].iloc[-1]
d1_trend = 'UP' if current_price_d1 > ema_d1_20 else 'DOWN'

# ATR pips
atr_pips = atr_now / 0.01

print("=== AUDJPY 多周期分析 ===")
print(f"当前价格: {tick.bid:.3f}")
print(f"D1 EMA20: {ema_d1_20:.3f} | D1趋势: {d1_trend}")
print(f"H1 ATR: {atr_pips:.1f}pips")
print(f"H1 EMA5: {ema_fast_now:.3f} | H1 EMA20: {ema_slow_now:.3f}")
print(f"H1 RSI: {rsi_now:.1f}")
print()

# 核心问题诊断
print("=== 核心问题诊断 ===")
# 5月6日AUDJPY发生了什么？
print("5月6日AUDJPY状态:")
# 查5月6日的数据
may6_start = int(datetime(2026,5,6,0).timestamp())
may6_end = int(datetime(2026,5,7,0).timestamp())
may6_deals = mt5.history_deals_get(may6_start, may6_end)
audjpy_may6 = [d for d in may6_deals if d.symbol == 'AUDJPY']
for d in audjpy_may6:
    tag = d.comment.strip('[]') if d.comment else ''
    t = datetime.fromtimestamp(d.time).strftime('%H:%M')
    print(f"  {t} {'BUY' if d.type==0 else 'SELL'} {float(d.volume):.2f} @{d.price_open:.3f} -> pnl=${float(d.profit):.2f} [{tag}]")

print()
print("=== AUDJPY 为什么5月6日SELL能赚钱 ===")
# 5月6日10:07 AUDJPY SELL @ 113.549 TP -> 赚钱了
# 说明那时候是下跌趋势
# 但18:46/18:52/18:53连续BUY 3单 -> 说明系统判断错了方向

# 查5月6日的价格走势
may6_rates = mt5.copy_rates_from_pos(sym, mt5.TIMEFRAME_H1, 0, 24*30)  # 最近30天
df_m6 = pd.DataFrame(may6_rates)
# 找到5月6日的数据
m6_data = [r for r in may6_rates if datetime.fromtimestamp(r['time']).date() == datetime(2026,5,6).date()]
if m6_data:
    df_m6day = pd.DataFrame(m6_data)
    m6_ema20 = df_m6day['close'].ewm(span=20).mean().mean()
    m6_rsi = rsi_now  # 简化
    print(f"5月6日AUDJPY收盘: {df_m6day['close'].iloc[-1]:.3f}")
    print(f"5月6日AUDJPY EMA20: {m6_ema20:.3f}")
    
    # 5月6日走势: 开盘大概水平，然后?
    high = df_m6day['high'].max()
    low = df_m6day['low'].min()
    close = df_m6day['close'].iloc[-1]
    open_ = df_m6day['open'].iloc[0]
    print(f"5月6日 O:{open_:.3f} H:{high:.3f} L:{low:.3f} C:{close:.3f}")
    
    if close < open_:
        print("-> 阴线（下跌）SELL赚钱合理")
    else:
        print("-> 阳线（上涨）SELL赚钱说明是反弹后回落")

print()
print("=== v2.1 AUDJPY JPY止损优化方案 ===")
print()
print("当前问题:")
print("  1. AUDJPY 日均波动82pips，15pip SL几乎必打")
print("  2. 5月6日连续3单BUY全是亏损（方向判断错误）")
print("  3. SELL信号(RSI>70)在趋势市场被碾压")
print()
print("优化方案:")
print("  A. 趋势确认: 必须D1 EMA确认方向才开仓")
print("  B. SL加宽: AUDJPY用 ATR*1.5 (约22pip) 替代固定15pip")
print("  C. 波动率门控: ATR当前值>16才开仓（避免低波动假信号）")
print("  D. 信号方向: RSI>75(而非70)才触发SELL，减少假信号")
print()

# 测试优化方案
print("=== 优化方案回测 ===")
trades_opt = []
in_pos = False

for i in range(50, len(df_r)):
    row = df_r.iloc[i]
    prev = df_r.iloc[i-1]
    
    if pd.isna(row.get('atr14')):
        continue
    
    atr_now_r = row['atr14'] if 'atr14' in row else tr.rolling(14).mean().iloc[i] if i < len(tr) else atr_now
    
    # 波动率门控: ATR > 16 pips
    if atr_now_r / 0.01 < 16:
        continue
    
    # 信号: EMA空头 + RSI > 75 (更严格)
    ema5 = row['close'] if 'ema_fast' not in row else row['ema_fast']
    ema20 = row['close'] if 'ema_slow' not in row else row['ema_slow']
    
    if in_pos:
        high = row['high']
        low = row['low']
        sl_pips_v = 22  # 优化后的SL
        
        if high >= entry_price + sl_pips_v * 0.01:
            trades_opt.append({'result': 'SL', 'rr': 0})
            in_pos = False
        elif low <= entry_price - sl_pips_v * 0.01 * 2:
            trades_opt.append({'result': 'TP', 'rr': 2})
            in_pos = False

print(f"优化方案测试: {len(trades_opt)}笔交易")

mt5.shutdown()