import MetaTrader5 as mt5
import sys

if not mt5.initialize():
    print("MT5 initialization failed")
    sys.exit(1)

account = mt5.account_info()

# 所有可能的 crypto
crypto_symbols = [
    "BTCUSD", "ETHUSD", "LTCUSD", "XRPUSD", "BCHUSD", 
    "ADAUSD", "SOLUSD", "DOTUSD", "LINKUSD", "UNIUSD",
    "AVAXUSD", "MATICUSD", "ATOMUSD", "FILUSD", "SANDUSD"
]

print("=" * 80)
print("FULL CRYPTO MARKET SCAN - Weekend Trading")
print("=" * 80)
print(f"Account: ${account.balance:.2f} | Equity: ${account.equity:.2f}\n")

opportunities = []

for symbol in crypto_symbols:
    tick = mt5.symbol_info_tick(symbol)
    if not tick or tick.bid == 0:
        continue
    
    spread = (tick.ask - tick.bid)
    spread_pct = (spread / tick.bid) * 100
    
    # H4 趋势
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H4, 0, 24)
    if rates is None or len(rates) < 12:
        continue
    
    closes = [r['close'] for r in rates]
    ma_6 = sum(closes[-6:]) / 6
    ma_12 = sum(closes[-12:]) / 12
    ma_24 = sum(closes) / len(closes)
    
    current = tick.bid
    trend_6 = ((current - ma_6) / ma_6) * 100
    trend_12 = ((current - ma_12) / ma_12) * 100
    trend_24 = ((current - ma_24) / ma_24) * 100
    
    # 波动性
    highs = [r['high'] for r in rates[-14:]]
    lows = [r['low'] for r in rates[-14:]]
    atr = sum(h - l for h, l in zip(highs, lows)) / 14
    atr_pct = (atr / current) * 100
    
    # 信号强度
    score = 0
    if trend_6 > 0.5 and trend_12 > 0.5 and trend_24 > 0.5:
        signal = "STRONG BUY"
        score = 90
    elif trend_6 > 0.3 and trend_12 > 0.3:
        signal = "BUY"
        score = 70
    elif trend_6 > 0.1:
        signal = "WEAK BUY"
        score = 50
    elif trend_6 < -0.5 and trend_12 < -0.5 and trend_24 < -0.5:
        signal = "STRONG SELL"
        score = 90
    elif trend_6 < -0.3 and trend_12 < -0.3:
        signal = "SELL"
        score = 70
    elif trend_6 < -0.1:
        signal = "WEAK SELL"
        score = 50
    else:
        signal = "NEUTRAL"
        score = 30
    
    # 点差调整
    if spread_pct > 0.1:
        score -= 20
    elif spread_pct > 0.05:
        score -= 10
    
    # 波动性调整 (适中最好)
    if 1 < atr_pct < 5:
        score += 10
    
    opportunities.append({
        'symbol': symbol,
        'price': current,
        'spread': spread_pct,
        'signal': signal,
        'score': score,
        'trend_6': trend_6,
        'trend_12': trend_12,
        'trend_24': trend_24,
        'atr': atr_pct
    })
    
    marker = "[+]" if "BUY" in signal else "[-]" if "SELL" in signal else "[ ]"
    print(f"{marker} {symbol:10} | ${current:>12.2f} | Spread: {spread_pct:.3f}% | {signal:12} | Score: {score:.0f} | 6H: {trend_6:+.2f}% | 12H: {trend_12:+.2f}% | 24H: {trend_24:+.2f}% | ATR: {atr_pct:.1f}%")

# 排序
opportunities.sort(key=lambda x: x['score'], reverse=True)

print("\n" + "=" * 80)
print("TOP TRADING OPPORTUNITIES")
print("=" * 80)

trades = [opp for opp in opportunities if opp['score'] >= 60]

if trades:
    for i, opp in enumerate(trades[:5], 1):
        print(f"\n#{i}: {opp['symbol']}")
        print(f"  Signal: {opp['signal']}")
        print(f"  Price: ${opp['price']:.2f}")
        print(f"  Score: {opp['score']:.0f}/100")
        print(f"  Spread: {opp['spread']:.3f}%")
        print(f"  Trend: 6H {opp['trend_6']:+.2f}% | 12H {opp['trend_12']:+.2f}% | 24H {opp['trend_24']:+.2f}%")
    
    # 最佳机会
    best = trades[0]
    print("\n" + "=" * 80)
    print("RECOMMENDED TRADE")
    print("=" * 80)
    print(f"\nExecute: {best['symbol']} {best['signal'].split()[-1]}")
    print(f"Entry: ${best['price']:.2f}")
    print(f"Score: {best['score']:.0f}/100")
    
    # 仓位计算
    risk = account.balance * 0.005
    if best['symbol'] == "BTCUSD":
        sl_points = best['price'] * 0.02
        lot = round(risk / sl_points, 3)
    else:
        sl_points = best['price'] * 0.03
        lot = round(risk / sl_points, 3)
    
    print(f"Lot Size: {lot:.3f}")
    print(f"Risk: ${risk:.2f} (0.5%)")
else:
    print("\nNo strong crypto opportunities (all scores < 60)")
    print("Current BTC position is profitable - hold and monitor")

mt5.shutdown()
