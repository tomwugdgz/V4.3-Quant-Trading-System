import MetaTrader5 as mt5
import sys

if not mt5.initialize():
    print("MT5 initialization failed")
    sys.exit(1)

account = mt5.account_info()

# 所有 crypto
crypto_symbols = ["BTCUSD", "ETHUSD", "LTCUSD", "XRPUSD", "BCHUSD", "ADAUSD", "SOLUSD", "DOTUSD", "LINKUSD", "UNIUSD"]

print("=" * 70)
print("CRYPTO SIGNAL SCAN - Finding Strongest Setup")
print("=" * 70)
print(f"Account: ${account.balance:.2f} | Leverage: 1:{account.leverage}\n")

opportunities = []

for symbol in crypto_symbols:
    tick = mt5.symbol_info_tick(symbol)
    if not tick or tick.bid == 0:
        continue
    
    current = tick.bid
    spread = (tick.ask - tick.bid)
    spread_pct = (spread / current) * 100
    
    # H1 趋势
    rates_h1 = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 24)
    if rates_h1 is None or len(rates_h1) < 12:
        continue
    
    closes_h1 = [r['close'] for r in rates_h1]
    ma_12 = sum(closes_h1[-12:]) / 12
    ma_24 = sum(closes_h1) / len(closes_h1)
    
    # H4 趋势
    rates_h4 = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H4, 0, 24)
    if rates_h4 is not None and len(rates_h4) >= 6:
        closes_h4 = [r['close'] for r in rates_h4]
        ma_h4_6 = sum(closes_h4[-6:]) / 6
        ma_h4_12 = sum(closes_h4) / len(closes_h4)
    else:
        ma_h4_6 = ma_12
        ma_h4_12 = ma_24
    
    # 信号强度
    h1_signal = ((current - ma_12) / ma_12) * 100
    h4_signal = ((current - ma_h4_6) / ma_h4_6) * 100
    
    # 综合信号
    combined = (h1_signal + h4_signal) / 2
    
    # 确定方向
    if h1_signal > 0.3 and h4_signal > 0.3:
        direction = "STRONG BUY"
        score = 80 + abs(combined)
    elif h1_signal > 0.15 and h4_signal > 0.15:
        direction = "BUY"
        score = 60 + abs(combined)
    elif h1_signal > 0:
        direction = "WEAK BUY"
        score = 40 + abs(combined)
    elif h1_signal < -0.3 and h4_signal < -0.3:
        direction = "STRONG SELL"
        score = 80 + abs(combined)
    elif h1_signal < -0.15 and h4_signal < -0.15:
        direction = "SELL"
        score = 60 + abs(combined)
    elif h1_signal < 0:
        direction = "WEAK SELL"
        score = 40 + abs(combined)
    else:
        direction = "NEUTRAL"
        score = 30
    
    # 点差惩罚
    if spread_pct > 0.1:
        score -= 20
    elif spread_pct > 0.05:
        score -= 10
    
    opportunities.append({
        'symbol': symbol,
        'price': current,
        'spread': spread_pct,
        'direction': direction,
        'score': score,
        'h1': h1_signal,
        'h4': h4_signal
    })
    
    print(f"{symbol:10} | Price: ${current:>12.2f} | Spread: {spread_pct:.3f}% | {direction:12} | Score: {score:.0f}/100 | H1: {h1_signal:+.2f}% | H4: {h4_signal:+.2f}%")

# 排序
opportunities.sort(key=lambda x: x['score'], reverse=True)

print("\n" + "=" * 70)
print("TOP 3 OPPORTUNITIES")
print("=" * 70)

for i, opp in enumerate(opportunities[:3], 1):
    print(f"\n#{i}: {opp['symbol']}")
    print(f"  Signal: {opp['direction']}")
    print(f"  Price: ${opp['price']:.2f}")
    print(f"  Score: {opp['score']:.0f}/100")
    print(f"  Spread: {opp['spread']:.3f}%")

# 最佳交易建议
best = opportunities[0] if opportunities else None

print("\n" + "=" * 70)
print("TRADING RECOMMENDATION")
print("=" * 70)

if best and best['score'] >= 60:
    print(f"\n[OK] Execute trade on {best['symbol']}")
    print(f"Direction: {best['direction'].split()[-1]}")
    print(f"Entry: ${best['price']:.2f}")
    
    # 仓位计算
    risk = account.balance * 0.005
    if best['symbol'] == "BTCUSD":
        sl_points = 1500
        lot = round(risk / sl_points, 3)
    elif best['symbol'] == "ETHUSD":
        sl_points = 100
        lot = round(risk / sl_points, 2)
    else:
        sl_points = best['price'] * 0.02  # 2% SL
        lot = round(risk / sl_points, 2)
    
    print(f"Lot Size: {lot:.3f}")
    print(f"Risk: ${risk:.2f} (0.5%)")
else:
    print("\n[WAIT] No strong signal found (best score < 60)")
    print("Market is ranging - wait for clearer setup")
    print("\nSuggestion: Monitor BTCUSD for breakout above $71,000 or below $69,000")

mt5.shutdown()
