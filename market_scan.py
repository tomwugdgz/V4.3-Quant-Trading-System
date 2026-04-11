import MetaTrader5 as mt5
import sys

if not mt5.initialize():
    print("MT5 initialization failed")
    sys.exit(1)

account = mt5.account_info()

# 扫描所有主要品种
symbols_to_scan = {
    'Forex': ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD', 'USDCAD', 'USDCHF', 'NZDUSD'],
    'Crypto': ['BTCUSD', 'ETHUSD', 'LTCUSD'],
    'Commodities': ['XAUUSD', 'XAGUSD', 'OIL', 'BRENT']
}

print("=" * 80)
print("MARKET OPPORTUNITY SCAN")
print("=" * 80)
print(f"Account: ${account.balance:.2f} | Equity: ${account.equity:.2f} | Free: ${account.margin_free:.2f}\n")

opportunities = []

for category, symbols in symbols_to_scan.items():
    print(f"\n{'='*80}")
    print(f"{category}")
    print("=" * 80)
    
    for symbol in symbols:
        tick = mt5.symbol_info_tick(symbol)
        if not tick or tick.bid == 0:
            continue
        
        spread = (tick.ask - tick.bid)
        spread_pct = (spread / tick.bid) * 100
        
        # H1 趋势
        rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 24)
        if rates is None or len(rates) < 12:
            continue
        
        closes = [r['close'] for r in rates]
        ma_12 = sum(closes[-12:]) / 12
        ma_24 = sum(closes) / len(closes)
        
        current = tick.bid
        trend_12 = ((current - ma_12) / ma_12) * 100
        trend_24 = ((current - ma_24) / ma_24) * 100
        
        # 信号强度
        if trend_12 > 0.1 and trend_24 > 0.1:
            signal = "STRONG BUY"
            score = 80
        elif trend_12 > 0.05 and trend_24 > 0.05:
            signal = "BUY"
            score = 60
        elif trend_12 > 0:
            signal = "WEAK BUY"
            score = 40
        elif trend_12 < -0.1 and trend_24 < -0.1:
            signal = "STRONG SELL"
            score = 80
        elif trend_12 < -0.05 and trend_24 < -0.05:
            signal = "SELL"
            score = 60
        elif trend_12 < 0:
            signal = "WEAK SELL"
            score = 40
        else:
            signal = "NEUTRAL"
            score = 30
        
        # 点差调整
        if spread_pct > 0.1:
            score -= 20
        elif spread_pct > 0.05:
            score -= 10
        
        opportunities.append({
            'symbol': symbol,
            'category': category,
            'price': current,
            'spread': spread_pct,
            'signal': signal,
            'score': score,
            'trend_12': trend_12,
            'trend_24': trend_24
        })
        
        marker = "[+]" if "BUY" in signal else "[-]" if "SELL" in signal else "[ ]"
        print(f"{marker} {symbol:10} | ${current:>12.2f} | Spread: {spread_pct:.3f}% | {signal:12} | Score: {score:.0f} | 12H: {trend_12:+.2f}% | 24H: {trend_24:+.2f}%")

# 排序
opportunities.sort(key=lambda x: x['score'], reverse=True)

print("\n" + "=" * 80)
print("TOP 5 OPPORTUNITIES")
print("=" * 80)

for i, opp in enumerate(opportunities[:5], 1):
    if opp['score'] >= 60:
        print(f"\n#{i}: {opp['symbol']} ({opp['category']})")
        print(f"  Signal: {opp['signal']}")
        print(f"  Price: ${opp['price']:.2f}")
        print(f"  Score: {opp['score']:.0f}/100")
        print(f"  Spread: {opp['spread']:.3f}%")

# 最佳机会
best = opportunities[0] if opportunities else None

print("\n" + "=" * 80)
print("TRADING RECOMMENDATION")
print("=" * 80)

if best and best['score'] >= 60:
    print(f"\n[OK] Execute: {best['symbol']}")
    print(f"Direction: {best['signal'].split()[-1]}")
    print(f"Entry: ${best['price']:.2f}")
    print(f"Score: {best['score']:.0f}/100")
    
    # 仓位计算
    risk = account.balance * 0.005
    
    if best['category'] == 'Forex':
        sl_pips = 30
        lot = round(risk / (sl_pips * 10), 2)
    elif best['category'] == 'Crypto':
        sl_points = best['price'] * 0.02
        lot = round(risk / sl_points, 3)
    elif best['category'] == 'Commodities':
        if 'XAU' in best['symbol']:
            sl_points = 30
            lot = round(risk / (sl_points * 10), 2)
        else:
            sl_points = 2
            lot = round(risk / (sl_points * 100), 2)
    
    print(f"Recommended Lot: {lot:.3f}")
    print(f"Risk: ${risk:.2f} (0.5%)")
else:
    print("\n[WAIT] No strong opportunity (best score < 60)")
    print("Current market is ranging - hold existing positions")

mt5.shutdown()
