"""
持仓品种 K 线快速分析
"""

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime
import sys
import io
import warnings
warnings.filterwarnings('ignore')

# 设置 UTF-8 输出
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

if not mt5.initialize():
    print("MT5 初始化失败")
    exit()

symbols = ["NZDUSD", "AUDUSD", "USDCHF"]

print("=" * 80)
print("持仓品种 K 线分析")
print(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)

for symbol in symbols:
    print(f"\n{'='*80}")
    print(f"{symbol} 分析")
    print(f"{'='*80}")
    
    # 获取 H1 数据
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 200)
    if rates is None or len(rates) == 0:
        print("无法获取数据")
        continue
    
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    df.set_index('time', inplace=True)
    
    # 计算指标
    df['MA20'] = df['close'].rolling(window=20).mean()
    df['MA50'] = df['close'].rolling(window=50).mean()
    df['MA200'] = df['close'].rolling(window=200).mean()
    
    # RSI
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # MACD
    df['EMA12'] = df['close'].ewm(span=12).mean()
    df['EMA26'] = df['close'].ewm(span=26).mean()
    df['MACD'] = df['EMA12'] - df['EMA26']
    df['MACD_Signal'] = df['MACD'].ewm(span=9).mean()
    df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']
    
    # ATR
    high_low = df['high'] - df['low']
    high_close = np.abs(df['high'] - df['close'].shift())
    low_close = np.abs(df['low'] - df['close'].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = np.max(ranges, axis=1)
    df['ATR'] = true_range.rolling(window=14).mean()
    
    latest = df.iloc[-1]
    prev = df.iloc[-2]
    
    # 趋势分析
    if latest['close'] > latest['MA50'] > latest['MA200']:
        trend = "上升趋势 [OK]"
    elif latest['close'] < latest['MA50'] < latest['MA200']:
        trend = "下降趋势 [NO]"
    else:
        trend = "横盘震荡 [WAIT]"
    
    # RSI 状态
    if latest['RSI'] > 70:
        rsi_status = "超买 (警惕回调)"
    elif latest['RSI'] < 30:
        rsi_status = "超卖 (可能反弹)"
    elif latest['RSI'] > 50:
        rsi_status = "偏强"
    else:
        rsi_status = "偏弱"
    
    # MACD 状态
    if latest['MACD_Hist'] > 0:
        macd_status = "看涨"
    else:
        macd_status = "看跌"
    
    # K 线形态
    body = latest['close'] - latest['open']
    body_size = abs(body)
    total_range = latest['high'] - latest['low']
    
    pattern = "普通 K 线"
    if body_size < total_range * 0.1:
        pattern = "十字星 (市场犹豫)"
    elif body > 0 and body_size > total_range * 0.7:
        pattern = "大阳线 (强势)"
    elif body < 0 and body_size > total_range * 0.7:
        pattern = "大阴线 (弱势)"
    
    # 支撑阻力
    recent_lows = df['low'].rolling(window=20).min()
    recent_highs = df['high'].rolling(window=20).max()
    support = recent_lows.iloc[-1]
    resistance = recent_highs.iloc[-1]
    
    # 打印分析
    print(f"当前价格：{latest['close']:.5f}")
    print(f"趋势：{trend}")
    print(f"RSI: {latest['RSI']:.2f} - {rsi_status}")
    print(f"MACD: {macd_status} (柱状图：{latest['MACD_Hist']:.5f})")
    print(f"K 线形态：{pattern}")
    print(f"支撑位：{support:.5f}")
    print(f"阻力位：{resistance:.5f}")
    print(f"ATR (波动率): {latest['ATR']:.5f}")
    
    # 交易建议
    print(f"\n交易建议:")
    if trend == "上升趋势 [OK]" and latest['RSI'] < 70 and latest['MACD_Hist'] > 0:
        print("  [持有多单] - 趋势向好，继续持有")
    elif trend == "下降趋势 [NO]" and latest['RSI'] > 30 and latest['MACD_Hist'] < 0:
        print("  [考虑离场] - 趋势转弱，建议平仓")
    else:
        print("  [观望/持有] - 等待明确信号")

print("\n" + "=" * 80)
mt5.shutdown()
