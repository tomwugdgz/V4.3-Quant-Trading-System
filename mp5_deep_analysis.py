#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MP5 策略数据深度分析
检查市场状态、节假日、数据质量
"""

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import io
import sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

SYMBOLS = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "USDCHF", "NZDUSD"]

def check_market_hours():
    """检查市场状态"""
    now = datetime.now()
    
    print("=" * 90)
    print("📅 时间与市场状态检查")
    print("=" * 90)
    print(f"\n当前时间：{now.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"星期：{now.strftime('%A')} ({now.strftime('%w')})")
    print(f"时区：Asia/Shanghai (GMT+8)")
    
    # 检查是否系周末
    weekday = now.weekday()
    if weekday >= 5:  # 周六或周日
        print(f"\n⚠️  周末休市 (周六 05:00 - 周一 06:00)")
    else:
        print(f"\n✅ 交易日 (星期{weekday + 1})")
    
    # 检查节假日 (2026 年)
    holidays_2026 = [
        (1, 1, "元旦"),
        (1, 19, "马丁路德金日 (美)"),
        (2, 16, "总统日 (美)"),
        (4, 3, "耶稣受难日"),
        (4, 6, "复活节星期一"),
        (5, 25, "阵亡将士纪念日 (美)"),
        (7, 4, "美国独立日"),
        (9, 7, "劳动节 (美)"),
        (11, 26, "感恩节 (美)"),
        (12, 25, "圣诞节"),
        (12, 26, "节礼日"),
    ]
    
    today = (now.month, now.day)
    is_holiday = False
    for month, day, name in holidays_2026:
        if today == (month, day):
            print(f"\n⚠️  节假日：{name} - 市场可能休市或提前收盘")
            is_holiday = True
            break
    
    if not is_holiday:
        print(f"\n✅ 非节假日，正常交易")
    
    # 检查交易时段
    hour = now.hour
    if hour < 6:
        print(f"\n⚠️  亚盘前时段 (流动性低)")
    elif hour < 15:
        print(f"\n✅ 亚洲盘时段 (06:00-15:00)")
    elif hour < 20:
        print(f"\n✅ 欧洲盘时段 (15:00-00:00) - 流动性高")
    elif hour < 24:
        print(f"\n✅ 美洲盘时段 (20:00-05:00) - 流动性最高")

def analyze_mp5_data():
    """深度分析 MP5 策略数据"""
    print("\n" + "=" * 90)
    print("📊 MP5 策略数据深度分析")
    print("=" * 90)
    
    if not mt5.initialize():
        print("MT5 initialization failed")
        return
    
    for symbol in SYMBOLS:
        tick = mt5.symbol_info_tick(symbol)
        if not tick or tick.bid <= 0:
            print(f"\n❌ {symbol}: 无实时数据")
            continue
        
        # 获取 H1 数据
        rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 100)
        if rates is None or len(rates) < 100:
            print(f"\n⚠️  {symbol}: 数据不足 ({len(rates) if rates else 0} 根 K 线)")
            continue
        
        df = pd.DataFrame(rates)
        
        # 基础统计
        current = tick.bid
        spread = (tick.ask - tick.bid) * 10000
        
        # 5 根 K 线趋势
        closes_5 = df['close'].iloc[-5:].values
        avg_5 = np.mean(closes_5)
        strength_5 = (current - avg_5) / avg_5 * 100
        
        # 20 根 K 线趋势
        closes_20 = df['close'].iloc[-20:].values
        avg_20 = np.mean(closes_20)
        strength_20 = (current - avg_20) / avg_20 * 100
        
        # EMA
        ema_fast = df['close'].ewm(span=10, adjust=False).mean().iloc[-1]
        ema_slow = df['close'].ewm(span=20, adjust=False).mean().iloc[-1]
        ema_diff = (ema_fast - ema_slow) / ema_slow * 100
        
        # MACD
        ema12 = df['close'].ewm(span=12, adjust=False).mean()
        ema26 = df['close'].ewm(span=26, adjust=False).mean()
        macd = ema12 - ema26
        macd_signal = macd.ewm(span=9, adjust=False).mean().iloc[-1]
        macd_hist = macd.iloc[-1] - macd_signal
        
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=12).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=12).mean()
        rs = gain / loss
        rsi = (100 - (100 / (1 + rs))).iloc[-1]
        
        # 波动率 (ATR)
        tr1 = df['high'] - df['low']
        tr2 = abs(df['high'] - df['close'].shift(1))
        tr3 = abs(df['low'] - df['close'].shift(1))
        tr = np.maximum(np.maximum(tr1, tr2), tr3)
        atr = tr.rolling(window=14).mean().iloc[-1]
        atr_pips = atr * 10000
        
        # 成交量
        avg_volume = df['tick_volume'].iloc[-20:].mean()
        current_volume = df['tick_volume'].iloc[-1]
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 0
        
        print(f"\n{symbol}")
        print(f"  价格：{current:.5f} | 点差：{spread:.1f} pips")
        print(f"  5K 趋势：{strength_5:+.3f}% | 20K 趋势：{strength_20:+.3f}%")
        print(f"  EMA(10/20): {ema_fast:.5f} / {ema_slow:.5f} (差值：{ema_diff:+.3f}%)")
        print(f"  MACD: {macd.iloc[-1]:.6f} | Signal: {macd_signal:.6f} | Histogram: {macd_hist:+.6f}")
        rsi_status = "(超卖)" if rsi < 35 else "(超买)" if rsi > 65 else "(中性)"
        print(f"  RSI(12): {rsi:.1f} {rsi_status}")
        print(f"  ATR(14): {atr_pips:.1f} pips")
        print(f"  成交量：{current_volume} (均量：{avg_volume:.0f}, 比率：{volume_ratio:.2f}x)")
        
        # MP5 信号评分
        score = 0
        signals = []
        
        # 1. 趋势强度 (≥0.05% 得分)
        if abs(strength_5) >= 0.05:
            score += 1
            signals.append(f"趋势强 ({strength_5:+.3f}%)")
        
        # 2. EMA 确认
        if ema_diff > 0.05:
            score += 1
            signals.append("EMA 多头")
        elif ema_diff < -0.05:
            score += 1
            signals.append("EMA 空头")
        
        # 3. MACD 确认
        if abs(macd_hist) > 0.0001:
            score += 1
            signals.append(f"MACD {'多' if macd_hist > 0 else '空'}")
        
        # 4. RSI 确认
        if rsi < 35:
            score += 1
            signals.append("RSI 超卖 (BUY)")
        elif rsi > 65:
            score += 1
            signals.append("RSI 超买 (SELL)")
        
        # 5. 成交量确认
        if volume_ratio > 1.5:
            score += 0.5
            signals.append("成交量放大")
        
        signal = "BUY" if strength_5 > 0 else "SELL"
        final_strength = abs(strength_5) * (score / 5)
        
        print(f"  MP5 评分：{score:.1f}/4.5")
        print(f"  信号：{signal} ({final_strength:.3f}%)")
        if score >= 3:
            print(f"  ✅ 强信号！")
        elif score >= 2:
            print(f"  ⚠️  中等信号")
        else:
            print(f"  ❌ 弱信号")
        
        if signals:
            print(f"  信号详情：{', '.join(signals)}")
    
    mt5.shutdown()

def check_data_quality():
    """检查数据质量"""
    print("\n" + "=" * 90)
    print("🔍 数据质量检查")
    print("=" * 90)
    
    if not mt5.initialize():
        return
    
    for symbol in SYMBOLS:
        rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 10)
        if rates is None or len(rates) < 10:
            print(f"❌ {symbol}: 数据缺失")
            continue
        
        df = pd.DataFrame(rates)
        
        # 检查时间连续性
        times = pd.to_datetime(df['time'], unit='s')
        time_diffs = times.diff().dropna()
        gaps = time_diffs[time_diffs > pd.Timedelta(hours=1)]
        
        if len(gaps) > 0:
            print(f"⚠️  {symbol}: 发现 {len(gaps)} 个数据缺口")
        else:
            print(f"✅ {symbol}: 数据连续")
        
        # 检查零值
        zero_closes = (df['close'] == 0).sum()
        if zero_closes > 0:
            print(f"  ⚠️  发现 {zero_closes} 个零值收盘价")
        
        # 检查异常波动
        returns = df['close'].pct_change() * 100
        outliers = returns[abs(returns) > 1.0]  # >1% 波动
        if len(outliers) > 0:
            print(f"  ⚠️  发现 {len(outliers)} 根 K 线波动>1%")
    
    mt5.shutdown()

def main():
    check_market_hours()
    analyze_mp5_data()
    check_data_quality()
    
    print("\n" + "=" * 90)
    print("💡 总结")
    print("=" * 90)
    
    now = datetime.now()
    weekday = now.weekday()
    
    if weekday >= 5:
        print("\n⚠️  周末休市，信号弱系正常的")
    else:
        print("\n✅ 正常交易日")
        print("\n如果信号普遍偏弱，可能原因:")
        print("  1. 亚洲盘时段 (流动性低)")
        print("  2. 节假日前后 (交易员休假)")
        print("  3. 重大数据发布前 (观望情绪)")
        print("  4. 市场震荡期 (无明确趋势)")
        print("\n建议:")
        print("  - 等待欧洲盘 (15:00) 或美洲盘 (20:00)")
        print("  - 关注财经日历 (非农、CPI、央行决议等)")
        print("  - 信号<0.1% 坚决不开仓 (交易铁律)")

if __name__ == "__main__":
    main()
