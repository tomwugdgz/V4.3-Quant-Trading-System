"""
MT5 K 线分析工具 - 开仓前必看
显示关键支撑/阻力、趋势、形态
"""

import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime

def analyze_symbol(symbol, timeframe=mt5.TIMEFRAME_H1, bars=100):
    """
    分析单个品种
    """
    print("=" * 70)
    print(f"{symbol} 技术分析")
    print("=" * 70)
    
    # 获取 K 线数据
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, bars)
    if rates is None or len(rates) == 0:
        print("无法获取 K 线数据")
        return
    
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    
    # 计算均线
    df['MA50'] = df['close'].rolling(window=50).mean()
    df['MA200'] = df['close'].rolling(window=200).mean()
    
    # 计算 RSI
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # 当前数据
    current_price = df['close'].iloc[-1]
    ma50 = df['MA50'].iloc[-1]
    ma200 = df['MA200'].iloc[-1]
    rsi = df['RSI'].iloc[-1]
    
    print(f"\n当前价格：{current_price:.5f}")
    print(f"MA50: {ma50:.5f} {'↑' if current_price > ma50 else '↓'}")
    print(f"MA200: {ma200:.5f} {'↑' if current_price > ma200 else '↓'}")
    print(f"RSI: {rsi:.2f} {'超买' if rsi > 70 else '超卖' if rsi < 30 else '中性'}")
    
    # 趋势判断
    if ma50 > ma200:
        trend = "上升趋势 ✅"
    elif ma50 < ma200:
        trend = "下降趋势 ❌"
    else:
        trend = "横盘震荡 ⚠️"
    
    print(f"\n趋势：{trend}")
    
    # 支撑/阻力位
    high_50 = df['high'].rolling(window=50).max().iloc[-1]
    low_50 = df['low'].rolling(window=50).min().iloc[-1]
    
    print(f"\n关键位置:")
    print(f"阻力位：{high_50:.5f}")
    print(f"支撑位：{low_50:.5f}")
    
    # 交易建议
    print(f"\n交易建议:")
    if current_price > ma50 > ma200 and rsi < 70:
        print("✅ 考虑 BUY (上升趋势，RSI 未超买)")
    elif current_price < ma50 < ma200 and rsi > 30:
        print("✅ 考虑 SELL (下降趋势，RSI 未超卖)")
    else:
        print("⚠️ 观望 (趋势不明或 RSI 极端)")
    
    print("=" * 70)

# 主程序
if __name__ == "__main__":
    mt5.initialize()
    
    # 分析当前持仓品种
    symbols = ["NZDUSD", "AUDUSD", "USDCHF"]
    
    for symbol in symbols:
        analyze_symbol(symbol)
    
    mt5.shutdown()
