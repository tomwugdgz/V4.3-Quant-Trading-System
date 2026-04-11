# -*- coding: utf-8 -*-
"""
市场扫描 + K 线分析汇总
"""
import MetaTrader5 as mt5
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

if not mt5.initialize():
    print("MT5 初始化失败")
    exit()

print("=" * 80)
print("市场扫描 + K 线分析汇总")
print(f"时间：{mt5.symbol_info_tick('EURUSD').time}")
print("=" * 80)

symbols = ["EURUSD", "GBPUSD", "AUDUSD", "USDCHF", "USDJPY", "NZDUSD"]

for symbol in symbols:
    # 获取 H1 数据
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 100)
    if rates is None:
        continue
    
    import pandas as pd
    import numpy as np
    
    df = pd.DataFrame(rates)
    df['MA50'] = df['close'].rolling(window=50).mean()
    df['MA200'] = df['close'].rolling(window=200).mean()
    
    # RSI
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    latest = df.iloc[-1]
    
    # 趋势
    if latest['close'] > latest['MA50'] > latest['MA200']:
        trend = "上升趋势"
    elif latest['close'] < latest['MA50'] < latest['MA200']:
        trend = "下降趋势"
    else:
        trend = "横盘"
    
    # RSI 状态
    if latest['RSI'] > 70:
        rsi_status = "超买"
    elif latest['RSI'] < 30:
        rsi_status = "超卖"
    else:
        rsi_status = "中性"
    
    print(f"\n{symbol}:")
    print(f"  价格：{latest['close']:.5f}")
    print(f"  趋势：{trend}")
    print(f"  RSI: {latest['RSI']:.2f} ({rsi_status})")

mt5.shutdown()
print("\n" + "=" * 80)
