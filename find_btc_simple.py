import MetaTrader5 as mt5
mt5.initialize()

print("Finding BTC...\n")

all_symbols = mt5.symbols_get()
btc_found = None

for sym in all_symbols:
    name = sym.name.upper()
    if 'BTC' in name:
        btc_found = sym.name
        break

if btc_found:
    tick = mt5.symbol_info_tick(btc_found)
    print("BTC: %s" % btc_found)
    print("Bid: %.2f Ask: %.2f" % (tick.bid, tick.ask))
    
    # Bayesian analysis
    rates = mt5.copy_rates_from_pos(btc_found, mt5.TIMEFRAME_D1, 0, 60)
    closes = [r['close'] for r in rates]
    avg5 = sum(closes[-5:])/5
    avg20 = sum(closes[-20:])/20
    avg50 = sum(closes[-50:])/50
    
    print("\nTrend:")
    print("  5-day: %.2f 20-day: %.2f 50-day: %.2f" % (avg5, avg20, avg50))
    
    if avg5 > avg20 > avg50:
        trend = "STRONG BULL"
        strength = 3
    elif avg5 > avg20:
        trend = "WEAK BULL"
        strength = 2
    elif avg5 < avg20 < avg50:
        trend = "STRONG BEAR"
        strength = -3
    elif avg5 < avg20:
        trend = "WEAK BEAR"
        strength = -2
    else:
        trend = "SIDEWAYS"
        strength = 0
    
    print("  Trend: %s (strength=%d)" % (trend, strength))
    
    # Bayesian calculation
    prior = 0.55
    if strength > 2:
        likelihood = 0.9
    elif strength > 0:
        likelihood = 0.75
    else:
        likelihood = 0.3
    
    p_trend = likelihood * prior + (1 - likelihood) * (1 - prior)
    posterior = (likelihood * prior) / p_trend
    
    print("\nBayesian:")
    print("  Prior win rate: 55%% (trend following)")
    print("  Likelihood: %.2f" % likelihood)
    print("  Posterior win rate: %.1f%%" % (posterior * 100))
    
    if posterior >= 0.8:
        print("\n✅ CONFIDENCE > 80% - Recommend BUY")
    else:
        print("\n⚠️  Insufficient confidence (<80%%) - Wait")

else:
    print("No BTC found")

print("\nLooking for ETF symbols...\n")
count = 0
for sym in all_symbols:
    name = sym.name.upper()
    if 'ETF' in name:
        tick = mt5.symbol_info_tick(sym.name)
        if tick:
            print("  %s: %.2f" % (sym.name, tick.bid))
            count += 1
            if count >= 10:
                break

if count == 0:
    print("  No ETF found")

mt5.shutdown()
