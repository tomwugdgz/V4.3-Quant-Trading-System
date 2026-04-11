import MetaTrader5 as mt5
from datetime import datetime

mt5.initialize()

print("=== Reopen AUDUSD with trailing stop (no fixed TP) ===\n")
print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
print()

# First close existing position
positions = mt5.positions_get()
ticket_close = None

if positions:
    for pos in positions:
        if pos.symbol == 'AUDUSD' and pos.type == mt5.ORDER_TYPE_BUY:
            ticket_close = pos.ticket
            volume_close = pos.volume
            print(f"Closing existing position: {ticket_close}, volume={volume_close}")

            # Close
            tick = mt5.symbol_info_tick('AUDUSD')
            request = {
                'action': mt5.TRADE_ACTION_DEAL,
                'symbol': 'AUDUSD',
                'volume': volume_close,
                'type': mt5.ORDER_TYPE_SELL,
                'position': ticket_close,
                'price': tick.bid,
                'deviation': 10,
                'magic': 2026031901,
                'comment': 'trailing reopen',
                'type_time': mt5.ORDER_TIME_GTC,
                'type_filling': mt5.ORDER_FILLING_IOC,
            }
            res = mt5.order_send(request)
            print(f"Close result: retcode={res.retcode}")
            if res.retcode != 10009:
                print(f"Error: {res.comment}")
            else:
                print("Closed old position OK")
            break

# Now reopen with new SL, no fixed TP (TP set very high)
print("\nReopening AUDUSD BUY...")

symbol = 'AUDUSD'
volume = 0.09
sl = 0.69900
tp = 0.80000  # very high, effectively trailing stop

tick = mt5.symbol_info_tick(symbol)
price = tick.ask

req = {
    'action': mt5.TRADE_ACTION_DEAL,
    'symbol': symbol,
    'volume': volume,
    'type': mt5.ORDER_TYPE_BUY,
    'price': price,
    'sl': sl,
    'tp': tp,
    'deviation': 10,
    'magic': 2026031902,
    'comment': 'trailing-stop',
    'type_time': mt5.ORDER_TIME_GTC,
    'type_filling': mt5.ORDER_FILLING_IOC,
}

res = mt5.order_send(req)
print(f"Open result: retcode={res.retcode}")
if res.retcode != 10009:
    print(f"Error: {res.comment}")
else:
    print("Opened new position with trailing stop OK")

print()
print("=== Final positions ===")
positions = mt5.positions_get()
if positions:
    for pos in positions:
        direction = "BUY" if pos.type == 0 else "SELL"
        profit_sign = "+" if pos.profit >= 0 else ""
        print(f"{pos.symbol} {direction} {pos.volume:.2f} lot")
        print(f"   Entry: {pos.price_open:.5f} | Current: {pos.price_current:.5f}")
        print(f"   SL: {pos.sl:.5f} | TP: {pos.tp:.5f}")
        print(f"   P/L: {profit_sign}{pos.profit:.2f}")

print()
print("=== Trailing Stop Rule ===")
print("1. Initial SL: 0.69900")
print("2. Price up 20 pips (0.0020) → SL moves up 20 pips")
print("3. No fixed TP, let profit run")
print("4. Close when price breaks current SL")
print()
print("This follows owner request: 'sell when retrace to a point, don't sell when it goes up'")

mt5.shutdown()
