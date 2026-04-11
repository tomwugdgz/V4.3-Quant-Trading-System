#!/usr/bin/env python
# -*- coding: utf-8 -*-
import MetaTrader5 as mt5

print("MT5 version:", mt5.version())
initialized = mt5.initialize()
print("initialized:", initialized)

if initialized:
    info = mt5.account_info()
    if info:
        print(f"login: {info.login}")
        print(f"balance: {info.balance}")
        print(f"equity: {info.equity}")
        print(f"leverage: {info.leverage}")
        print(f"currency: {info.currency}")
    else:
        print("No account info")
    positions = mt5.positions_get()
    if positions:
        print(f"\nCurrent positions ({len(positions)}):")
        for pos in positions:
            print(f"  {pos.symbol}: {'BUY' if pos.type == 0 else 'SELL'} {pos.volume} lots @ {pos.price_open}, profit: {pos.profit}")
    else:
        print("\nNo open positions")
    mt5.shutdown()
