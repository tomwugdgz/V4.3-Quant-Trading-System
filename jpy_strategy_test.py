import MetaTrader5 as mt5, pandas as pd, numpy as np
from datetime import datetime

mt5.initialize(login=52797683, server='ICMarketsSC-Demo', timeout=10000)

sym = 'AUDJPY'
# 获取更多数据做回测
rates = mt5.copy_rates_from_pos(sym, mt5.TIMEFRAME_H1, 0, 2000)
df = pd.DataFrame(rates)
df['time'] = pd.to_datetime(df['time'], unit='s')
df.set_index('time', inplace=True)

# ATR
df['tr'] = np.maximum(df['high'] - df['low'],
    np.maximum(abs(df['high'] - df['close'].shift(1)),
               abs(df['low'] - df['close'].shift(1))))
df['atr14'] = df['tr'].rolling(14).mean()

# EMA 20
df['ema20'] = df['close'].ewm(span=20).mean()
# RSI 14
delta = df['close'].diff(14)
gain = delta.where(delta > 0, 0).rolling(14).mean()
loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
rs = gain / loss.replace(0, 0.001)
df['rsi14'] = 100 - (100 / (1 + rs))

# 信号
df['ema_bull'] = df['close'] > df['ema20']
df['ema_bear'] = df['close'] < df['ema20']

# 只做SELL（顺势）
# SELL信号: price > EMA20 (反弹做空) + RSI > 65
# SL: recent high + ATR buffer
# TP: recent swing low - ATR

print("=== AUDJPY SELL顺势策略回测（最近500根K线）===")
trades = []
in_pos = False
entry_price = 0
sl_price = 0
tp_price = 0

for i in range(50, len(df)):
    row = df.iloc[i]
    prev = df.iloc[i-1]
    
    if pd.isna(row['atr14']) or pd.isna(row['rsi14']):
        continue
    
    # SELL信号: EMA空头(price<ema) + RSI>65
    # 但顺势我们找的是: price突破EMA后回调做空
    # 更简单: 找RSI>70的超涨，做SELL
    if not in_pos and row['rsi14'] > 70 and row['close'] > row['ema20']:
        # 入场SELL
        entry = row['close']
        atr = row['atr14']
        sl = entry + 0.25 * atr  # SL在价格上方25% ATR
        tp = entry - 0.50 * atr   # TP在价格下方50% ATR
        
        in_pos = True
        entry_price = entry
        sl_price = sl
        tp_price = tp
        
    elif in_pos:
        # 检查是否触发了SL或TP
        high = row['high']
        low = row['low']
        
        if high >= sl_price:
            # SL触发
            pnl = -(sl_price - entry_price) / 0.01
            trades.append({'result': 'SL', 'pnl_pips': pnl, 'sym': sym})
            in_pos = False
        elif low <= tp_price:
            # TP触发
            pnl = (entry_price - tp_price) / 0.01
            trades.append({'result': 'TP', 'pnl_pips': pnl, 'sym': sym})
            in_pos = False

print(f"SELL顺势策略: {len(trades)}笔交易")
win = [t for t in trades if t['pnl_pips'] > 0]
lose = [t for t in trades if t['pnl_pips'] <= 0]
print(f"盈利: {len(win)}笔 | 亏损: {len(lose)}笔")
if trades:
    avg = sum(t['pnl_pips'] for t in trades) / len(trades)
    print(f"平均Pips: {avg:.1f}")

print()
print("=== AUDJPY RSI超卖做SELL策略（更保守）===")
# 更保守的策略: RSI>75 + 价格距EMA>1% 才做SELL
# 这意味着价格已经大幅偏离均线，可能是假突破
trades2 = []
in_pos2 = False

for i in range(50, len(df)):
    row = df.iloc[i]
    
    if pd.isna(row['atr14']) or pd.isna(row['rsi14']):
        continue
    
    # 找最近30根K线的最低价（作为TP参考）
    recent_low = df.iloc[i-20:i]['low'].min()
    recent_high = df.iloc[i-20:i]['high'].max()
    range_pips = (recent_high - recent_low) / 0.01
    
    if not in_pos2:
        # SELL信号: RSI>75 + 价格距EMA偏离>1.5%
        ema_dist = (row['close'] - row['ema20']) / row['ema20'] * 100
        if row['rsi14'] > 75 and ema_dist > 1.5:
            entry = row['close']
            # SL用最近20根最高价 + 10pip缓冲
            sl = recent_high + 0.10  # 10pip缓冲
            # TP用近期低点下方
            tp = recent_low - 0.15
            
            sl_pips = (sl - entry) / 0.01
            tp_pips = (entry - tp) / 0.01
            rr = tp_pips / sl_pips if sl_pips > 0 else 0
            
            # 只接受RR>=1.5的信号
            if rr >= 1.5:
                in_pos2 = True
                entry_price = entry
                sl_price = sl
                tp_price = tp
                
    elif in_pos2:
        high = row['high']
        low = row['low']
        
        if high >= sl_price:
            pnl = -(sl_price - entry_price) / 0.01
            trades2.append({'result': 'SL', 'pnl_pips': pnl})
            in_pos2 = False
        elif low <= tp_price:
            pnl = (entry_price - tp_price) / 0.01
            trades2.append({'result': 'TP', 'pnl_pips': pnl})
            in_pos2 = False

print(f"保守SELL策略(RSI>75+EMA偏离>1.5%+RR>=1.5): {len(trades2)}笔交易")
win2 = [t for t in trades2 if t['pnl_pips'] > 0]
lose2 = [t for t in trades2 if t['pnl_pips'] <= 0]
print(f"盈利: {len(win2)}笔 | 亏损: {len(lose2)}笔")
if trades2:
    avg2 = sum(t['pnl_pips'] for t in trades2) / len(trades2)
    print(f"平均Pips: {avg2:.1f}")

print()
print("=== 当前AUDJPY市场状态 ===")
tick = mt5.symbol_info_tick(sym)
rates_recent = mt5.copy_rates_from_pos(sym, mt5.TIMEFRAME_H1, 0, 30)
df_r = pd.DataFrame(rates_recent)
hi, lo, cl = df_r['high'], df_r['low'], df_r['close']
tr1 = hi - lo; tr2 = abs(hi - cl.shift(1)); tr3 = abs(lo - cl.shift(1))
tr = np.maximum(np.maximum(tr1, tr2), tr3)
atr_now = tr.rolling(14).mean().iloc[-1]
atr_pips = atr_now / 0.01

print(f"当前价格: {tick.bid:.3f}")
print(f"ATR(14): {atr_pips:.1f}pips")
print(f"EMA(20): 计算中...")
ema20_now = df_r['close'].ewm(span=20).mean().iloc[-1]
delta = df_r['close'].diff(14)
gain = delta.where(delta > 0, 0).rolling(14).mean()
loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
rs = gain / loss.replace(0, 0.001)
rsi_now = (100 - (100 / (1 + rs))).iloc[-1]

recent_low_20 = df_r['low'].min()
recent_high_20 = df_r['high'].max()

print(f"EMA(20): {ema20_now:.3f}")
print(f"RSI(14): {rsi_now:.1f}")
print(f"20根最低: {recent_low_20:.3f}")
print(f"20根最高: {recent_high_20:.3f}")
print(f"距EMA偏离: {(tick.bid - ema20_now)/ema20_now*100:.2f}%")

mt5.shutdown()