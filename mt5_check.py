import MetaTrader5 as mt5
import sys

# 初始化
if not mt5.initialize():
    print("MT5 initialization failed")
    sys.exit(1)

# 获取 USDJPY 详细信息
symbol = "USDJPY"
info = mt5.symbol_info(symbol)

if info is None:
    print(f"{symbol} not available")
    mt5.shutdown()
    sys.exit(1)

# 显示 tick 数据
tick = mt5.symbol_info_tick(symbol)
if tick:
    print(f"Symbol: {symbol}")
    print(f"Bid: {tick.bid}")
    print(f"Ask: {tick.ask}")
    print(f"Last: {tick.last}")
    print(f"Volume: {tick.volume}")
    print(f"Spread: {(tick.ask - tick.bid) * 10000:.1f} pips")
    
    # 获取最近 10 根 H1 K 线
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 10)
    if rates is not None and len(rates) > 0:
        print(f"\nRecent H1 candles ({len(rates)}):")
        for i, rate in enumerate(rates[-5:]):
            print(f"  {i+1}: O={rate['open']:.2f} H={rate['high']:.2f} L={rate['low']:.2f} C={rate['close']:.2f}")
        
        # 简单趋势分析
        closes = [r['close'] for r in rates[-5:]]
        avg_close = sum(closes) / len(closes)
        current = tick.last
        
        print(f"\n5-candle avg close: {avg_close:.2f}")
        print(f"Current price: {current:.2f}")
        
        if current > avg_close:
            print("Signal: BULLISH (price above average)")
        else:
            print("Signal: BEARISH (price below average)")
    else:
        print("No rate data available")
else:
    print("No tick data")

mt5.shutdown()
