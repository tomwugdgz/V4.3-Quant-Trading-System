import MetaTrader5 as mt5
import sys

if not mt5.initialize():
    print("MT5 initialization failed")
    sys.exit(1)

symbol = "BTCUSD"

# 获取合约规格
info = mt5.symbol_info(symbol)

if info is None:
    print("Symbol not found")
    mt5.shutdown()
    sys.exit(1)

print("=" * 70)
print(f"BTCUSD Contract Specifications")
print("=" * 70)

print(f"\nBasic Info:")
print(f"  Name: {info.name}")
print(f"  Description: {info.description}")
print(f"  Currency: {info.currency_margin}")
print(f"  Currency Profit: {info.currency_profit}")

print(f"\nVolume Limits:")
print(f"  Min Volume: {info.volume_min}")
print(f"  Max Volume: {info.volume_max}")
print(f"  Volume Step: {info.volume_step}")

print(f"\nContract Size:")
print(f"  Contract Size: {info.trade_contract_size}")

print(f"\nMargin:")
print(f"  Initial Margin: {info.margin_initial}")
print(f"  Maintenance Margin: {info.margin_maintenance}")

print(f"\nPrice Info:")
tick = mt5.symbol_info_tick(symbol)
if tick:
    print(f"  Bid: ${tick.bid:.2f}")
    print(f"  Ask: ${tick.ask:.2f}")
    print(f"  Spread: ${tick.ask - tick.bid:.2f}")

# 计算正确的手数
account = mt5.account_info()
risk_amount = account.balance * 0.005  # 0.5% = $51.76
stop_loss = 1500  # $1500

# 对于 BTCUSD，1 lot = 1 BTC
# P&L = (close_price - open_price) * volume * contract_size
# 所以：volume = risk / (stop_loss * contract_size)

contract_size = info.trade_contract_size
volume = risk_amount / (stop_loss * contract_size)

print(f"\n" + "=" * 70)
print(f"POSITION SIZING CALCULATION")
print("=" * 70)
print(f"Risk Amount: ${risk_amount:.2f}")
print(f"Stop Loss: ${stop_loss:.2f}")
print(f"Contract Size: {contract_size}")
print(f"Calculated Volume: {volume:.4f}")

# 调整到符合平台要求
volume_step = info.volume_min
corrected_volume = round(volume / volume_step) * volume_step
corrected_volume = max(info.volume_min, min(info.volume_max, corrected_volume))

print(f"Volume Step: {volume_step}")
print(f"Corrected Volume: {corrected_volume:.4f}")

# 保证金检查
margin_per_lot = info.margin_initial
total_margin = margin_per_lot * corrected_volume

print(f"\nMargin per Lot: ${margin_per_lot:.2f}")
print(f"Total Margin Required: ${total_margin:.2f}")
print(f"Available Margin: ${account.margin_free:.2f}")

if total_margin < account.margin_free * 0.5:
    print("\n[OK] Margin sufficient")
    print(f"\nREADY TO TRADE: {corrected_volume:.4f} lots")
else:
    print("\n[WARN] High margin usage")
    # 减少仓位
    max_lots = (account.margin_free * 0.3) / margin_per_lot
    max_lots = round(max_lots / volume_step) * volume_step
    print(f"Reduced Volume: {max_lots:.4f} lots")

mt5.shutdown()
