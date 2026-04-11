import MetaTrader5 as mt5

mt5.initialize()

print("Scanning for BTC and ETF symbols...\n")

all_symbols = mt5.symbols_get()
btc_list = []
etf_list = []

for sym in all_symbols:
    name = sym.name.upper()
    if 'BTC' in name or 'BITCOIN' in name:
        btc_list.append(sym.name)
    if 'ETF' in name or ('XBT' in name and not 'BTC' in name):
        etf_list.append(sym.name)

print("BTC symbols found:")
for s in btc_list:
    tick = mt5.symbol_info_tick(s)
    if tick:
        print("  %s: bid=%.2f ask=%.2f" % (s, tick.bid, tick.ask))
    else:
        print("  %s: (no tick)" % s)

print("\nETF symbols found:")
for s in etf_list:
    tick = mt5.symbol_info_tick(s)
    if tick:
        print("  %s: bid=%.2f ask=%.2f" % (s, tick.bid, tick.ask))
    else:
        print("  %s: (no tick)" % s)

# Calculate Bayesian win rate for current trend
print("\n=== BAYESIAN ANALYSIS ===")

def calculate_bayesian_winrate(symbol, direction_hypothesis):
    """
    Bayesian probability calculation:
    P(win | trend) = P(trend | win) * P(win) / P(trend)
    
    Prior: historical win rate ~ 55% for trend following
    Likelihood: if trend is correct, probability of observation ~ high
    """
    
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_D1, 0, 60)
    if rates is None or len(rates) < 20:
        return None
    
    # Calculate recent trend
    closes = [r['close'] for r in rates]
    avg5 = sum(closes[-5:]) / 5
    avg20 = sum(closes[-20:]) / 20
    avg50 = sum(closes[-50:]) / 50
    
    # Current trend direction
    if avg5 > avg20 > avg50:
        trend_strength = 3  # strong bull
    elif avg5 > avg20:
        trend_strength = 2  # weak bull
    elif avg5 < avg20 < avg50:
        trend_strength = -3  # strong bear
    elif avg5 < avg20:
        trend_strength = -2  # weak bear
    else:
        trend_strength = 0
    
    # Bayesian prior: P(win) = 0.55 (base rate for trend following)
    prior_win = 0.55
    
    # Likelihood depends on trend strength
    if direction_hypothesis == 'BUY':
        if trend_strength > 2:
            likelihood = 0.9  # strong bull -> high likelihood
        elif trend_strength > 0:
            likelihood = 0.75
        else:
            likelihood = 0.3
    else:  # SELL
        if trend_strength < -2:
            likelihood = 0.9
        elif trend_strength < 0:
            likelihood = 0.75
        else:
            likelihood = 0.3
    
    # Marginal probability P(trend) = likelihood * prior + (1-likelihood)*(1-prior)
    p_trend = likelihood * prior_win + (1 - likelihood) * (1 - prior_win)
    
    # Bayes theorem
    posterior = (likelihood * prior_win) / p_trend
    
    # Calculate ATR
    ranges = [r['high'] - r['low'] for r in rates[-14:]]
    atr = sum(ranges) / 14
    
    current_price = closes[-1]
    
    return {
        'symbol': symbol,
        'posterior_winrate': posterior,
        'trend_strength': trend_strength,
        'atr': atr,
        'current_price': current_price,
        'recommended_direction': direction_hypothesis
    }

# Analyze BTC
print("\nBTC Analysis:")
for btc in btc_list[:1]:
    result = calculate_bayesian_winrate(btc, 'BUY')
    if result:
        print("  Symbol: %s" % result['symbol'])
        print("  Current price: %.2f" % result['current_price'])
        print("  Trend strength: %d" % result['trend_strength'])
        print("  Bayesian win rate: %.1f%%" % (result['posterior_winrate'] * 100))
        if result['posterior_winrate'] >= 0.8:
            print("  ✅ HIGH CONFIDENCE (>80%) - Recommend BUY")
        else:
            print("  ⚠️  Insufficient confidence - Wait")

mt5.shutdown()
