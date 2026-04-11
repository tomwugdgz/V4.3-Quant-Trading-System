import MetaTrader5 as mt5
mt5.initialize()

# Find BTC
all_symbols = mt5.symbols_get()
btc_found = None
for sym in all_symbols:
    name = sym.name.upper()
    if 'BTC' in name:
        btc_found = sym.name
        break

# Analyze BTC
tick = mt5.symbol_info_tick(btc_found)
print("BTC: %s" % btc_found)
print("Current: Bid %.2f Ask %.2f" % (tick.bid, tick.ask))

rates = mt5.copy_rates_from_pos(btc_found, mt5.TIMEFRAME_D1, 0, 60)
closes = [r['close'] for r in rates]
avg5 = sum(closes[-5:])/5
avg20 = sum(closes[-20:])/20
avg50 = sum(closes[-50:])/50

print("\nTrend Analysis:")
print("  5-day average:  %.2f" % avg5)
print("  20-day average: %.2f" % avg20)
print("  50-day average: %.2f" % avg50)

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
prior = 0.55  # prior win rate for trend following
if strength > 2:
    likelihood = 0.9
elif strength > 0:
    likelihood = 0.75
else:
    likelihood = 0.3

p_trend = likelihood * prior + (1 - likelihood) * (1 - prior)
posterior = (likelihood * prior) / p_trend

print("\nBayesian Probability Calculation:")
print("  Prior (base rate): 55%%")
print("  Likelihood (trend matches): %.2f" % likelihood)
print("  Posterior win rate: %.1f%%" % (posterior * 100))

if posterior >= 0.8:
    print("\nRESULT: CONFIDENCE > 80% - Recommend BUY")
else:
    print("\nRESULT: Insufficient confidence (<80%%) - Wait for better entry")

# Calculate ATR for risk management
ranges = [r['high'] - r['low'] for r in rates[-14:]]
atr = sum(ranges) / 14
print("\nRisk Management:")
print("  ATR(14): %.2f" % atr)
print("  1.5x ATR stop loss: %.2f" % (tick.ask - atr * 1.5))
print("  2.5x ATR take profit: %.2f" % (tick.ask + atr * 2.5))

# List ETF
print("\nAvailable ETF symbols (top 10):")
count = 0
for sym in all_symbols:
    name = sym.name.upper()
    if 'ETF' in name:
        tick_etf = mt5.symbol_info_tick(sym.name)
        if tick_etf:
            print("  %s: %.2f" % (sym.name, tick_etf.bid))
            count += 1
            if count >= 10:
                break

if count == 0:
    print("  No ETF symbols found in your MT5")

mt5.shutdown()
