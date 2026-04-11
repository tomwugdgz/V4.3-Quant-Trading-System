import MetaTrader5 as mt5
import datetime
import numpy as np

mt5.initialize()

symbols = ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'BTCUSD', 'XAUUSD']

print('=' * 60)
print('旺财量化 - 市场分析报告')
print('=' * 60)
print('时间:', datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
print('账户：52797683 | 余额：$10,355.54 | 回报率：+3.56%')
print('=' * 60)
print('')

# 获取 K 线数据并计算指标
def analyze_symbol(symbol, timeframe=mt5.TIMEFRAME_H1, periods=100):
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, periods)
    if rates is None or len(rates) == 0:
        return None
    
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
    if current_price > sma20 > sma50:
        trend = '多头'
        signal = 'BUY'
    elif current_price < sma20 < sma50:
        trend = '空头'
        signal = 'SELL'
    else:
        trend = '震荡'
        signal = 'WAIT'
    
    # 波动性 (标准差)
    std_dev = np.std(closes[-20:])
    atr = np.mean(highs[-20:] - lows[-20:])
    
    # 支撑阻力
    support = np.min(lows[-20:])
    resistance = np.max(highs[-20:])
    
    return {
        'price': current_price,
        'sma20': sma20,
        'sma50': sma50,
        'pct_20': pct_20,
        'trend': trend,
        'signal': signal,
        'std_dev': std_dev,
        'atr': atr,
        'support': support,
        'resistance': resistance
    }

print('【品种分析】')
print('')

for s in symbols:
    data = analyze_symbol(s)
    if data:
        print(f'{s}')
        print(f'  当前价：{data["price"]:.5f}')
        print(f'  20 日涨跌：{data["pct_20"]:+.2f}%')
        print(f'  SMA20: {data["sma20"]:.5f} | SMA50: {data["sma50"]:.5f}')
        print(f'  趋势：{data["trend"]} | 信号：{data["signal"]}')
        print(f'  支撑：{data["support"]:.5f} | 阻力：{data["resistance"]:.5f}')
        print(f'  ATR(波动): {data["atr"]:.5f}')
        print('')
    else:
        print(f'{s}: 数据不足')
        print('')

print('=' * 60)
print('【交易建议】')
print('=' * 60)
print('')

# 生成交易建议
signals = []
for s in symbols:
    data = analyze_symbol(s)
    if data and data['signal'] != 'WAIT':
        signals.append((s, data))

if signals:
    for s, data in signals:
        direction = '做多' if data['signal'] == 'BUY' else '做空'
        print(f'{s}: {direction}')
        print(f'  理由：{data["trend"]}趋势明确，20 日{data["pct_20"]:+.2f}%')
        if data['signal'] == 'BUY':
            entry = data['price']
            stop_loss = data['support'] * 0.9995
            take_profit = data['resistance'] * 1.001
        else:
            entry = data['price']
            stop_loss = data['resistance'] * 1.0005
            take_profit = data['support'] * 0.999
        
        # 计算仓位 (风险 0.5% 账户)
        risk_amount = 10355.54 * 0.005  # 0.5% risk
        stop_distance = abs(entry - stop_loss)
        lot_size = round(risk_amount / stop_distance / 100000, 2) if s != 'USDJPY' else round(risk_amount / stop_distance / 1000, 2)
        lot_size = max(0.01, min(lot_size, 0.1))  # 限制在 0.01-0.1 手
        
        print(f'  入场：{entry:.5f}')
        print(f'  止损：{stop_loss:.5f}')
        print(f'  止盈：{take_profit:.5f}')
        print(f'  建议仓位：{lot_size:.2f}手 (风险 0.5% = ${risk_amount:.2f})')
        print('')
else:
    print('当前市场震荡，建议观望')
    print('')

print('=' * 60)

mt5.shutdown()
