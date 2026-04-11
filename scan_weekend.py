import MetaTrader5 as mt5
import sys

if not mt5.initialize():
    print("MT5 initialization failed")
    sys.exit(1)

# 获取所有可用品种
all_symbols = mt5.symbols_get()

if all_symbols is None:
    print("No symbols available")
    mt5.shutdown()
    sys.exit(1)

print("=" * 70)
print("MT5 Available Symbols - Weekend Trading Opportunities")
print("=" * 70)

# 分类
crypto = []
forex = []
indices = []
commodities = []
stocks = []

for sym in all_symbols:
    name = sym.name
    if 'BTC' in name or 'ETH' in name or 'CRYPTO' in name or 'LTC' in name or 'XRP' in name:
        crypto.append(sym)
    elif 'USD' in name or 'EUR' in name or 'GBP' in name or 'JPY' in name:
        forex.append(sym)
    elif 'DJI' in name or 'SPX' in name or 'IXIC' in name or 'NDX' in name:
        indices.append(sym)
    elif 'GOLD' in name or 'SILVER' in name or 'OIL' in name or 'BRENT' in name:
        commodities.append(sym)
    else:
        stocks.append(sym)

print(f"\nTotal Symbols: {len(all_symbols)}")
print(f"  Crypto: {len(crypto)}")
print(f"  Forex: {len(forex)}")
print(f"  Indices: {len(indices)}")
print(f"  Commodities: {len(commodities)}")
print(f"  Stocks: {len(stocks)}")

# 显示加密货币详情
print("\n" + "=" * 70)
print("CRYPTOCURRENCIES (24/7 Trading)")
print("=" * 70)

for sym in crypto:
    tick = mt5.symbol_info_tick(sym.name)
    if tick and tick.bid > 0:
        spread = (tick.ask - tick.bid)
        print(f"\n{sym.name}:")
        print(f"  Bid: {tick.bid:.2f}")
        print(f"  Ask: {tick.ask:.2f}")
        print(f"  Spread: {spread:.2f}")
        print(f"  Volume: {tick.volume}")
        
        # 获取 H1 数据
        rates = mt5.copy_rates_from_pos(sym.name, mt5.TIMEFRAME_H1, 0, 24)
        if rates is not None and len(rates) > 0:
            closes = [r['close'] for r in rates[-12:]]
            avg_close = sum(closes) / len(closes)
            current = tick.bid
            pct_change = ((current - avg_close) / avg_close) * 100
            
            trend = "UP" if current > avg_close else "DOWN"
            print(f"  Trend (12h): {trend} ({pct_change:+.2f}%)")

# 显示商品详情
print("\n" + "=" * 70)
print("COMMODITIES")
print("=" * 70)

for sym in commodities[:5]:  # 显示前 5 个
    tick = mt5.symbol_info_tick(sym.name)
    if tick and tick.bid > 0:
        spread = (tick.ask - tick.bid)
        print(f"\n{sym.name}:")
        print(f"  Bid: {tick.bid:.2f}")
        print(f"  Ask: {tick.ask:.2f}")
        print(f"  Spread: {spread:.2f}")

mt5.shutdown()
