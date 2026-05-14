import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import sys, io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

if not mt5.initialize(login=52797683, server='ICMarketsSC-Demo', timeout=10000):
    print("MT5 init failed")
    sys.exit()

def check_symbol(symbol):
    si = mt5.symbol_info(symbol)
    d1 = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_D1, 0, 100)
    h1 = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 50)
    
    if d1 is None or h1 is None:
        print(f"{symbol}: 数据不足")
        return
    
    d1_df = pd.DataFrame(d1)
    h1_df = pd.DataFrame(h1)
    
    # 价格范围
    d1_high = d1_df['high'].max()
    d1_low = d1_df['low'].min()
    d1_range = d1_high - d1_low
    d1_avg = d1_df['close'].mean()
    
    h1_high = h1_df['high'].max()
    h1_low = h1_df['low'].min()
    h1_range = h1_high - h1_low
    h1_avg = h1_df['close'].mean()
    
    # ATR (H1)
    tr1 = h1_df['high'] - h1_df['low']
    tr2 = abs(h1_df['high'] - h1_df['close'].shift(1))
    tr3 = abs(h1_df['low'] - h1_df['close'].shift(1))
    tr = np.maximum(np.maximum(tr1, tr2), tr3)
    atr = tr.rolling(14).mean().iloc[-1]
    
    # ATR 百分比
    atr_pct = (atr / h1_avg) * 100
    
    print(f"\n{symbol} (digits={si.digits}, point={si.point}):")
    print(f"  D1: 高={d1_high:.5f} 低={d1_low:.5f} 范围={d1_range:.5f} 均值={d1_avg:.5f}")
    print(f"  H1: 高={h1_high:.5f} 低={h1_low:.5f} 范围={h1_range:.5f} 均值={h1_avg:.5f}")
    print(f"  ATR(H1): {atr:.5f} ({atr_pct:.3f}%)")
    
    # EMA 信号
    ema20 = d1_df['close'].ewm(span=20).mean().iloc[-1]
    ema50 = d1_df['close'].ewm(span=50).mean().iloc[-1]
    price = d1_df['close'].iloc[-1]
    
    print(f"  EMA20={ema20:.5f} EMA50={ema50:.5f} Price={price:.5f}")
    print(f"  D1趋势: {'Bullish' if ema20 > ema50 and price > ema20 else 'Bearish' if ema20 < ema50 and price < ema20 else 'Neutral'}")

# 检查所有品种
symbols = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "AUDJPY", "EURJPY", "GBPJPY", "USDCHF"]
for sym in symbols:
    check_symbol(sym)

mt5.shutdown()
