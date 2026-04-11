import MetaTrader5 as mt5
import sys

if not mt5.initialize():
    print("MT5 initialization failed")
    sys.exit(1)

symbol = "XAUUSD"  # 黄金

info = mt5.symbol_info(symbol)
tick = mt5.symbol_info_tick(symbol)

print("=" * 70)
print("XAUUSD (GOLD) ANALYSIS")
print("=" * 70)

print(f"\nPrice:")
print(f"  Bid: ${tick.bid:.2f}")
print(f"  Ask: ${tick.ask:.2f}")
print(f"  Spread: ${tick.ask - tick.bid:.2f} ({((tick.ask - tick.bid) / tick.bid) * 100:.3f}%)")

# H4 趋势
rates_h4 = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H4, 0, 24)
if rates_h4 is not None and len(rates_h4) > 0:
    closes = [r['close'] for r in rates_h4]
    ma_6 = sum(closes[-6:]) / 6
    ma_12 = sum(closes[-12:]) / 12 if len(closes) >= 12 else ma_6
    
    current = tick.bid
    trend_6 = ((current - ma_6) / ma_6) * 100
    trend_12 = ((current - ma_12) / ma_12) * 100
    
    print(f"\nH4 Trend:")
    print(f"  vs 6-period MA: {trend_6:+.2f}%")
    print(f"  vs 12-period MA: {trend_12:+.2f}%")
    
    # 波动性
    highs = [r['high'] for r in rates_h4[-14:]]
    lows = [r['low'] for r in rates_h4[-14:]]
    atr = sum(h - l for h, l in zip(highs, lows)) / 14
    
    print(f"\nATR (14): ${atr:.2f} ({(atr/current)*100:.2f}%)")
    
    if trend_6 < -0.5 and trend_12 < -0.5:
        print("\n  Signal: STRONG SELL (strong downtrend)")
        direction = "SELL"
    elif trend_6 < 0:
        print("\n  Signal: SELL")
        direction = "SELL"
    else:
        print("\n  Signal: NEUTRAL/BUY")
        direction = "NEUTRAL"

# 合约规格
print(f"\nContract Specs:")
print(f"  Min Volume: {info.volume_min}")
print(f"  Max Volume: {info.volume_max}")
print(f"  Volume Step: {info.volume_step}")
print(f"  Contract Size: {info.trade_contract_size}")

# 仓位计算
account = mt5.account_info()
risk = account.balance * 0.005  # 0.5%

if direction in ["SELL", "BUY"]:
    # 黄金：1 lot = 100 oz, $1 move = $100 per lot
    # 使用 2 ATR 止损
    sl_atr = 2 * atr
    lot_size = risk / (sl_atr * 100)  # 100 = contract size
    lot_size = round(lot_size / info.volume_step) * info.volume_step
    lot_size = max(info.volume_min, min(info.volume_max, lot_size))
    
    sl_price = current + sl_atr if direction == "SELL" else current - sl_atr
    tp_price = current - (sl_atr * 2) if direction == "SELL" else current + (sl_atr * 2)
    
    print(f"\nTrade Setup ({direction}):")
    print(f"  Entry: ${current:.2f}")
    print(f"  Stop Loss: ${sl_price:.2f} ({sl_atr:.2f} points)")
    print(f"  Take Profit: ${tp_price:.2f} ({sl_atr*2:.2f} points)")
    print(f"  Lot Size: {lot_size:.3f}")
    print(f"  Risk: ${risk:.2f} (0.5%)")
    
    # 保证金
    margin_required = (current * lot_size * info.trade_contract_size) / account.leverage
    print(f"  Margin Required: ${margin_required:.2f}")
    
    if margin_required < account.margin_free * 0.5:
        print(f"  [OK] Ready to trade!")
    else:
        print(f"  [WARN] High margin usage")
else:
    print("\n  No trade - wait for clearer signal")

mt5.shutdown()
