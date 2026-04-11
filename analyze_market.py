import MetaTrader5 as mt5
import datetime

mt5.initialize()

symbols = ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'BTCUSD', 'XAUUSD']

print('=== 实时行情 ===')
print('时间:', datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
print('')

for s in symbols:
    tick = mt5.symbol_info_tick(s)
    if tick:
        spread = (tick.ask - tick.bid) * 10000 if s != 'USDJPY' else (tick.ask - tick.bid) * 100
        print(f'{s}: Bid={tick.bid:.5f} Ask={tick.ask:.5f} Spread={spread:.2f} points')
    else:
        print(f'{s}: 无数据')

print('')
print('=== 技术指标分析 ===')

# 获取 K 线数据并计算指标
def analyze_symbol(symbol, timeframe=mt5.TIMEFRAME_H1, periods=100):
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, periods)
    if rates is None or len(rates) == 0:
        return None
    
    import numpy as np
    closes = rates['close']
    highs = rates['high']
    lows = rates['low']
    
    # 简单趋势分析
    sma20 = np.mean(closes[-20:])
    sma50 = np.mean(closes[-50:]) if len(closes) >= 50 else sma20
    current_price = closes[-1]
    
    # 20 日涨跌幅
    pct_20 = ((closes[-1] - closes[-20]) / closes[-20]) * 100 if len(closes) >= 20 else 0
    
    # 趋势判断
    trend = '多头' if current_price > sma20 > sma50 else ('空头' if current_price < sma20 < sma50 else '震荡')
    
    return {
        'price': current_price,
        'sma20': sma20,
        'sma50': sma50,
        'pct_20': pct_20,
        'trend': trend
    }

for s in symbols:
    data = analyze_symbol(s)
    if data:
        print(f"{s}:")
        print(f"  当前价：{data['price']:.5f}")
        print(f"  20 日趋势：{data['pct_20']:+.2f}%")
        print(f"  SMA20: {data['sma20']:.5f}")
        print(f"  SMA50: {data['sma50']:.5f}")
        print(f"  趋势判断：{data['trend']}")
        print('')
    else:
        print(f'{s}: 数据不足')
        print('')

mt5.shutdown()
