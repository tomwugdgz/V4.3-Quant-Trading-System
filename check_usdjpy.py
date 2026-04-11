import MetaTrader5 as mt5
import sys

if not mt5.initialize():
    print("MT5 initialization failed")
    sys.exit(1)

symbol = "USDJPY"

# 获取详细信息
info = mt5.symbol_info(symbol)
tick = mt5.symbol_info_tick(symbol)

print("=" * 70)
print("USDJPY DETAILED CHECK")
print("=" * 70)

print(f"\nPrice:")
print(f"  Bid: {tick.bid:.3f}")
print(f"  Ask: {tick.ask:.3f}")
print(f"  Spread: {(tick.ask - tick.bid) * 10000:.1f} pips")

# H4 趋势
rates_h4 = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H4, 0, 24)
if rates_h4:
    closes = [r['close'] for r in rates_h4]
    ma_6 = sum(closes[-6:]) / 6
    ma_12 = sum(closes[-12:]) / 12 if len(closes) >= 12 else ma_6
    
    current = tick.bid
    trend_6 = ((current - ma_6) / ma_6) * 100
    trend_12 = ((current - ma_12) / ma_12) * 100
    
    print(f"\nH4 Trend:")
    print(f"  vs 6-period MA: {trend_6:+.2f}%")
    print(f"  vs 12-period MA: {trend_12:+.2f}%")
    
    if trend_6 > 0.1 and trend_12 > 0.1:
        print("\n  Signal: STRONG BUY")
    elif trend_6 > 0:
        print("\n  Signal: BUY")
    else:
        print("\n  Signal: NEUTRAL/SELL")

# 合约规格
print(f"\nContract Specs:")
print(f"  Min Volume: {info.volume_min}")
print(f"  Max Volume: {info.volume_max}")
print(f"  Volume Step: {info.volume_step}")
print(f"  Contract Size: {info.trade_contract_size}")

# 仓位计算
account = mt5.account_info()
risk = account.balance * 0.005  # 0.5%
sl_pips = 30

# USDJPY: 1 pip = 0.01
# P&L = (close - open) * volume * contract_size / 100 (for JPY pairs)
# 简化：lot_size = risk / (sl_pips * pip_value)
# pip_value for USDJPY ≈ $9.30 per 1.0 lot per pip (depends on exchange rate)

pip_value_per_lot = 9.30  # approximate for USDJPY
lot_size = risk / (sl_pips * pip_value_per_lot)
lot_size = round(lot_size / info.volume_step) * info.volume_step
lot_size = max(info.volume_min, min(info.volume_max, lot_size))

print(f"\nPosition Sizing:")
print(f"  Risk: ${risk:.2f} (0.5%)")
print(f"  Stop Loss: {sl_pips} pips")
print(f"  Pip Value: ${pip_value_per_lot:.2f} per lot")
print(f"  Recommended Lot: {lot_size:.2f}")

# 保证金检查
margin_required = (tick.ask * lot_size * info.trade_contract_size) / account.leverage
print(f"  Margin Required: ${margin_required:.2f}")
print(f"  Free Margin: ${account.margin_free:.2f}")

if margin_required < account.margin_free * 0.5:
    print("\n  [OK] Margin sufficient")
else:
    print("\n  [WARN] High margin usage")

mt5.shutdown()
