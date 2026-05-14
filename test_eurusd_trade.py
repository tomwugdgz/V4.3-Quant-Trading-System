#!/usr/bin/env python
import MetaTrader5 as mt5
import sys, time

if not mt5.initialize():
    print("MT5 init failed")
    sys.exit(1)

symbol = "EURUSD"
tick = mt5.symbol_info_tick(symbol)
if not tick:
    print("No tick data")
    mt5.shutdown()
    sys.exit(1)

print(f"EURUSD: Bid={tick.bid:.5f}, Ask={tick.ask:.5f}", flush=True)

volume = 0.01
point = mt5.symbol_info(symbol).point
digits = mt5.symbol_info(symbol).digits

# 30 pip SL, 60 pip TP (1:2 RR)
sl_pips = 30
tp_pips = 60
sl_price = round(tick.ask - sl_pips * point * 10, digits)
tp_price = round(tick.ask + tp_pips * point * 10, digits)

request = {
    "action": mt5.TRADE_ACTION_DEAL,
    "symbol": symbol,
    "volume": volume,
    "type": mt5.ORDER_TYPE_BUY,
    "price": tick.ask,
    "sl": sl_price,
    "tp": tp_price,
    "deviation": 50,
    "magic": 240501,
    "comment": "Wangcai Test",
    "type_time": mt5.ORDER_TIME_GTC,
    "type_filling": mt5.ORDER_FILLING_IOC,
}

print(f"Order: BUY {volume} {symbol} @ {tick.ask:.5f}", flush=True)
print(f"SL={sl_price:.5f} ({sl_pips} pips), TP={tp_price:.5f} ({tp_pips} pips)", flush=True)
print(f"Risk: ~${volume * sl_pips * 1:.2f}", flush=True)

result = mt5.order_send(request)
print(f"Result: retcode={result.retcode}", flush=True)

if result.retcode == mt5.TRADE_RETCODE_DONE:
    print(f"SUCCESS! Order #{result.order}, Deal #{result.deal}", flush=True)
    
    # Wait and verify position
    time.sleep(3)
    positions = mt5.positions_get(symbol=symbol)
    if positions:
        for p in positions:
            print(f"Position #{p.ticket}: {p.volume} {p.symbol} BUY @ {p.price_open:.5f}", flush=True)
            print(f"  SL={p.sl:.5f}, TP={p.tp:.5f}", flush=True)
        
        # Now close the position to complete the test
        print("\nClosing position for test...", flush=True)
        pos = positions[0]
        tick2 = mt5.symbol_info_tick(symbol)
        
        close_request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": pos.volume,
            "type": mt5.ORDER_TYPE_SELL,
            "position": pos.ticket,
            "price": tick2.bid,
            "deviation": 50,
            "magic": 240501,
            "comment": "Test Close",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        close_result = mt5.order_send(close_request)
        print(f"Close result: retcode={close_result.retcode}", flush=True)
        
        if close_result.retcode == mt5.TRADE_RETCODE_DONE:
            print(f"CLOSED! Profit/Loss: ${pos.profit:.2f}", flush=True)
        else:
            print(f"Close failed: {close_result.comment}", flush=True)
    else:
        print("No position found (may have been auto-closed)", flush=True)
else:
    print(f"Trade failed: {result.comment} (code {result.retcode})", flush=True)

mt5.shutdown()
print("Test complete", flush=True)
