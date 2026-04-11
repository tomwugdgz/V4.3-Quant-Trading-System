#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import requests
import pandas as pd
import numpy as np
import json
import os

# Alpha Vantage API key
API_KEY = "HGTBD9DSFEHLBUAF"

# Calculate RSI
def calc_rsi(close, window=14):
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1/window, adjust=False, min_periods=window).mean()
    avg_loss = loss.ewm(alpha=1/window, adjust=False, min_periods=window).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return rsi

# Calculate MACD
def calc_macd(close, fast=12, slow=26, signal=9):
    ema_fast = close.ewm(span=fast, adjust=False, min_periods=fast).mean()
    ema_slow = close.ewm(span=slow, adjust=False, min_periods=slow).mean()
    macd = ema_fast - ema_slow
    signal_line = macd.ewm(span=signal, adjust=False, min_periods=signal).mean()
    histogram = macd - signal_line
    return macd, signal_line, histogram

# Calculate ATR
def calc_atr(high, low, close, window=14):
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1/window, adjust=False, min_periods=window).mean()
    return atr

# Get daily data from Alpha Vantage
def get_daily_stock(symbol):
    url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&apikey={API_KEY}&outputsize=compact"
    response = requests.get(url)
    if response.status_code != 200:
        print(f"API Error: {response.status_code}")
        return None
    
    data = response.json()
    if 'Time Series (Daily)' not in data:
        print(f"No data for {symbol}")
        print(f"Response: {data}")
        return None
    
    ts = data['Time Series (Daily)']
    df = pd.DataFrame.from_dict(ts, orient='index')
    df.index = pd.to_datetime(df.index)
    df = df.sort_index()
    df = df.astype(float)
    df = df.rename(columns={
        '1. open': 'Open',
        '2. high': 'High',
        '3. low': 'Low',
        '4. close': 'Close',
    })
    
    # Take last 180 days
    df = df.tail(180)
    return df

# Analyze TSLA
def main():
    symbol = "TSLA"
    print(f"\n{'='*60}")
    print(f"分析: Tesla (TSLA)")
    print(f"{'='*60}")
    
    data = get_daily_stock(symbol)
    if data is None or data.empty:
        print("X 获取数据失败")
        return
    
    # Get latest
    current = data['Close'].iloc[-1]
    prev_close = data['Close'].iloc[-2]
    change = (current - prev_close) / prev_close * 100
    
    # Calculate indicators
    data['RSI'] = calc_rsi(data['Close'])
    data['MACD'], data['Signal'], data['Histogram'] = calc_macd(data['Close'])
    data['ATR'] = calc_atr(data['High'], data['Low'], data['Close'])
    
    latest = data.iloc[-1]
    rsi = latest['RSI']
    macd = latest['MACD']
    signal = latest['Signal']
    histogram = latest['Histogram']
    atr = latest['ATR']
    
    # Calculate moving averages
    data['MA20'] = data['Close'].rolling(20).mean()
    data['MA50'] = data['Close'].rolling(50).mean()
    data['MA200'] = data['Close'].rolling(200).mean()
    
    ma20 = data['MA20'].iloc[-1]
    ma50 = data['MA50'].iloc[-1]
    ma200 = data['MA200'].iloc[-1] if not pd.isna(data['MA200'].iloc[-1]) else None
    
    # Trend判断
    trend = "中性"
    if current > ma20 > ma50:
        trend = "[多头趋势]"
    elif current < ma20 < ma50:
        trend = "[空头趋势]"
    elif ma20 > ma50 and current < ma20:
        trend = "[多头回调]"
    elif ma20 < ma50 and current > ma20:
        trend = "[空头反弹]"
    
    # RSI 状态
    rsi_status = "中性"
    if rsi > 70:
        rsi_status = "超买 (可能回调)"
    elif rsi < 30:
        rsi_status = "超卖 (可能反弹)"
    
    # MACD 信号
    macd_signal = "中性"
    if macd > signal and histogram > 0:
        macd_signal = "[看涨 (金叉/多头排列)]"
    elif macd < signal and histogram < 0:
        macd_signal = "[看跌 (死叉/空头排列)]"
    elif macd > signal and histogram < 0:
        macd_signal = "[看涨背离]"
    elif macd < signal and histogram > 0:
        macd_signal = "[看跌背离]"
    
    # 支撑阻力
    recent_low = data['Low'].tail(20).min()
    recent_high = data['High'].tail(20).max()
    
    # 汇总输出
    print(f"当前价格: ${current:.2f}")
    print(f"日涨跌幅: {change:+.2f}%")
    print(f"ATR (14): ${atr:.2f} (平均每日波动)")
    print(f"RSI (14): {rsi:.1f} - {rsi_status}")
    print(f"MACD: {macd:.2f} vs 信号线 {signal:.2f} - {macd_signal}")
    print(f"MA20: ${ma20:.2f} | MA50: ${ma50:.2f}")
    if ma200:
        print(f"MA200: ${ma200:.2f}")
    print(f"趋势判断: {trend}")
    print(f"近20日最低: ${recent_low:.2f} | 近20日最高: ${recent_high:.2f}")
    
    # 用户持仓对比
    print(f"\n你的持仓: 买入 0.1 手 @ $399.53, 当前 $392.56")
    print(f"你的止损: $380.78")
    distance_to_sl = current - 380.78
    print(f"距离你的止损: ${distance_to_sl:.2f} ({(distance_to_sl/atr):.1f} ATR)")
    
    # 判断是否需要止损
    print(f"\n判断:")
    if current < ma20 and macd < signal and rsi < 40:
        print("-> 趋势已经转空，建议止损离场")
    elif current < ma20 and current > 380.78:
        print("-> 趋势转弱，但还没到你的止损位，持有观察，到达止损再走")
    elif current > ma20:
        print("-> 趋势仍然向上，继续持有")
    
    print(f"\n{'='*60}")

if __name__ == "__main__":
    main()
