import MetaTrader5 as mt5
from datetime import datetime

mt5.initialize()

print("=== Opening two positions per LTCM-INTJ strategy ===\n")
print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
print()

# Account: 52797683, Balance: $10,000, Risk per trade 0.5% = $50
risk_per_trade = 50.0

# ========== 1. USDJPY BUY ==========
symbol = 'USDJPY'
direction = 'BUY'
entry_price = 159.293
sl_price = 158.80
tp_price = 160.20

tick = mt5.symbol_info_tick(symbol)
info = mt5.symbol_info(symbol)

price = tick.ask
sl = sl_price
tp = tp_price

# Calculate lot size based on risk
# For USDJPY, 1 pip = 0.01 JPY = $0.10 per 0.01 lot
pip_distance = price - sl
pips_risked = pip_distance * 100  # 100 pips per 1.00 price
# 0.01 lot = $0.10 per pip
lot_size = (risk_per_trade / (pips_risked * 0.10)) * 0.01
lot_size = round(lot_size / info.volume_step) * info.volume_step
lot_size = max(0.01, lot_size)

print(f"1. {symbol} {direction}")
print(f"   Current price: {price:.3f}")
print(f"   SL: {sl:.3f}, TP: {tp:.3f}")
print(f"   Risk: ${risk_per_trade:.2f}, Lot: {lot_size:.2f}")

req = {
    'action': mt5.TRADE_ACTION_DEAL,
    'symbol': symbol,
    'volume': lot_size,
    'type': mt5.ORDER_TYPE_BUY,
    'price': price,
    'sl': round(sl, 3),
    'tp': round(tp, 3),
    'deviation': 10,
    'magic': 2026031901,
    'comment': 'ltcm-intj',
    'type_time': mt5.ORDER_TIME_GTC,
    'type_filling': mt5.ORDER_FILLING_IOC,
}
res = mt5.order_send(req)
print(f"   Result: retcode={res.retcode}")
if res.retcode != 10009:
    print(f"   Error: {res.comment}")
print()

# ========== 2. AUDUSD BUY ==========
symbol = 'AUDUSD'
direction = 'BUY'
sl_price = 0.6990
tp_price = 0.7080

tick = mt5.symbol_info_tick(symbol)
info = mt5.symbol_info(symbol)

price = tick.ask
sl = sl_price
tp = tp_price

# Calculate lot size for AUDUSD
# 1 pip = 0.0001 = $0.10 per 0.01 lot
pip_distance = (price - sl) * 10000  # pips
lot_size = (risk_per_trade / (pip_distance * 0.10)) * 0.01
lot_size = round(lot_size / info.volume_step) * info.volume_step
lot_size = max(0.01, lot_size)

print(f"2. {symbol} {direction}")
print(f"   Current price: {price:.5f}")
print(f"   SL: {sl:.5f}, TP: {tp:.5f}")
print(f"   Risk: ${risk_per_trade:.2f}, Lot: {lot_size:.2f}")

req = {
    'action': mt5.TRADE_ACTION_DEAL,
    'symbol': symbol,
    'volume': lot_size,
    'type': mt5.ORDER_TYPE_BUY,
    'price': price,
    'sl': round(sl, 5),
    'tp': round(tp, 5),
    'deviation': 10,
    'magic': 2026031901,
    'comment': 'ltcm-intj',
    'type_time': mt5.ORDER_TIME_GTC,
    'type_filling': mt5.ORDER_FILLING_IOC,
}
res = mt5.order_send(req)
print(f"   Result: retcode={res.retcode}")
if res.retcode != 10009:
    print(f"   Error: {res.comment}")
print()

# ========== Summary ==========
print("=== CURRENT POSITIONS ===\n")
positions = mt5.positions_get()
if positions:
    total_profit = 0.0
    total_volume = 0.0
    for i, pos in enumerate(positions, 1):
        direction = "BUY" if pos.type == 0 else "SELL"
        profit_sign = "+" if pos.profit >= 0 else ""
        print(f"{i}. {pos.symbol} {direction} {pos.volume:.2f} lot")
        print(f"   Entry: {pos.price_open:.5f} | Current: {pos.price_current:.5f}")
        print(f"   P/L: {profit_sign}{pos.profit:.2f} USD")
        total_profit += pos.profit
        total_volume += pos.volume
    print()
    print("=== SUMMARY ===")
    print(f"Total lots: {total_volume:.2f}")
    print(f"Total floating P/L: {profit_sign}{total_profit:.2f} USD")
else:
    print("No open positions")

print()
mt5.shutdown()
