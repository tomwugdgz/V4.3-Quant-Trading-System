#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
市场信号扫描 v2.3 - 四重确认版
创建：2026-04-07
修复:
  1. 信号阈值：0.005% → 0.05%（符合交易铁律）
  2. 选择逻辑：选信号最强，不是点差最小
  3. 增加多重确认：EMA + MACD + RSI + ADX
  4. ATR 动态止损计算
"""

import MetaTrader5 as mt5
import sys
from datetime import datetime
import pandas as pd
import numpy as np

# ========== 配置参数 ==========
SYMBOLS = [
    # 美元直盘
    "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "USDCHF", "NZDUSD",
    # 日元交叉盘
    "EURJPY", "GBPJPY", "AUDJPY", "NZDJPY", "CADJPY", "CHFJPY"
]

# 信号强度门槛（交易铁律）
SIGNAL_THRESHOLD_STANDARD = 0.1  # 标准门槛 0.1%
SIGNAL_THRESHOLD_LIGHT = 0.05    # 轻仓测试 0.05%

# 四重确认参数
EMA_FAST = 10
EMA_SLOW = 20
RSI_PERIOD = 12
RSI_OVERBOUGHT = 65
RSI_OVERSOLD = 35
ADX_THRESHOLD = 20

# 风险参数
RISK_PERCENT = 0.005  # 0.5% 单笔风险
ATR_MULTIPLIER_SL = 2.0
ATR_MULTIPLIER_TP = 4.0

# ========== 技术指标计算 ==========

def calculate_ema(prices, period):
    """计算 EMA"""
    return prices.ewm(span=period, adjust=False).mean().iloc[-1]

def calculate_macd(prices):
    """计算 MACD"""
    ema12 = prices.ewm(span=12, adjust=False).mean()
    ema26 = prices.ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9, adjust=False).mean()
    histogram = macd - signal
    return macd.iloc[-1], signal.iloc[-1], histogram.iloc[-1]

def calculate_rsi(prices, period=12):
    """计算 RSI"""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.iloc[-1]

def calculate_adx(high, low, close, period=14):
    """计算 ADX"""
    plus_dm = high.diff()
    minus_dm = -low.diff()
    
    plus_dm = np.where((plus_dm > minus_dm) & (plus_dm > 0), plus_dm, 0)
    minus_dm = np.where((minus_dm > plus_dm) & (minus_dm > 0), minus_dm, 0)
    
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    tr = np.maximum(np.maximum(tr1, tr2), tr3)
    
    atr = pd.Series(tr).rolling(window=period).mean()
    plus_di = 100 * pd.Series(plus_dm).rolling(window=period).mean() / atr
    minus_di = 100 * pd.Series(minus_dm).rolling(window=period).mean() / atr
    
    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
    adx = dx.rolling(window=period).mean()
    
    return adx.iloc[-1], plus_di.iloc[-1], minus_di.iloc[-1]

def calculate_atr(high, low, close, period=14):
    """计算 ATR"""
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    tr = np.maximum(np.maximum(tr1, tr2), tr3)
    atr = tr.rolling(window=period).mean()
    return atr.iloc[-1]

# ========== 信号分析 ==========

def analyze_symbol(symbol):
    """分析单个品种的多重信号"""
    tick = mt5.symbol_info_tick(symbol)
    if not tick or tick.bid <= 0:
        return None
    
    # 获取 H1 数据
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 100)
    if rates is None or len(rates) < 50:
        return None
    
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    
    current_price = tick.bid
    spread = (tick.ask - tick.bid) * 10000  # pips
    
    # 1. EMA 趋势确认
    ema_fast = calculate_ema(df['close'], EMA_FAST)
    ema_slow = calculate_ema(df['close'], EMA_SLOW)
    ema_signal = "BUY" if ema_fast > ema_slow else "SELL"
    ema_strength = abs(ema_fast - ema_slow) / ema_slow * 100
    
    # 2. MACD 动量确认
    macd, macd_signal, macd_hist = calculate_macd(df['close'])
    macd_direction = "BUY" if macd > macd_signal else "SELL"
    
    # 3. RSI 超买超卖
    rsi = calculate_rsi(df['close'], RSI_PERIOD)
    rsi_signal = "NEUTRAL"
    if rsi < RSI_OVERSOLD:
        rsi_signal = "BUY"  # 超卖，可能反弹
    elif rsi > RSI_OVERBOUGHT:
        rsi_signal = "SELL"  # 超买，可能回调
    
    # 4. ADX 趋势强度
    adx, plus_di, minus_di = calculate_adx(df['high'], df['low'], df['close'])
    adx_trend = "BUY" if plus_di > minus_di else "SELL"
    
    # 5. 基础趋势强度（5 根 K 线）
    closes = df['close'].iloc[-5:].values
    avg_close = np.mean(closes)
    base_strength = abs((current_price - avg_close) / avg_close * 100)
    base_signal = "BUY" if current_price > avg_close else "SELL"
    
    # ========== 四重确认评分 ==========
    confirmations = 0
    buy_signals = 0
    sell_signals = 0
    
    # EMA 确认
    if ema_strength > 0.05:
        confirmations += 1
        if ema_signal == "BUY":
            buy_signals += 1
        else:
            sell_signals += 1
    
    # MACD 确认
    if abs(macd_hist) > 0.0001:
        confirmations += 1
        if macd_direction == "BUY":
            buy_signals += 1
        else:
            sell_signals += 1
    
    # RSI 确认（反向信号）
    if rsi < RSI_OVERSOLD or rsi > RSI_OVERBOUGHT:
        confirmations += 1
        if rsi_signal == "BUY":
            buy_signals += 1
        else:
            sell_signals += 1
    
    # ADX 确认
    if adx > ADX_THRESHOLD:
        confirmations += 1
        if adx_trend == "BUY":
            buy_signals += 1
        else:
            sell_signals += 1
    
    # 确定最终信号
    if buy_signals >= 3:
        final_signal = "BUY"
    elif sell_signals >= 3:
        final_signal = "SELL"
    else:
        final_signal = "NEUTRAL"
    
    # 综合信号强度（修复：归一化到 0-1% 范围）
    raw_strength = base_strength * (confirmations / 4)
    # 归一化：确保信号强度不超过 1%
    signal_strength = min(raw_strength, 1.0)
    
    # 异常值检测
    if raw_strength > 1.0:
        print(f"⚠️ WARNING: {symbol} raw strength {raw_strength:.2f}% capped to 1.0%")
    
    # 计算 ATR 动态止损
    atr = calculate_atr(df['high'], df['low'], df['close'])
    atr_pips = atr * 10000  # 转换为 pips
    dynamic_sl = atr_pips * ATR_MULTIPLIER_SL
    dynamic_tp = atr_pips * ATR_MULTIPLIER_TP
    
    return {
        'symbol': symbol,
        'price': current_price,
        'spread': spread,
        'base_signal': base_signal,
        'base_strength': base_strength,
        'final_signal': final_signal,
        'signal_strength': signal_strength,
        'confirmations': confirmations,
        'ema_signal': ema_signal,
        'macd_signal': macd_direction,
        'rsi': rsi,
        'rsi_signal': rsi_signal,
        'adx': adx,
        'adx_signal': adx_trend,
        'atr_pips': atr_pips,
        'dynamic_sl': dynamic_sl,
        'dynamic_tp': dynamic_tp
    }

# ========== 主程序 ==========

def main():
    print("=" * 80)
    print("Market Scan v2.3 - Four-Factor Confirmation (四重确认)")
    print(f"Scan Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    if not mt5.initialize():
        print("MT5 initialization failed")
        sys.exit(1)
    
    # 获取账户信息
    account = mt5.account_info()
    print(f"\nAccount: {account.login} | Balance: ${account.balance:.2f} | Leverage: 1:{account.leverage}")
    print(f"Equity: ${account.equity:.2f} | Floating P/L: ${account.equity - account.balance:.2f}")
    
    # 检查持仓
    positions = mt5.positions_get()
    position_count = len(positions) if positions else 0
    print(f"Open Positions: {position_count}/3")
    print("=" * 80)
    
    results = []
    for symbol in SYMBOLS:
        result = analyze_symbol(symbol)
        if result:
            results.append(result)
            # 只显示有信号的
            if result['final_signal'] != "NEUTRAL" and result['signal_strength'] > 0.01:
                print(f"\n{result['symbol']}:")
                print(f"  Price: {result['price']:.5f} | Spread: {result['spread']:.1f} pips")
                print(f"  Signal: {result['final_signal']} (Strength: {result['signal_strength']:.3f}%)")
                print(f"  Confirmations: {result['confirmations']}/4")
                print(f"  Indicators:")
                print(f"    EMA({EMA_FAST}/{EMA_SLOW}): {result['ema_signal']} | Strength: {result['base_strength']:.3f}%")
                print(f"    MACD: {result['macd_signal']} | RSI({RSI_PERIOD}): {result['rsi']:.1f} ({result['rsi_signal']})")
                print(f"    ADX(14): {result['adx']:.1f} ({result['adx_signal']})")
                print(f"  Dynamic SL/TP: {result['dynamic_sl']:.1f} / {result['dynamic_tp']:.1f} pips")
    
    # 排序：信号强度优先
    results.sort(key=lambda x: x['signal_strength'], reverse=True)
    
    # 找出最佳机会
    best = None
    for r in results:
        if r['final_signal'] != "NEUTRAL" and r['signal_strength'] >= SIGNAL_THRESHOLD_LIGHT:
            best = r
            break
    
    print("\n" + "=" * 80)
    if best:
        threshold_type = "STANDARD" if best['signal_strength'] >= SIGNAL_THRESHOLD_STANDARD else "LIGHT"
        print(f"BEST OPPORTUNITY: {best['symbol']} [{threshold_type}]")
        print(f"  Signal: {best['final_signal']}")
        print(f"  Price: {best['price']:.5f}")
        print(f"  Strength: {best['signal_strength']:.3f}% (Confirmations: {best['confirmations']}/4)")
        print(f"  Spread: {best['spread']:.1f} pips")
        print(f"  ATR-based SL: {best['dynamic_sl']:.1f} pips | TP: {best['dynamic_tp']:.1f} pips")
        
        # 计算仓位 — 使用 MT5 真实的 tick_value
        risk_amount = account.balance * RISK_PERCENT
        sym_info = mt5.symbol_info(best['symbol'])
        # tick_value = 每 tick (1 point) 的盈亏金额
        # 标准手(1.0 lot) = 100,000 units
        # 1 pip = 10 points (5 位报价)，所以 pip_value_per_lot = tick_value * 10
        tick_value = (sym_info.trade_tick_value or 0) if sym_info else 0
        if tick_value <= 0:
            tick_value = 1.0  # fallback: $1/point = $10/pip (USD直盘标准值)
        pip_value_per_lot = tick_value * 10
        lot_size = round(risk_amount / (best['dynamic_sl'] * pip_value_per_lot), 2)
        lot_size = max(0.01, min(lot_size, 1.0))
        
        print(f"\n  POSITION SIZING:")
        print(f"    Risk: ${risk_amount:.2f} ({RISK_PERCENT*100:.1f}% of ${account.balance:.2f})")
        print(f"    Stop Loss: {best['dynamic_sl']:.1f} pips (ATR x {ATR_MULTIPLIER_SL})")
        print(f"    Take Profit: {best['dynamic_tp']:.1f} pips (ATR x {ATR_MULTIPLIER_TP})")
        print(f"    Lot Size: {lot_size:.2f}")
        
        # 交易建议
        if best['signal_strength'] >= SIGNAL_THRESHOLD_STANDARD:
            print(f"\n  RECOMMENDED: Signal strength >= {SIGNAL_THRESHOLD_STANDARD}% (Standard trade)")
        elif best['signal_strength'] >= SIGNAL_THRESHOLD_LIGHT:
            print(f"\n  LIGHT POSITION: Signal strength {best['signal_strength']:.3f}% (Light test only)")
        else:
            print(f"\n  NOT RECOMMENDED: Signal strength below threshold")
    else:
        print("NO GOOD OPPORTUNITY FOUND")
        print(f"  - No signals ≥ {SIGNAL_THRESHOLD_LIGHT}% (Light threshold)")
        print("  - Waiting for better market conditions...")
    
    print("=" * 80)
    mt5.shutdown()

if __name__ == "__main__":
    main()
