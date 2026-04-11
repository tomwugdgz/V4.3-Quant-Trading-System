import MetaTrader5 as mt5
import datetime
import numpy as np

mt5.initialize()

print("=" * 60)
print("旺财量化 - 行情分析与判断")
print("=" * 60)
print(f"时间：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 60)
print("")

# 账户信息
account = mt5.account_info()
print(f"账户余额：${account.balance:.2f}")
print(f"账户净值：${account.equity:.2f}")
print(f"总盈亏：${account.profit:.2f}")
print("")

# 当前持仓
positions = mt5.positions_get()
print("=== 当前持仓 ===")
if positions:
    for p in positions:
        direction = "做多" if p.type == 0 else "做空"
        print(f"{p.symbol} | {direction} | {p.volume}手 | 入场：${p.price_open:.2f} | 现价：${p.price_current:.2f} | 盈亏：${p.profit:.2f}")
else:
    print("无持仓")
print("")

# 获取多个品种的 K 线数据进行分析
symbols = ['BTCUSD', 'EURUSD', 'USDJPY', 'XAUUSD']

print("=== 技术分析 (H1 周期) ===")
print("")

for symbol in symbols:
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 200)
    if rates is None or len(rates) == 0:
        print(f"{symbol}: 数据不足")
        continue
    
    closes = rates['close']
    highs = rates['high']
    lows = rates['low']
    volumes = rates['tick_volume']
    
    current_price = closes[-1]
    
    # 移动平均线
    sma20 = np.mean(closes[-20:])
    sma50 = np.mean(closes[-50:]) if len(closes) >= 50 else sma20
    sma200 = np.mean(closes[-200:]) if len(closes) >= 200 else sma50
    
    # 趋势判断
    if current_price > sma20 > sma50 > sma200:
        trend = "强多头"
        signal = "买入/持有"
    elif current_price > sma20 > sma50:
        trend = "多头"
        signal = "持有"
    elif current_price < sma20 < sma50 < sma200:
        trend = "强空头"
        signal = "卖出/做空"
    elif current_price < sma20 < sma50:
        trend = "空头"
        signal = "做空/观望"
    else:
        trend = "震荡"
        signal = "观望"
    
    # 涨跌幅
    pct_24h = ((closes[-1] - closes[-24]) / closes[-24]) * 100 if len(closes) >= 24 else 0
    pct_7d = ((closes[-1] - closes[-168]) / closes[-168]) * 100 if len(closes) >= 168 else 0
    
    # 波动性
    atr = np.mean(highs[-20:] - lows[-20:])
    
    # 支撑阻力
    support = np.min(lows[-50:])
    resistance = np.max(highs[-50:])
    
    print(f"{symbol}")
    print(f"  当前价：{current_price:.5f}")
    print(f"  24 小时涨跌：{pct_24h:+.2f}%")
    print(f"  7 天涨跌：{pct_7d:+.2f}%")
    print(f"  SMA20: {sma20:.5f} | SMA50: {sma50:.5f} | SMA200: {sma200:.5f}")
    print(f"  趋势：{trend}")
    print(f"  信号：{signal}")
    print(f"  支撑：{support:.5f} | 阻力：{resistance:.5f}")
    print(f"  ATR(波动): {atr:.5f}")
    print("")

print("=" * 60)
print("【未来几天判断】")
print("=" * 60)
print("")

# 针对 BTC 的详细分析
btc_rates = mt5.copy_rates_from_pos('BTCUSD', mt5.TIMEFRAME_H1, 0, 200)
if btc_rates is not None and len(btc_rates) > 0:
    btc_closes = btc_rates['close']
    btc_highs = btc_rates['high']
    btc_lows = btc_rates['low']
    
    current = btc_closes[-1]
    sma20 = np.mean(btc_closes[-20:])
    sma50 = np.mean(btc_closes[-50:])
    
    # 判断
    if current > sma20:
        short_term = "短期偏多"
    else:
        short_term = "短期偏空"
    
    if current > sma50:
        medium_term = "中期偏多"
    else:
        medium_term = "中期偏空"
    
    print("BTCUSD 详细分析:")
    print(f"  短期 (1-2 天): {short_term}")
    print(f"  中期 (3-7 天): {medium_term}")
    print(f"  关键支撑：${np.min(btc_lows[-50:]):.2f}")
    print(f"  关键阻力：${np.max(btc_highs[-50:]):.2f}")
    print("")
    
    # 情景分析
    print("情景分析:")
    print(f"  看涨情景：突破 ${np.max(btc_highs[-50:]):.2f} → 目标 ${current * 1.05:.2f} (+5%)")
    print(f"  看跌情景：跌破 ${np.min(btc_lows[-50:]):.2f} → 目标 ${current * 0.95:.2f} (-5%)")
    print(f"  震荡情景：在 ${np.min(btc_lows[-50:]):.2f} - ${np.max(btc_highs[-50:]):.2f} 区间波动")
    print("")

mt5.shutdown()
