import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import io
import sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

SYMBOLS = [
    "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "USDCHF", "NZDUSD",
    "EURJPY", "GBPJPY", "AUDJPY", "NZDJPY", "CADJPY", "CHFJPY"
]

def analyze_simple(symbol):
    tick = mt5.symbol_info_tick(symbol)
    if not tick or tick.bid <= 0:
        return None
    
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 100)
    if rates is None or len(rates) < 50:
        return None
    
    df = pd.DataFrame(rates)
    current = tick.bid
    spread = (tick.ask - tick.bid) * 10000
    
    # 5 根 K 线简单趋势
    closes = df['close'].iloc[-5:].values
    avg_close = np.mean(closes)
    strength = abs((current - avg_close) / avg_close * 100)
    signal = "BUY" if current > avg_close else "SELL"
    
    # EMA 确认
    ema_fast = df['close'].ewm(span=10, adjust=False).mean().iloc[-1]
    ema_slow = df['close'].ewm(span=20, adjust=False).mean().iloc[-1]
    ema_signal = "BUY" if ema_fast > ema_slow else "SELL"
    
    # RSI
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=12).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=12).mean()
    rs = gain / loss
    rsi = (100 - (100 / (1 + rs))).iloc[-1]
    
    return {
        'symbol': symbol,
        'price': current,
        'spread': spread,
        'signal': signal,
        'strength': strength,
        'ema': ema_signal,
        'rsi': rsi
    }

if not mt5.initialize():
    print("MT5 initialization failed")
    exit(1)

print("=" * 90)
print("全品种信号扫描 (详细版)")
print("=" * 90)

results = []
for symbol in SYMBOLS:
    result = analyze_simple(symbol)
    if result:
        results.append(result)

# 按信号强度排序
results.sort(key=lambda x: x['strength'], reverse=True)

print(f"\n{'品种':<10} {'价格':<12} {'点差':<8} {'信号':<8} {'强度':<10} {'EMA':<8} {'RSI':<8}")
print("-" * 90)

for r in results:
    print(f"{r['symbol']:<10} {r['price']:<12.5f} {r['spread']:<8.1f} {r['signal']:<8} {r['strength']:<10.3f}% {r['ema']:<8} {r['rsi']:<8.1f}")

print("\n" + "=" * 90)
print("信号强度分级:")
print(f"  超强信号 (≥0.2%): {len([r for r in results if r['strength'] >= 0.2])} 个")
print(f"  强信号 (≥0.1%): {len([r for r in results if r['strength'] >= 0.1])} 个")
print(f"  中等信号 (≥0.05%): {len([r for r in results if r['strength'] >= 0.05])} 个")
print(f"  弱信号 (<0.05%): {len([r for r in results if r['strength'] < 0.05])} 个")

print("\n" + "=" * 90)
if results and results[0]['strength'] >= 0.1:
    best = results[0]
    print(f"推荐交易：{best['symbol']} {best['signal']}")
    print(f"  信号强度：{best['strength']:.3f}% >= 0.1% (达标)")
    print(f"  建议仓位：0.5% 风险")
else:
    print("无达标信号，建议等待")
    if results:
        print(f"  最强信号：{results[0]['symbol']} {results[0]['signal']} ({results[0]['strength']:.3f}%)")
        print(f"  距离达标还差：{0.1 - results[0]['strength']:.3f}%")

print("=" * 90)

mt5.shutdown()
