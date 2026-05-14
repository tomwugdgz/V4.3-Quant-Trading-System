#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
寻找交易机会 - 扫描所有品种的信号强度
"""

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime

# 连接 MT5
if not mt5.initialize():
    print(f"MT5 connection failed: {mt5.last_error()}")
    exit(1)

print("="*70)
print("Market Signal Scanner")
print("="*70)

# 扫描的品种（已移除加密货币）
symbols = [
    'EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'AUDUSD', 'NZDUSD',  # 外汇
    'XAUUSD', 'XAGUSD'   # 贵金属
]

def calculate_signal_strength(df, symbol, h1_df=None):
    """
    计算信号强度 (基于多指标组合)
    
    返回：
    - signal: BUY/SELL/NONE
    - strength: 信号强度 (0-1)
    - reasons: 信号原因
    - allowed_direction: 允许的交易方向 (基于趋势过滤)
    """
    if len(df) < 30:
        return None, 0, [], None
    
    latest = df.iloc[-1]
    prev = df.iloc[-2]
    
    reasons = []
    score = 0
    
    # 【铁律 5】趋势过滤器 (H1 EMA200)
    allowed_direction = None
    if h1_df is not None and len(h1_df) >= 200:
        ema200_h1 = h1_df['close'].ewm(span=200, min_periods=1).mean().iloc[-1]
        current_price = latest['close']
        
        if current_price > ema200_h1 * 1.001:  # 1% 容差
            allowed_direction = 'BUY'
            reasons.append(f"✅ 趋势：多头 (价格>{ema200_h1:.5f})")
        elif current_price < ema200_h1 * 0.999:
            allowed_direction = 'SELL'
            reasons.append(f"✅ 趋势：空头 (价格<{ema200_h1:.5f})")
        else:
            allowed_direction = 'NONE'
            reasons.append(f"⚠️ 趋势：震荡 (价格接近 EMA200)")
    else:
        reasons.append("⚠️ 无 H1 数据，跳过趋势过滤")
    
    # 1. 均线系统 (EMA 20/50)
    ema20 = df['close'].ewm(span=20, min_periods=1).mean().iloc[-1]
    ema50 = df['close'].ewm(span=50, min_periods=1).mean().iloc[-1]
    ema20_prev = df['close'].ewm(span=20, min_periods=1).mean().iloc[-2]
    ema50_prev = df['close'].ewm(span=50, min_periods=1).mean().iloc[-2]
    
    if ema20 > ema50:
        score += 1
        reasons.append("EMA20 > EMA50 (Bullish)")
    elif ema20 < ema50:
        score -= 1
        reasons.append("EMA20 < EMA50 (Bearish)")
    
    # 金叉/死叉
    if ema20_prev <= ema50_prev and ema20 > ema50:
        score += 2
        reasons.append("Golden Cross!")
    elif ema20_prev >= ema50_prev and ema20 < ema50:
        score -= 2
        reasons.append("Death Cross!")
    
    # 2. RSI (14)
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14, min_periods=1).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14, min_periods=1).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    rsi_latest = rsi.iloc[-1]
    
    if rsi_latest < 30:
        score += 2
        reasons.append(f"RSI Oversold ({rsi_latest:.1f})")
    elif rsi_latest > 70:
        score -= 2
        reasons.append(f"RSI Overbought ({rsi_latest:.1f})")
    
    # 3. MACD
    ema12 = df['close'].ewm(span=12, min_periods=1).mean()
    ema26 = df['close'].ewm(span=26, min_periods=1).mean()
    macd = ema12 - ema26
    signal_line = macd.ewm(span=9, min_periods=1).mean()
    
    macd_latest = macd.iloc[-1]
    signal_latest = signal_line.iloc[-1]
    macd_prev = macd.iloc[-2]
    signal_prev = signal_line.iloc[-2]
    
    if macd_latest > signal_latest:
        score += 1
        reasons.append("MACD > Signal")
    else:
        score -= 1
        reasons.append("MACD < Signal")
    
    # MACD 交叉
    if macd_prev <= signal_prev and macd_latest > signal_latest:
        score += 2
        reasons.append("MACD Bullish Cross!")
    elif macd_prev >= signal_prev and macd_latest < signal_latest:
        score -= 2
        reasons.append("MACD Bearish Cross!")
    
    # 4. 布林带
    ma20 = df['close'].rolling(window=20, min_periods=1).mean()
    std20 = df['close'].rolling(window=20, min_periods=1).std()
    upper = ma20 + (std20 * 2)
    lower = ma20 - (std20 * 2)
    
    if latest['close'] < lower.iloc[-1]:
        score += 2
        reasons.append("Price below Lower BB (Oversold)")
    elif latest['close'] > upper.iloc[-1]:
        score -= 2
        reasons.append("Price above Upper BB (Overbought)")
    
    # 5. 动量
    momentum = df['close'].pct_change(periods=10).iloc[-1]
    if momentum > 0.02:
        score += 1
        reasons.append(f"Strong Momentum (+{momentum*100:.2f}%)")
    elif momentum < -0.02:
        score -= 1
        reasons.append(f"Strong Negative Momentum ({momentum*100:.2f}%)")
    
    # 确定信号
    if score >= 4:
        signal = "STRONG BUY"
        strength = min(score / 10, 1.0)
    elif score >= 2:
        signal = "BUY"
        strength = score / 10
    elif score <= -4:
        signal = "STRONG SELL"
        strength = min(abs(score) / 10, 1.0)
    elif score <= -2:
        signal = "SELL"
        strength = abs(score) / 10
    else:
        signal = "NONE"
        strength = 0
    
    # 趋势过滤：信号方向必须与趋势一致
    if allowed_direction == 'BUY' and signal in ['SELL', 'STRONG SELL']:
        reasons.append("❌ 信号与趋势相反 (只做多)")
        signal = "NONE"
        strength = 0
    elif allowed_direction == 'SELL' and signal in ['BUY', 'STRONG BUY']:
        reasons.append("❌ 信号与趋势相反 (只做空)")
        signal = "NONE"
        strength = 0
    elif allowed_direction == 'NONE':
        reasons.append("❌ 趋势不明，不交易")
        signal = "NONE"
        strength = 0
    
    return signal, strength, reasons, allowed_direction


# 扫描所有品种
opportunities = []

for symbol in symbols:
    # 获取日线数据
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_D1, 0, 100)
    
    if rates is None or len(rates) < 30:
        continue
    
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    df.set_index('time', inplace=True)
    
    # 【铁律 5】获取 H1 数据用于 EMA200 趋势过滤
    h1_rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 200)
    h1_df = None
    if h1_rates is not None and len(h1_rates) >= 200:
        h1_df = pd.DataFrame(h1_rates)
        h1_df['time'] = pd.to_datetime(h1_df['time'], unit='s')
        h1_df.set_index('time', inplace=True)
    
    # 计算信号 (带趋势过滤)
    signal, strength, reasons, allowed_direction = calculate_signal_strength(df, symbol, h1_df)
    
    if signal != "NONE" and strength > 0.10:  # P1: 最低过滤阈值 0.10（开仓阈值另计为 0.15%）
        opportunities.append({
            'symbol': symbol,
            'signal': signal,
            'strength': strength,
            'price': df['close'].iloc[-1],
            'reasons': reasons,
            'allowed_direction': allowed_direction
        })

# 排序
opportunities.sort(key=lambda x: x['strength'], reverse=True)

# 显示结果
print("\n" + "="*70)
print("Trading Opportunities")
print("="*70)

if not opportunities:
    print("\nNo strong trading opportunities found.")
    print("Waiting for clearer signals...")
else:
    print(f"\nFound {len(opportunities)} potential opportunities:\n")
    
    for i, opp in enumerate(opportunities, 1):
        print(f"{i}. {opp['symbol']} - {opp['signal']}")
        print(f"   Strength: {opp['strength']*100:.1f}%")
        print(f"   Price: {opp['price']:.5f}")
        print(f"   Reasons:")
        for reason in opp['reasons'][:3]:  # 显示前 3 个原因
            print(f"     - {reason}")
        print()

# 最佳机会
if opportunities:
    best = opportunities[0]
    print("="*70)
    print("BEST OPPORTUNITY")
    print("="*70)
    print(f"Symbol: {best['symbol']}")
    print(f"Signal: {best['signal']}")
    print(f"Strength: {best['strength']*100:.1f}%")
    print(f"Price: {best['price']:.5f}")
    print(f"\nFull Analysis:")
    for reason in best['reasons']:
        print(f"  - {reason}")

mt5.shutdown()
