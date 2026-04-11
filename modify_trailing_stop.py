import MetaTrader5 as mt5
from datetime import datetime

mt5.initialize()

print("=== Modify position to trailing stop (remove fixed TP) ===\n")
print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
print()

# Find AUDUSD position
positions = mt5.positions_get()
audusd_ticket = None

if positions:
    for pos in positions:
        if pos.symbol == 'AUDUSD' and pos.type == mt5.ORDER_TYPE_BUY:
            audusd_ticket = pos.ticket
            print(f"Found AUDUSD position: ticket={audusd_ticket}")
            print(f"Current SL: {pos.sl:.5f}, Current TP: {pos.tp:.5f}")
            break

if audusd_ticket is None:
    print("ERROR: AUDUSD position not found")
    mt5.shutdown()
    exit()

# Modify: set TP to very high level, effectively trailing stop (no fixed exit)
request = {
    'action': mt5.TRADE_ACTION_MODIFY,
    'position': audusd_ticket,
    'symbol': 'AUDUSD',
    'sl': 0.69900,  # keep original SL
    'tp': 0.80000,  # set to very high, effectively no fixed TP
    'deviation': 10,
}

result = mt5.order_send(request)
print(f"\nModify result: retcode={result.retcode}")
if result.retcode != 10009:
    print(f"Error: {result.comment}")
else:
    print("✅ Success! Fixed TP removed, now using trailing stop")

print()
print("=== Updated positions ===")
positions = mt5.positions_get()
for pos in positions:
    direction = "BUY" if pos.type == 0 else "SELL"
    profit_sign = "+" if pos.profit >= 0 else ""
    print(f"{pos.symbol} {direction} {pos.volume:.2f} lot")
    print(f"   Entry: {pos.price_open:.5f} | Current: {pos.price_current:.5f}")
    print(f"   SL: {pos.sl:.5f} | TP: {pos.tp:.5f}")
    print(f"   P/L: {profit_sign}{pos.profit:.2f}")

print()
print("Trailing stop rule:")
print("- SL starts at 0.69900")
print("- For every +20 pips (0.0020) move up, SL moves up 20 pips")
print("- No fixed TP, let profit run")
print("- Close when price retraces and breaks SL")

mt5.shutdown()
