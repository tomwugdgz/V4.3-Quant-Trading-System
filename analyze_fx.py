#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import yfinance as yf
import pandas as pd
import numpy as np

# Calculate RSI
def calc_rsi(close, window=14):
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1/window, adjust=False, min_periods=window).mean()
    avg_loss = loss.ewm(alpha=1/window, adjust=False, min_periods=window).mean()
    rs = avg_gain / avg_loss.replace(0, pd.NA)
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

# Analyze a single symbol
def analyze_symbol(symbol, name):
    print(f"\n{'='*60}")
    print(f"分析: {name} ({symbol})")
    print(f"{'='*60}")
    
    # Download 6 months data
    data = yf.download(symbol, period="6mo")
    if data.empty:
        print("X 获取数据失败")
        return None
    
    # Get latest
    current = data['Close'].iloc[-1].values[0]
    prev_close = data['Close'].iloc[-2].values[0]
    change = (current - prev_close) / prev_close * 100
    
    # Calculate indicators
    data['RSI'] = calc_rsi(data['Close'])
    data['MACD'], data['Signal'], data['Histogram'] = calc_macd(data['Close'])
    data['ATR'] = calc_atr(data['High'], data['Low'], data['Close'])
    
    latest = data.iloc[-1]
    rsi = latest['RSI'].values[0]
    macd = latest['MACD'].values[0]
    signal = latest['Signal'].values[0]
    histogram = latest['Histogram'].values[0]
    atr = latest['ATR'].values[0]
    
    # Calculate moving averages
    data['MA20'] = data['Close'].rolling(20).mean()
    data['MA50'] = data['Close'].rolling(50).mean()
    data['MA200'] = data['Close'].rolling(200).mean()
    
    ma20 = data['MA20'].iloc[-1].values[0]
    ma50 = data['MA50'].iloc[-1].values[0]
    ma200 = data['MA200'].iloc[-1].values[0] if not pd.isna(data['MA200'].iloc[-1].values[0]) else None
    
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
        macd_signal ="[看涨 (金叉/多头排列)]"
    elif macd < signal and histogram < 0:
        macd_signal = "[看跌 (死叉/空头排列)]"
    elif macd > signal and histogram < 0:
        macd_signal = "[看涨背离]"
    elif macd < signal and histogram > 0:
        macd_signal = "[看跌背离]"
    
    # 支撑阻力
    recent_low = data['Low'].tail(20).min().values[0]
    recent_high = data['High'].tail(20).max().values[0]
    
    # 汇总输出
    print(f"当前价格: {current:.5f}")
    print(f"日涨跌幅: {change:+.2f}%")
    print(f"ATR (14): {atr:.5f} (平均波动: {atr*10000:.1f} 点)")
    print(f"RSI (14): {rsi:.1f} - {rsi_status}")
    print(f"MACD: {macd:.4f} vs 信号线 {signal:.4f} - {macd_signal}")
    print(f"MA20: {ma20:.5f} | MA50: {ma50:.5f}")
    if ma200:
        print(f"MA200: {ma200:.5f}")
    print(f"趋势判断: {trend}")
    print(f"近20日最低: {recent_low:.5f} | 近20日最高: {recent_high:.5f}")
    
    # 交易建议
    print(f"\n 交易建议:")
    suggestion = "观望"
    direction = None
    sl_distance = None
    
    if "多头趋势" in trend and "看涨" in macd_signal and 40 < rsi < 70:
        suggestion = "[OK] 可做多"
        direction = "BUY"
        sl_distance = 1.5 * atr
        entry = current
        sl = entry - 1.5 * atr
        tp = entry + 2.5 * atr
        print(f"  建议方向: 做多 (BUY)")
        print(f"  入场: {entry:.5f} | 止损: {sl:.5f} | 止盈: {tp:.5f}")
        rr = (tp - entry) / (entry - sl)
        print(f"  盈亏比: {rr:.2f} : 1")
    elif "空头趋势" in trend and "看跌" in macd_signal and 30 < rsi < 60:
        suggestion = "[OK] 可做空"
        direction = "SELL"
        sl_distance = 1.5 * atr
        entry = current
        sl = entry + 1.5 * atr
        tp = entry - 2.5 * atr
        print(f"  建议方向: 做空 (SELL)")
        print(f"  入场: {entry:.5f} | 止损: {sl:.5f} | 止盈: {tp:.5f}")
        rr = (entry - tp) / (sl - entry)
        print(f"  盈亏比: {rr:.2f} : 1")
    else:
        print(f"  暂无高概率信号，建议观望等待更好机会")
    
    return {
        "symbol": symbol,
        "name": name,
        "current": current,
        "rsi": rsi,
        "macd_signal": macd_signal,
        "trend": trend,
        "suggestion": suggestion,
        "direction": direction,
        "atr": atr,
        "recent_low": recent_low,
        "recent_high": recent_high
    }

def main():
    symbols = [
        ("JPY=X", "USD/JPY"),
        ("GBPUSD=X", "GBP/USD"),
        ("EURUSD=X", "EUR/USD"),
        ("AUDUSD=X", "AUD/USD"),
        ("CAD=X", "USD/CAD"),
        ("BTC-USD", "Bitcoin"),
    ]
    
    results = []
    for symbol, name in symbols:
        res = analyze_symbol(symbol, name)
        if res:
            results.append(res)
    
    print(f"\n{'='*60}")
    print("== 汇总 - 高概率交易机会")
    print(f"{'='*60}")
    
    opportunities = [r for r in results if "可" in r['suggestion']]
    if opportunities:
        for opp in opportunities:
            print(f"\n{opp['name']}: {opp['trend']} - {opp['suggestion']}")
    else:
        print("\n当前没有明确的高概率机会，建议耐心等待。")
    
    print(f"\n{'='*60}")

if __name__ == "__main__":
    main()
